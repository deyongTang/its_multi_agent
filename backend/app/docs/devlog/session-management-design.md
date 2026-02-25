# 开发日志 - 会话管理架构设计

**日期**: 2026-02-23
**类型**: 架构设计
**重要性**: 核心亮点

---

## 背景：为什么不用 LangGraph Checkpointer

LangGraph 官方提供了 Checkpointer 机制用于状态持久化，但它的设计目标是 **Human-in-the-loop** 场景：

```
工作流执行到中途 → 暂停 → 等用户审批/介入 → 从断点继续
```

典型案例：Cursor、Devin 等 coding agent，生成代码后暂停等用户 approve。

**我们的对话系统完全不同：**

```
用户发消息 → 启动全新工作流 → 跑完 → 结束
用户再发消息 → 又是全新工作流（不是从断点恢复）
```

每个工作流都是完整独立的。Checkpointer 存的是"未完成的工作流实例"，对我们没有意义。

对话系统真正需要的是：**把上一轮结果存起来，下一轮作为上下文传入新工作流**。

---

## 架构设计：双层存储

```
Redis  ──→  活跃 session 状态（追问标记，TTL 自动过期）
MySQL  ──→  完整对话历史（持久化，可查询，可展示）
```

### Redis 层：追问状态缓存

```
key:   session:{user_id}:{session_id}
value: hash { is_ask_user: "1", pending_intent: "search_info" }
TTL:   86400 秒（24小时不活跃自动清理）
```

**职责**：存储当前 session 是否处于追问等待状态，以及待恢复的意图。

**生命周期**：
- 工作流以 `ask_user` 结束 → 写入 Redis hash，设 TTL
- 工作流正常结束（generate_report / escalate）→ 删除 Redis key
- 24小时无活动 → TTL 自动过期，无需手动清理

### MySQL 层：对话历史持久化

```sql
CREATE TABLE chat_messages (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        VARCHAR(64) NOT NULL,
    session_id     VARCHAR(64) NOT NULL,
    seq_id         INT NOT NULL DEFAULT 0,
    role           VARCHAR(16) NOT NULL,       -- user / assistant / system
    content        TEXT NOT NULL,
    is_ask_user    TINYINT DEFAULT 0,
    pending_intent VARCHAR(64) DEFAULT '',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (user_id, session_id, seq_id)
);
```

**职责**：永久存储完整对话历史，供前端展示历史会话、供 runner.py 恢复上下文。

---

## 数据流：一次完整的追问交互

```
Turn 1: "明天天气怎么样"
  ↓
runner.py 构建 initial_state（current_intent=None）
  ↓
LangGraph 工作流：intent → slot_filling → ask_user → END
  ↓
workflow_stream_service: SSE 携带 is_ask_user=True, pending_intent="search_info"
  ↓
agent_service_v2: 保存到 MySQL
  { role: "assistant", content: "请问城市？", is_ask_user: 1, pending_intent: "search_info" }
  ↓
session_repository.save_session:
  → MySQL: 写入完整历史
  → Redis: SET session:u1:s1 { is_ask_user:"1", pending_intent:"search_info" } EX 86400

Turn 2: "深圳市"
  ↓
session_service.prepare_history: 从 MySQL 读取历史
  chat_history[-1] = { is_ask_user: True, pending_intent: "search_info" }
  ↓
runner.py 检测追问状态，重建 initial_state:
  current_intent = "search_info"   ← 从 pending_intent 恢复
  original_query = "明天天气怎么样" ← 从历史反查
  ask_user_count = 1
  ↓
LangGraph 工作流：intent（跳过LLM）→ slot_filling → retrieval → verify → generate_report
  ↓
session_repository.save_session:
  → MySQL: 写入完整历史
  → Redis: DELETE session:u1:s1（正常结束，清除追问状态）
```

---

## 与 LangGraph Checkpointer 的对比

| 维度 | LangGraph Checkpointer | 我们的方案 |
|------|----------------------|-----------|
| 设计目标 | 工作流断点恢复 | 对话历史管理 |
| 存储格式 | LangGraph 内部格式 | 标准 role/content 格式 |
| 业务层可读 | 否 | 是（前端直接展示） |
| 追问状态 | 存整个 AgentState | 只存关键字段（轻量） |
| 过期清理 | 需手动管理 | Redis TTL 自动过期 |
| 适用场景 | Human-in-the-loop agent | 对话系统 |

---

## 核心设计原则

**1. 职责分离**
- Redis 管"现在"：当前 session 是否在追问，短暂，自动过期
- MySQL 管"历史"：完整对话记录，永久，可查询

**2. 最小存储**
- Redis 只存追问状态两个字段，不存整个 AgentState
- `get_max_seq_id` 用 `SELECT MAX(seq_id)` 而非全量加载

**3. 幂等写入**
- `save_session` 先 DELETE 再 INSERT，重复调用结果一致

**4. 框架无关**
- 会话管理完全在业务层，不依赖 LangGraph 内部机制
- 未来换掉 LangGraph，会话层代码不需要改动

---

## 涉及文件

| 文件 | 职责 |
|------|------|
| [session_repository.py](../../repositories/session_repository.py) | 底层存储：Redis + MySQL 读写 |
| [session_service.py](../../services/session_service.py) | 业务逻辑：历史裁剪、seq_id 分配 |
| [agent_service_v2.py](../../services/agent_service_v2.py) | 解析 SSE，保存 is_ask_user / pending_intent |
| [runner.py](../workflow/runner.py) | 从历史恢复 current_intent / original_query |
| [workflow_stream_service.py](../../services/workflow_stream_service.py) | 从 LangGraph 事件提取 pending_intent |
