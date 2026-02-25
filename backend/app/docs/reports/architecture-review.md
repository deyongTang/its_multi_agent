# ITS 多智能体系统架构审查报告

> 日期: 2026-02-23 | 版本: v1.0

---

## 1. 数据流全貌

一次用户请求的完整链路：

```
前端 POST /api/query
  → TraceIdMiddleware 注入 trace_id
  → routers.py 创建 StreamingResponse
  → agent_service_v2.py:
      1. session_service.prepare_history() 从 JSON 文件读历史，裁剪到最近 3 轮
      2. workflow_runner.stream_run():
         - 检查 Redis Checkpointer 有无 checkpoint
         - 有 → update_state 追加消息，从断点继续（slots 自动恢复）
         - 无 → 用历史初始化 messages，全新执行
      3. astream_events → workflow_stream_service 解析事件 → SSE 推送
      4. 拼接 full_ai_response → session_service.save_history() 写回 JSON 文件
```

---

## 2. 双模型架构

| 模型 | 提供商 | 用途 | 调用节点 |
|------|--------|------|---------|
| `main_model` (Qwen3-32B) | 硅基流动 | 最终答案生成 | `node_generate_report` |
| `sub_model` (qwen3-max) | 阿里百炼 | 轻量决策任务 | `node_intent`、`node_slot_filling`、`node_ask_user`、`node_general_chat` |

分工合理：重活用大模型，轻活用小模型，控制成本。

---

## 3. 双 SDK 共存现状

`openai_client.py` 同时维护两套 SDK：

- **LangChain ChatOpenAI** — 给 LangGraph 工作流用（`main_model`、`sub_model`）
- **OpenAI Agents SDK** — 给旧版 Orchestrator 用（`agents_main_model`、`agents_sub_model`）

旧版 Agents SDK 的代码（`agents_*` 系列）目前只被 `service_station.py` 的 `@function_tool` 装饰器引用，以及 `mcp_servers.py` 的 `MCPServerSse`。LangGraph 版本和 Agents SDK 版本的工具定义混在一起，属于历史遗留。

---

## 4. 会话存储实际状态

文档里写的 Phase 3 目标是 MySQL，但当前实际实现是 **JSON 文件系统**：

- `session_repository.py` → `user_memories/{user_id}/{session_id}.json`
- 与 `session-persistence.md` 的 Phase 1 描述一致

---

## 5. 架构层面问题

### 5.1 `node_generate_report` 用 `ainvoke` 破坏了流式体验

**位置**: `action_nodes.py:88`

`main_model.ainvoke()` 是阻塞式调用。虽然 `openai_client.py` 里 `main_model` 设置了 `streaming=True`，但 `ainvoke` 会等完整响应返回后才写入 `messages`。

`workflow_stream_service.py` 的 `on_chat_model_stream` 处理逻辑是正确的，但它只能捕获到 LangGraph 节点内部直接使用 LLM 时的流式事件。`ainvoke` 在节点内部消费完了所有 token，外部的 `astream_events` 看到的是一个完整的 `AIMessage` 一次性出现。

**用户体验**：前面的意图识别、槽位填充、搜索过程都有实时 PROCESS 事件推送，但到了最关键的答案生成环节，突然卡住几秒，然后全文一次性出现。

---

### 5.2 知识库调用链路存在双重 LLM 生成

**位置**: `knowledge_base.py:28-32` → `action_nodes.py:88`

`knowledge_base.py` 调用知识库平台的 `/query` 接口，该接口内部已经做了 RAG（检索 + LLM 生成），返回的是一个完整的答案字符串。然后 `node_generate_report` 又把这个答案字符串作为"参考资料"，再调一次 LLM 生成最终回答。

**实际效果**：
- 知识库 LLM 生成了一遍答案 → app 层 LLM 又改写了一遍
- 用户看到的是"二手加工"的内容
- 两次 LLM 调用的成本和延迟叠加

**现实约束**：知识库平台是独立部署的服务，`/query` 接口返回完整答案，不提供"只返回原始 chunks"的接口。解决需要知识库平台配合改造。

---

### 5.3 `strategy_gen_node` 生成的策略没有被消费

**位置**: `strategy_gen_node.py` → `search_nodes.py`

`strategy_gen_node` 生成 `RetrievalStrategy`（包含 `query_tags`、`search_kwargs`），写入 state。但三个搜索节点全部直接从 `messages` 取最后一条用户消息作为 query，完全没有读取 `state["retrieval_strategy"]`。

该节点目前是纯空转（不消耗 LLM，是普通函数），但增加了不必要的 graph 节点和状态流转。

---

### 5.4 Agents SDK 和 LangGraph 的工具定义混用

`service_station.py` 里的函数同时有两个版本：
- `resolve_user_location_from_text_raw` — 给 LangGraph 节点直接调用
- `resolve_user_location_from_text = function_tool(...)` — 给旧版 Agents SDK 用

`mcp_servers.py` 用的是 `agents.mcp.MCPServerSse`（Agents SDK 的 MCP 客户端），但它被 LangGraph 节点调用。LangGraph 工作流依赖了 Agents SDK 的 MCP 实现。

影响：
- 无法干净地移除 Agents SDK 依赖
- MCP 客户端的生命周期管理绑定在 Agents SDK 的实现上

---

### 5.5 `verify` 节点和重试机制是空壳

**位置**: `merge_verify_nodes.py:48-70`

`node_verify` 返回空字典，不做任何校验。`state.py` 里定义了 `retry_count`、`error_log`，`strategy_gen_node` 里也有 `if retry_count > 0` 的逻辑，但 graph 拓扑里没有从 verify 回到 strategy_gen 的边。

重试循环在 v1.4 被移除（注释说"不再进行循环重试"），但相关的状态字段和节点代码还留着。

`node_escalate` 返回一条固定文本，没有对接任何工单系统。

---

### 5.6 会话存储是 JSON 文件，不适合生产

`session_repository.py` 用 JSON 文件存储会话历史。`save_history` 每次都是全量覆盖写入（读出全部 → 追加 → 写回全部），随着对话轮数增加，单个文件越来越大，写入性能线性下降。多实例部署时文件系统不共享，分布式锁也无法保护。

---

## 6. 升级优先级

| 优先级 | 问题 | 改动范围 | 收益 |
|--------|------|---------|------|
| P0 | `ainvoke` → 真流式生成 | `action_nodes.py` | 用户体验质变 |
| P1 | 知识库返回 chunks 而非答案 | `knowledge` 平台 + `search_nodes.py` | 消除双重 LLM，降本提质 |
| P1 | 会话存储升级到 MySQL | `session_repository.py` | 生产可用 |
| P2 | 清理 Agents SDK 残留 | `openai_client.py`、`service_station.py`、`mcp_servers.py` | 降低维护成本 |
| P2 | `strategy_gen` 要么用起来要么删掉 | `strategy_gen_node.py` + `search_nodes.py` | 消除空转 |
| P3 | `verify` 实现真实质量校验 | `merge_verify_nodes.py` | 系统韧性 |
| P3 | `escalate` 对接工单系统 | `action_nodes.py` | 人工兜底闭环 |
