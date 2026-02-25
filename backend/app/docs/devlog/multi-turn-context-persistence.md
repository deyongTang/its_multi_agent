# 开发日志 - 多轮追问上下文断链问题

**日期**: 2026-02-23
**问题类型**: 架构设计缺陷
**严重程度**: 高（核心业务流程失效）

---

## 问题描述

追问（Ask User）场景下，第二轮回复无法正确延续第一轮的意图和问题上下文。

**复现步骤**：
1. 用户发送："明天天气怎么样"
2. 系统追问："请问您所在的城市？"
3. 用户回复："深圳市"
4. 系统错误地将"深圳市"识别为 `poi_navigation` 意图，而非继续 `search_info` 流程

**实际日志**：
```
[Intent] 识别结果: poi_navigation  ← 错误，应为 search_info
[Retrieval Search] query=深圳市    ← 错误，应为"明天天气怎么样 深圳市"
[Verify] 质量校验未通过             ← 因为用"深圳市"去搜天气，结果不相关
```

---

## 根本原因分析

### 核心矛盾：无状态工作流 vs 有状态多轮对话

LangGraph 工作流是**无状态**的——每次请求都从零构建 `initial_state`，上一轮的运行时状态全部丢失。但追问场景天然是**有状态**的，需要跨轮次保留三类信息：

| 信息类型 | 第一轮产生 | 第二轮需要 | 丢失后果 |
|---------|-----------|-----------|---------|
| 意图 (`current_intent`) | `search_info` | 跳过 LLM 重识别 | LLM 把"深圳市"识别为 `poi_navigation` |
| 原始问题 (`original_query`) | "明天天气怎么样" | 拼接检索 query | 只用"深圳市"检索，结果无关 |
| 追问标记 (`ask_user_count`) | 1 | 触发追问逻辑 | 走普通流程，槽位重新收集 |

### 断链的完整链路

```
Turn 1: "明天天气怎么样"
  intent_node → LLM 识别 → search_info ✅
  slot_filling → 缺少 [地点]
  ask_user_node → 追问，工作流结束
  ↓
  ❌ 所有运行时状态丢失（current_intent, original_query 等）

Turn 2: "深圳市"
  runner.py → initial_state: current_intent=None, original_query=None
  intent_node → LLM 重新识别 "深圳市" → poi_navigation ❌
  retrieval → query="深圳市" ❌
  verify → "深圳市"搜不到天气 → 质量校验失败 ❌
  escalate → 转人工 ❌
```

---

## 解决方案：三层状态持久化

将 LangGraph 运行时状态**序列化到 Session 存储**，下一轮请求时**反序列化回 initial_state**，绕过无状态限制。

### 第一层：意图持久化

**问题**：`current_intent` 在工作流结束后丢失，下一轮 LLM 重识别出错。

**方案**：通过 SSE 事件流将意图传递到 Session 存储。

```
ask_user_node 执行
  → LangGraph state 中有 current_intent="search_info"
  ↓
workflow_stream_service.py
  on_chain_end/ask_user 事件 → 从 output 提取 current_intent
  → SSE packet 携带 pending_intent="search_info"
  ↓
agent_service_v2.py
  解析 SSE → 检测到 is_ask_user=True
  → 保存到 session: {role:"assistant", is_ask_user:true, pending_intent:"search_info"}
  ↓
Turn 2: runner.py
  chat_history[-1].pending_intent → initial_state.current_intent="search_info"
  ↓
intent_node
  ask_user_count>0 且 current_intent 已有值 → 跳过 LLM，直接复用 ✅
```

**关键代码**（[workflow_stream_service.py](../../services/workflow_stream_service.py)）：
```python
elif kind == "on_chain_end" and name == "ask_user":
    output = data.get("output", {})
    pending_intent = output.get("current_intent", "")
    packet["is_ask_user"] = True
    packet["pending_intent"] = pending_intent  # 意图随 SSE 传出
```

**关键代码**（[runner.py](../workflow/runner.py)）：
```python
is_followup = bool(chat_history and chat_history[-1].get("is_ask_user"))
restored_intent = chat_history[-1].get("pending_intent") if is_followup else None
initial_state["current_intent"] = restored_intent  # 恢复意图
```

---

### 第二层：原始问题持久化

**问题**：第二轮只有"深圳市"，检索时丢失了"明天天气怎么样"。

