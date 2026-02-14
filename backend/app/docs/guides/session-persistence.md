# ITS 会话持久化：架构设计与部署指南

> 本文合并自 `SESSION_PERSISTENCE_DESIGN.md` 和 `SESSION_PERSISTENCE_GUIDE.md`

---

## 1. 核心挑战与目标

在工业级 Agent 系统中，我们面临 "数据双态性" 的挑战：
1. **运行时状态 (Runtime State)**：机器需要的结构化数据（如槽位 `{"device": "mac"}`、当前节点 `node_ask_user`）。要求低延迟、高频读写。
2. **历史记录 (Chat History)**：人类需要的文本记录。要求持久保存、结构稳定。

**设计目标**：建立一套**可插拔、最终一致**的数据架构，确保 Agent 既能"接得上话"（State），用户也能"查得到记录"（History），并在分布式环境下保证**顺序一致性**。

---

## 2. 双层存储架构

| 层面 | 术语 | 存储介质 | 职责 | 服务对象 |
| :--- | :--- | :--- | :--- | :--- |
| **热存储** | Session State | Redis (Checkpointer) | 维护推理状态 (Slots, Thread) | 机器 (LangGraph) |
| **冷存储** | Chat History | 文件系统 (JSON) | 维护对话日志 + seq_id | 人类 (Frontend) |

### 核心特性

- **Thread ID 绑定** — `thread_id = f"thread_{user_id}_{session_id}"`
- **Redis Checkpointer** — LangGraph 状态自动持久化到 Redis
- **分布式锁** — 防止并发写入导致数据乱序
- **逻辑序号 (seq_id)** — 确保消息顺序一致性
- **优雅降级** — Redis 不可用时自动降级到 MemorySaver

---

## 3. LangGraph 深度整合

### 3.1 ID 绑定策略 (Thread Binding)

LangGraph 的 `thread_id` 是连接业务与引擎的唯一纽带。**严禁使用随机 UUID。**

* **业务 ID**: `session_id` (前端生成)
* **引擎 ID**: `thread_id`
* **绑定公式**: `thread_id = f"thread_{user_id}_{session_id}"`
* **代码位置**: `multi_agent/workflow/runner.py`

### 3.2 状态生命周期

1. **加载 (Load)**: 请求到达时，LangGraph 根据 `thread_id` 自动从 Redis 加载 Checkpoint。所有 `slots` 和 `memory` 瞬间恢复。
2. **执行 (Execute)**: 每经过一个 Node，LangGraph 自动执行 `checkpoint.put()`。
3. **中断 (Interrupt)**: 如果进入 `node_ask_user`，流程挂起，状态持久化到 Redis，等待下一次请求唤醒。

---

## 4. 数据同步机制

采用 **"State 自动，History 手动"** 的双轨制。

### 4.1 State (Hot): 自动同步
* **机制**: 依赖 LangGraph 内置的 `Checkpointer`
* **频率**: 高频（Node 级）
* **一致性**: 强一致（写完 Redis 才算 Step 完成）

### 4.2 History (Cold): 触发式同步
* **机制**: 在 `AgentService` 业务层手动调用
* **时机**: 流式响应结束 (End of Stream)
* **代码位置**: `services/agent_service_v2.py`

```python
# 流式响应结束后保存历史
if full_ai_response:
    format_result = re.sub(r'\n+', '\n', full_ai_response)
    chat_history.append({"role": "assistant", "content": format_result})
    session_service.save_history(user_id, session_id, chat_history)
```

---

## 5. 分布式并发控制

### 5.1 写入保护：Redis 分布式锁

代码位置: `infrastructure/redis_lock.py`

```python
with redis_lock(f"lock:session:{user_id}:{session_id}:write", timeout=5):
    # 临界区：Read-Modify-Write
    max_seq_id = repo.get_max_seq_id(user_id, session_id)
    for msg in chat_history:
        if "seq_id" not in msg:
            msg["seq_id"] = max_seq_id + 1
            max_seq_id += 1
    repo.save_session(user_id, session_id, chat_history)
```

保护机制：
- 使用 Redis `SET NX EX` 原子操作获取锁
- 锁超时时间 5 秒（防止死锁）
- 使用 Lua 脚本释放锁（防止误删）

### 5.2 数据自证：逻辑序号 (Sequence ID)

即便在锁失效的极端边缘情况（如 Redis 主从切换），`seq_id` 也能作为最后的防线。
* **生成规则**: 基于当前数据库中已有的最大值 + 1
* **查询规则**: 返回前端前执行 `history.sort(key=lambda x: x.seq_id)`

---

## 6. 部署步骤

### 6.1 安装依赖

```bash
cd backend/app
pip install -r requirements.txt
```

新增依赖：`redis>=5.0.0`、`langgraph-checkpoint-redis>=0.1.0`

### 6.2 启动 Redis 服务

```bash
# Docker 启动
docker run -d --name redis-its -p 6379:6379 redis:7-alpine

# 或 macOS 本地安装
brew install redis && brew services start redis

# 验证
redis-cli ping  # 输出: PONG
```

### 6.3 配置环境变量

编辑 `backend/app/.env`：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_DECODE_RESPONSES=true
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### 6.4 运行测试

```bash
cd backend/app
python test_session_persistence.py
```

预期输出：4/4 项测试通过（Redis 连接、分布式锁、seq_id 机制、并发写入）。

---

## 7. 故障恢复

### Q1: Redis 不可用怎么办？
- LangGraph 自动降级到 `MemorySaver`（内存模式）
- 分布式锁失效，使用无锁模式
- 仅适用于单实例部署

### Q2: 服务重启后会话丢失吗？
- **State**: 使用 RedisSaver 时从 Redis 恢复
- **History**: 持久化到文件系统，永久保存

### Q3: LangGraph 跑了一半服务挂了？
- State 停留在上一个成功的 Checkpoint
- 用户再次发送消息，LangGraph 从 Checkpoint 恢复，继续执行未完成的步骤
- 数据最终一致

### Q4: 流式推完了但存储写入失败？
- 属于严重系统错误，State 已更新但 History 丢失最后一句
- 生产环境可引入 MQ 异步写入作为兜底

---

## 8. 监控与调试

```bash
# 查看 Redis 中的 Checkpoint
redis-cli KEYS "thread_*"

# 查看会话文件
ls -la backend/app/user_memories/{user_id}/

# 日志关键字
grep "Checkpointer" logs/app.log
grep "获取锁\|释放锁" logs/app.log
grep "seq_id" logs/app.log
```

---

## 9. 性能优化建议

- **Redis 连接池**: `max_connections=10`，`health_check_interval=30`（见 `infrastructure/redis_client.py`）
- **锁超时调整**: 业务逻辑复杂时可增加到 10 秒
- **History 存储升级**: 当前为文件系统 (JSON)，未来升级为 MySQL + 异步写入 (Phase 3)

---

## 10. 架构演进路线

1. **Phase 1 (Current)**: State → `MemorySaver`，History → 文件系统 (无锁)
2. **Phase 2 (Prod Ready)**: State → `RedisSaver`，History → 文件系统 + Redis Lock
3. **Phase 3 (High Scale)**: History → 异步写入 (Kafka/RabbitMQ) → MySQL

---

**版本**: v1.2 | **日期**: 2026-01-28
