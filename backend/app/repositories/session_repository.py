import json
from typing import Any, Dict, List, Optional, Tuple, Union

from infrastructure.logging.logger import logger
from infrastructure.database.database_pool import DatabasePool
from infrastructure.redis_client import redis_client

SESSION_TTL = 86400        # 24小时
SESSION_CACHE_SIZE = 7     # 缓存条数：system(1) + 最近3轮(6)


class SessionRepository:
    """会话数据仓储类。

    Redis  → 历史缓存（最近 SESSION_CACHE_SIZE 条）+ 追问状态，TTL 自动过期
    MySQL  → 完整对话历史，持久化（唯一索引保证增量写入幂等）
    """

    def _redis_key(self, user_id: str, session_id: str) -> str:
        return f"session:{user_id}:{session_id}"

    def _cache_key(self, user_id: str, session_id: str) -> str:
        return f"session_cache:{user_id}:{session_id}"

    def _get_conn(self):
        return DatabasePool.get_connection()

    def _write_cache(self, ckey: str, messages: List[Dict[str, Any]]) -> None:
        """将最近 SESSION_CACHE_SIZE 条消息写入 Redis 缓存。"""
        try:
            tail = messages[-SESSION_CACHE_SIZE:]
            redis_client.set(ckey, json.dumps(tail, ensure_ascii=False), ex=SESSION_TTL)
        except Exception as e:
            logger.warning(f"写入 Redis 缓存失败（不影响主流程）: {e}")

    # ------------------------------------------------------------------ #
    #  load_session  —  先查 Redis 缓存，miss 再查 MySQL                   #
    # ------------------------------------------------------------------ #

    def load_session(self, user_id: str, session_id: str) -> Optional[List[Dict[str, Any]]]:
        # 1. 先查 Redis 缓存
        ckey = self._cache_key(user_id, session_id)
        try:
            cached = redis_client.get(ckey)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"读取 Redis 缓存失败，降级查 MySQL: {e}")

        # 2. Cache miss，查 MySQL
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT seq_id, role, content, is_ask_user, pending_intent "
                    "FROM chat_messages "
                    "WHERE user_id=%s AND session_id=%s ORDER BY seq_id ASC",
                    (user_id, session_id),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        messages = []
        for seq_id, role, content, is_ask_user, pending_intent in rows:
            msg: Dict[str, Any] = {"role": role, "content": content, "seq_id": seq_id}
            if is_ask_user:
                msg["is_ask_user"] = True
            if pending_intent:
                msg["pending_intent"] = pending_intent
            messages.append(msg)

        # 3. 回写缓存
        self._write_cache(ckey, messages)
        return messages

    # ------------------------------------------------------------------ #
    #  save_session  —  增量写入 MySQL（INSERT IGNORE），更新 Redis 缓存    #
    # ------------------------------------------------------------------ #

    def save_session(self, user_id: str, session_id: str, data: List[Dict[str, Any]]) -> None:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                for msg in data:
                    cur.execute(
                        "INSERT IGNORE INTO chat_messages "
                        "(user_id, session_id, seq_id, role, content, is_ask_user, pending_intent) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (
                            user_id,
                            session_id,
                            msg.get("seq_id", 0),
                            msg.get("role", ""),
                            msg.get("content", ""),
                            1 if msg.get("is_ask_user") else 0,
                            msg.get("pending_intent", ""),
                        ),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        # 更新 Redis 历史缓存
        self._write_cache(self._cache_key(user_id, session_id), data)

        # 同步追问状态
        last_assistant = next(
            (m for m in reversed(data) if m.get("role") == "assistant"), None
        )
        rkey = self._redis_key(user_id, session_id)
        if last_assistant and last_assistant.get("is_ask_user"):
            redis_client.hset(rkey, mapping={
                "is_ask_user": "1",
                "pending_intent": last_assistant.get("pending_intent", ""),
            })
            redis_client.expire(rkey, SESSION_TTL)
        else:
            redis_client.delete(rkey)

    # ------------------------------------------------------------------ #
    #  get_max_seq_id  —  直接查 MySQL 聚合，避免全量加载                    #
    # ------------------------------------------------------------------ #

    def get_max_seq_id(self, user_id: str, session_id: str) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(seq_id), -1) FROM chat_messages "
                    "WHERE user_id=%s AND session_id=%s",
                    (user_id, session_id),
                )
                return cur.fetchone()[0]
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  get_all_sessions_metadata  —  查询用户所有 session 列表              #
    # ------------------------------------------------------------------ #

    def get_all_sessions_metadata(self, user_id: str) -> List[Tuple[str, str, Union[List, Exception]]]:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT session_id, MIN(created_at) "
                    "FROM chat_messages WHERE user_id=%s GROUP BY session_id",
                    (user_id,),
                )
                sessions = cur.fetchall()
        finally:
            conn.close()

        results = []
        for session_id, create_time in sessions:
            try:
                data = self.load_session(user_id, session_id) or []
                results.append((session_id, str(create_time), data))
            except Exception as e:
                logger.error(f"读取会话 {session_id} 失败: {e}")
                results.append((session_id, str(create_time), e))

        return results


# 全局单例
session_repository = SessionRepository()
