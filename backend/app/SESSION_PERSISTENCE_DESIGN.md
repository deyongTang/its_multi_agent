# ITS 会话持久化与数据同步架构设计 (Session Persistence Architecture)

| 文档版本 | 日期 | 作者 | 状态 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-01-28 | 架构师 | 已归档 |
| v1.1 | 2026-01-28 | 架构师 | 已归档 |
| v1.2 | 2026-01-28 | 架构师 | **现行有效** (整合 LangGraph 深度绑定) |

---

## 1. 核心挑战与目标

在工业级 Agent 系统中，我们面临 "数据双态性" 的挑战：
1.  **运行时状态 (Runtime State)**: 机器需要的结构化数据（如槽位 `{"device": "mac"}`、当前节点 `node_ask_user`）。要求低延迟、高频读写。
2.  **历史记录 (Chat History)**: 人类需要的文本记录。要求持久保存、结构稳定。

**设计目标**：建立一套**可插拔、最终一致**的数据架构，确保 Agent 既能"接得上话"（State），用户也能"查得到记录"（History），并在分布式环境下保证**顺序一致性**。

---

## 2. 双层存储架构 (Dual-Store Architecture)

| 层面 | 术语 | 存储介质 | 职责 |
| :--- | :--- | :--- | :--- |
| **热存储** | **Session State** | Redis (Checkpointer) | 维护推理状态 (Slots, Thread)。服务于 **机器** (LangGraph)。 |
| **冷存储** | **Chat History** | MySQL | 维护对话日志，**引入 Seq ID**。服务于 **人类** (Frontend)。 |

---

## 3. LangGraph 深度整合方案 (Deep Integration)

### 3.1 ID 绑定策略 (Thread Binding)
LangGraph 的 `thread_id` 是连接业务与引擎的唯一纽带。**严禁使用随机 UUID。**

*   **业务 ID**: `session_id` (前端生成，如 `sess_user123_t999`)
*   **引擎 ID**: `thread_id`
*   **绑定公式**: `thread_id = f"thread_{user_id}_{session_id}"`

**代码实现位置**: `multi_agent/workflow/runner.py`

### 3.2 状态生命周期 (State Lifecycle)
1.  **加载 (Load)**: 请求到达时，LangGraph 根据 `thread_id` 自动从 Redis 加载 Checkpoint。
    *   *此时，所有的 `slots` 和 `memory` 瞬间恢复，仿佛服务从未重启。*
2.  **执行 (Execute)**: 每经过一个 Node，LangGraph 自动执行 `checkpoint.put()`。
3.  **中断 (Interrupt)**: 如果进入 `node_ask_user`，流程挂起，状态持久化到 Redis，等待下一次请求唤醒。

---

## 4. 数据同步机制 (Sync Mechanism)

我们采用 **"State 自动，History 手动"** 的双轨制。

### 4.1 State (Hot): 自动同步
*   **机制**: 依赖 LangGraph 内置的 `Checkpointer`。
*   **频率**: 高频（Node 级）。
*   **一致性**: 强一致（写完 Redis 才算 Step 完成）。

### 4.2 History (Cold): 触发式同步
*   **机制**: 在 `AgentService` 业务层手动调用。
*   **时机**: **流式响应结束 (End of Stream)**。
*   **逻辑**:
    ```python
    # 伪代码
    full_response = await stream_to_frontend()
    if full_response:
        db.save_history(session_id, user_query, full_response)
    ```

---

## 5. 分布式并发控制 (Concurrency Control)

为了防止多 Pod 部署时产生的并发写入导致数据乱序，我们采用 **Redis 分布式锁 + 逻辑序号** 双重保障机制。

### 5.1 写入保护：Redis 分布式锁
*   **锁 Key**: `lock:session:{session_id}:write`
*   **时机**: 在 `session_service.save_history` 执行 Read-Modify-Write 之前。
*   **超时**: TTL = 5秒 (防止死锁)。
*   **逻辑**:
    ```python
    with redis_lock(f"lock:session:{session_id}", timeout=5):
        history = db.get_history(session_id)
        # 临界区：确保读到的是最新的，且我是唯一在写的
        last_seq = history[-1].seq_id
        new_msg.seq_id = last_seq + 1
        history.append(new_msg)
        db.save_history(session_id, history)
    ```

### 5.2 数据自证：逻辑序号 (Sequence ID)
即便在锁失效的极端边缘情况（如 Redis 主从切换），`seq_id` 也能作为最后的防线。
*   **生成规则**: `seq_id` 基于当前数据库中已有的最大值 + 1。
*   **查询规则**: 服务端返回给前端前，执行一次 `history.sort(key=lambda x: x.seq_id)`，确保展示永远是有序的。

---

## 6. 异常恢复与边缘情况 (Edge Cases)

### Q1: 如果 LangGraph 跑了一半服务挂了？
*   **State**: 停留在上一个成功的 Checkpoint（如 `node_search` 刚结束）。
*   **History**: MySQL 没写进去。
*   **用户侧**: 看到 loading 转圈失败。
*   **重试**: 用户再次发送消息，LangGraph 从 Checkpoint 恢复，**继续执行未完成的步骤**。数据最终一致。

### Q2: 如果流式推完了，但 MySQL 写入失败？
*   **State**: 已更新。
*   **History**: 丢失最后一句。
*   **补救**: 这属于严重系统错误 (System Error)。虽然 State 还在，但用户记录丢了。生产环境可引入 **MQ 异步写入** 作为兜底（Write-Ahead Log）。

---

## 7. 架构演进路线

1.  **Phase 1 (Current)**:
    *   State -> `MemorySaver`
    *   History -> MySQL (无锁)
2.  **Phase 2 (Prod Ready)**:
    *   State -> `RedisSaver`
    *   History -> MySQL + Redis Lock
3.  **Phase 3 (High Scale)**:
    *   History -> 异步写入 (Kafka/RabbitMQ) -> MySQL
