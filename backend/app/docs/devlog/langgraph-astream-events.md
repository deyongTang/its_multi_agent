# LangGraph astream_events 事件参考

**日期**: 2026-02-24
**类型**: 学习笔记

---

## 什么是 astream_events

`graph.astream_events(state, config, version="v2")` 是 LangGraph 提供的流式事件接口。
每次工作流执行，LangGraph 会自动产生一系列事件，我们通过异步迭代消费它们。

```python
async for event in self.graph.astream_events(initial_state, config, version="v2"):
    kind = event.get("event")   # 事件类型
    name = event.get("name")    # 节点/模型/工具名称
    data = event.get("data")    # 事件携带的数据
```

---

## 事件类型全览

### 1. on_chain_start / on_chain_end

图或节点的生命周期事件。

| name 值 | 含义 |
|---------|------|
| `LangGraph` | 整个工作流开始/结束 |
| `node_intent` / `ask_user` / ... | 某个具体节点开始/结束 |

**我们的用法**：`on_chain_end` + `name == "ask_user"` 时，从 `data["output"]` 取出追问内容发给前端：

```python
elif kind == "on_chain_end" and name == "ask_user":
    output = data.get("output", {})
    messages = output.get("messages", [])
    pending_intent = output.get("current_intent", "")
```

`data["output"]` 就是该节点返回的完整 AgentState，可以读取任意字段。

---

### 2. on_node_start

每个节点开始执行时触发，`name` 是节点名称。

```python
elif kind == "on_node_start":
    node_name = name  # e.g. "intent", "slot_filling", "ask_user"
```

**我们的用法**：过滤掉 `__start__` / `__end__` 等内部节点，向前端发送进度提示。

---

### 3. on_chat_model_stream

LLM 流式输出时，每个 token 触发一次。`data["chunk"]` 是 LangChain 的 `AIMessageChunk`。

```python
elif kind == "on_chat_model_stream":
    chunk = data.get("chunk")
    reasoning = chunk.additional_kwargs.get("reasoning_content")  # 推理内容（DeepSeek R1等）
    content = chunk.content                                        # 正文内容
```

**我们的用法**：分别提取 `reasoning_content`（THINKING）和 `content`（ANSWER）发给前端。

---

### 4. on_tool_start / on_tool_end

工具调用的生命周期事件。

```python
elif kind == "on_tool_start":
    tool_name = name
    tool_input = data.get("input")

elif kind == "on_tool_end":
    tool_output = data.get("output")
```

**我们的用法**：`on_tool_start` 时向前端发送"调用工具: xxx"的进度提示。

---

### 5. on_custom_event

节点内部通过 `adispatch_custom_event` 手动触发的自定义事件，用于向外暴露节点内部状态。

```python
# 节点内部（发送方）
from langchain_core.callbacks import adispatch_custom_event
await adispatch_custom_event("retrieved_docs", {"docs": docs})

# stream_service（接收方）
elif kind == "on_custom_event":
    event_name = name
    payload = data
```

**我们的用法**：目前预留，未来可用于把检索到的文档详情推送给前端。

---

## 事件数据结构

每个 event 的完整结构：

```python
{
    "event": "on_chat_model_stream",   # 事件类型
    "name": "ChatOpenAI",              # 触发源名称
    "run_id": "uuid...",               # 本次运行ID
    "tags": [...],                     # 标签
    "metadata": {...},                 # 元数据（含 langgraph_node 等）
    "data": {                          # 事件数据，不同事件结构不同
        "chunk": AIMessageChunk(...)   # on_chat_model_stream 特有
        "input": {...},                # on_*_start 特有
        "output": {...},               # on_*_end 特有
    }
}
```

---

## 我们消费的事件汇总

| 事件 | name 过滤 | 用途 | 发给前端的类型 |
|------|----------|------|--------------|
| `on_chain_end` | `ask_user` | 取追问内容 + pending_intent | ANSWER (is_ask_user=True) |
| `on_node_start` | 非内部节点 | 节点进度提示 | PROCESS |
| `on_chat_model_stream` | - | LLM 流式输出 | THINKING / ANSWER |
| `on_tool_start` | - | 工具调用提示 | PROCESS |
| `on_custom_event` | - | 预留扩展 | - |

---

## 涉及文件

| 文件 | 职责 |
|------|------|
| [workflow_stream_service.py](../../services/workflow_stream_service.py) | 消费 astream_events，转换为 SSE |
| [runner.py](../workflow/runner.py) | 调用 `graph.astream_events`，产生事件流 |