**方案**：`runner.py` 从历史记录中反向查找原始问题，写入 `original_query`。

```python
# runner.py：追问场景，找到 ask_user 消息之前的最后一条 user 消息
if is_followup:
    for msg in reversed(chat_history[:-1]):  # 跳过最后的 ask_user assistant 消息
        if msg.get("role") == "user":
            original_query = msg.get("content")  # "明天天气怎么样"
            break
initial_state["original_query"] = original_query
```

**检索时合并**（[graph.py](../workflow/graph.py)）：
```python
original_query = state.get("original_query") or user_query
combined_query = f"{original_query} {user_query}"  # "明天天气怎么样 深圳市"
```

---

### 第三层：报告生成上下文

**问题**：LLM 生成报告时只看到最后一条消息"深圳市"，不知道用户真正想问什么。

**方案**：`action_nodes.py` 将原始问题和补充信息合并后传给 LLM。

```python
# action_nodes.py
if original_query and original_query != last_user_query:
    user_query = f"{original_query}（补充信息：{last_user_query}）"
    # → "明天天气怎么样（补充信息：深圳市）"
```

---

## 修复后的完整数据流

```
Turn 1: "明天天气怎么样"
  intent_node: LLM → search_info
  slot_filling: missing=[地点]
  ask_user_node: 追问，state.current_intent=search_info
  workflow_stream_service: SSE packet {is_ask_user:true, pending_intent:"search_info"}
  agent_service_v2: session 保存 {pending_intent:"search_info"}
  session[-2]: {role:"user", content:"明天天气怎么样"}  ← 原始问题留在历史里

Turn 2: "深圳市"
  runner.py:
    is_followup=True
    restored_intent="search_info"       ← 从 pending_intent 恢复
    original_query="明天天气怎么样"      ← 从 session[-2] 恢复
    ask_user_count=1
  intent_node: ask_user_count>0 且 current_intent 已有值 → 跳过 LLM ✅
  slot_filling: 动态槽位，提取 地点=深圳市，missing=[] ✅
  retrieval: query="明天天气怎么样 深圳市" ✅
  evaluate: 天气结果与天气问题相关 → sufficient=true ✅
  verify: 质量校验通过 ✅
  generate_report: "明天天气怎么样（补充信息：深圳市）" → 只回答天气 ✅
```

---

## 涉及文件

| 文件 | 修改内容 |
|------|---------|
| [state.py](../workflow/state.py) | `AgentState` 增加 `original_query: Optional[str]` 字段 |
| [runner.py](../workflow/runner.py) | 追问检测、恢复 `current_intent` 和 `original_query` |
| [workflow_stream_service.py](../../services/workflow_stream_service.py) | `on_chain_end/ask_user` 事件提取并透传 `pending_intent` |
| [agent_service_v2.py](../../services/agent_service_v2.py) | 解析 `pending_intent`，保存到 session |
| [intent_node.py](../workflow/nodes/intent_node.py) | `ask_user_count>0` 且 `current_intent` 已有值时跳过 LLM |
| [graph.py](../workflow/graph.py) | `node_retrieval` 合并 `original_query + user_query` |
| [retrieval_subgraph_nodes.py](../workflow/nodes/retrieval_subgraph_nodes.py) | evaluate 使用 `original_query`，宽松判定标准 |
| [merge_verify_nodes.py](../workflow/nodes/merge_verify_nodes.py) | verify 使用 `original_query`，宽松判定标准 |
| [action_nodes.py](../workflow/nodes/action_nodes.py) | 报告生成合并原始问题 + 补充信息 |

---

## 设计原则总结

**核心思路**：LangGraph 无状态工作流 + Session 存储 = 有状态多轮对话

> 把需要跨轮次保留的状态，在工作流结束时**序列化到外部存储**（Session），下一轮开始时**反序列化回 initial_state**。工作流本身保持无状态，状态管理责任转移到 runner 层。

**三条规则**：
1. **意图不重识别**：追问轮次直接复用上一轮意图，不调用 LLM
2. **原始问题不丢失**：检索、评估、报告生成全程使用原始问题，补充信息只作为附加上下文
3. **质量判断要宽松**：网络搜索结果天然不完整，只要相关就通过，不因"不够精确"而失败

---

**修复状态**: ✅ 已修复
**验证方式**: "明天天气怎么样" → 追问 → "深圳市" → 正确返回深圳天气预报
