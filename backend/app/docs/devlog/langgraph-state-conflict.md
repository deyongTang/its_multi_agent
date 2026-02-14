# 开发日志 - LangGraph 并行节点状态冲突问题

**日期**: 2026-01-29
**问题类型**: LangGraph 架构错误
**严重程度**: 高（阻塞性错误）

---

## 问题描述

在使用 LangGraph 构建多智能体工作流时，遇到以下错误：

```
At key 'retrieved_documents': Can receive only one value per step.
Use an Annotated key to handle multiple values.
```

### 错误触发场景

当多个并行节点（parallel nodes）同时更新同一个状态字段时，如果该字段没有使用 `Annotated` 和 reducer 函数，LangGraph 会抛出此错误。

---

## 错误根源分析

### 1. 问题代码位置

**状态定义文件**: `backend/app/multi_agent/workflow/state.py:58`

```python
class AgentState(TypedDict):
    # ... 其他字段 ...

    # ❌ 错误写法：没有使用 Annotated
    retrieved_documents: List[Any]  # 检索到的文档
```

**并行节点文件**: `backend/app/multi_agent/workflow/nodes/search_nodes.py`

```python
async def node_search_es(state: AgentState) -> dict:
    """并行节点 1: ES 搜索"""
    return {"retrieved_documents": [{"source": "ES", "content": "..."}]}

async def node_search_baidu(state: AgentState) -> dict:
    """并行节点 2: 百度搜索"""
    return {"retrieved_documents": [{"source": "Baidu", "content": "..."}]}

async def node_search_tools(state: AgentState) -> dict:
    """并行节点 3: 工具搜索"""
    return {"retrieved_documents": [{"source": "Tools", "content": "..."}]}
```

### 2. 冲突原因

在 LangGraph 工作流中，当多个节点被配置为**并行执行**（使用 `add_edge` 连接到同一个下游节点）时：

```
     ┌─────────────┐
     │ strategy_gen│
     └──────┬──────┘
            │
     ┌──────┴──────┐
     │   (并行)    │
     ├─────┬───────┼─────┐
     │     │       │     │
┌────▼──┐ ┌▼────┐ ┌▼────▼──┐
│search │ │search│ │search  │
│  ES   │ │Baidu │ │ tools  │
└───┬───┘ └──┬───┘ └───┬────┘
    │        │         │
    └────────┼─────────┘
             │
      ┌──────▼──────┐
      │merge_rerank │
      └─────────────┘
```

这三个搜索节点会**同时执行**，并且都尝试更新 `retrieved_documents` 字段。

**LangGraph 的默认行为**：
- 对于普通字段（非 `Annotated`），每个 step 只能接收**一个值**
- 当多个并行节点同时返回同一个 key 时，LangGraph 不知道如何合并，直接报错

---

## 解决方案

### ✅ 正确写法：使用 Annotated + Reducer

修改 `backend/app/multi_agent/workflow/state.py:58`：

```python
from typing import TypedDict, Annotated, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
import operator  # ← 导入 operator

class AgentState(TypedDict):
    # ... 其他字段 ...

    # ✅ 正确写法：使用 Annotated 和 operator.add
    retrieved_documents: Annotated[List[Any], operator.add]  # 检索到的文档（支持并行追加）
```

### 工作原理

**`Annotated[List[Any], operator.add]` 的含义**：

1. **`List[Any]`**: 字段类型是列表
2. **`operator.add`**: 当多个节点同时更新此字段时，使用 `+` 运算符合并结果

**执行流程**：

```python
# 并行节点 1 返回
{"retrieved_documents": [{"source": "ES", "content": "..."}]}

# 并行节点 2 返回
{"retrieved_documents": [{"source": "Baidu", "content": "..."}]}

# 并行节点 3 返回
{"retrieved_documents": [{"source": "Tools", "content": "..."}]}

# LangGraph 自动合并（使用 operator.add）
state["retrieved_documents"] = [
    {"source": "ES", "content": "..."},
    {"source": "Baidu", "content": "..."},
    {"source": "Tools", "content": "..."}
]
```

---

## 类比：messages 字段的正确示例

在同一个文件中，`messages` 字段已经正确使用了 `Annotated`：

```python
# backend/app/multi_agent/workflow/state.py:39
messages: Annotated[List[BaseMessage], operator.add]
```

这就是为什么多个节点可以同时追加消息而不会冲突。

---

## 常见的 Reducer 函数

根据不同的合并需求，可以使用不同的 reducer：

| Reducer | 用途 | 示例 |
|---------|------|------|
| `operator.add` | 列表追加 | `[1, 2] + [3] = [1, 2, 3]` |
| `operator.or_` | 字典合并 | `{"a": 1} \| {"b": 2} = {"a": 1, "b": 2}` |
| 自定义函数 | 复杂逻辑 | 去重、排序、加权合并等 |

### 自定义 Reducer 示例

如果需要去重合并，可以定义自定义 reducer：

```python
def merge_unique_docs(existing: List[dict], new: List[dict]) -> List[dict]:
    """去重合并文档"""
    seen = {doc.get("content") for doc in existing}
    result = existing.copy()
    for doc in new:
        if doc.get("content") not in seen:
            result.append(doc)
            seen.add(doc.get("content"))
    return result

# 使用自定义 reducer
retrieved_documents: Annotated[List[Any], merge_unique_docs]
```

---

## 何时需要使用 Annotated

### ✅ 必须使用 Annotated 的场景

1. **并行节点更新同一字段**
   - 多个节点同时执行，返回相同的 key
   - 例如：多路检索、并行工具调用

2. **多轮对话历史追加**
   - 每个节点都可能追加消息到 `messages`
   - 需要保留完整的对话链

3. **累积型数据收集**
   - 错误日志、执行步骤、诊断记录等
   - 需要在整个工作流中持续追加

### ❌ 不需要使用 Annotated 的场景

1. **单一节点更新的字段**
   - 只有一个节点会修改此字段
   - 例如：`current_intent`、`intent_confidence`

2. **覆盖型字段**
   - 每次更新都是完全替换，不需要合并
   - 例如：`final_report`、`need_human_help`

---

## 调试技巧

### 1. 如何快速定位问题

当遇到 "Can receive only one value per step" 错误时：

**步骤 1**: 查看错误信息中的 key 名称
```
At key 'retrieved_documents': Can receive only one value per step.
                ↑
            问题字段名
```

**步骤 2**: 在代码中搜索该字段
```bash
grep -r "retrieved_documents" backend/app/multi_agent/workflow/
```

**步骤 3**: 检查是否有多个节点返回该字段
- 查看所有 `return {"retrieved_documents": ...}` 的位置
- 检查工作流图中是否有并行边

**步骤 4**: 在 `state.py` 中添加 `Annotated`

### 2. 验证并行节点配置

检查工作流图定义（`graph.py`）：

```python
# 查找是否有并行边配置
graph.add_edge("strategy_gen", "search_es")
graph.add_edge("strategy_gen", "search_baidu")
graph.add_edge("strategy_gen", "search_tools")
# ↑ 这三条边会导致并行执行
```

---

## 最佳实践建议

### 1. 状态字段设计原则

**原则 1: 明确字段的更新模式**

在设计状态字段时，先问自己：
- 这个字段会被多个节点同时更新吗？ → 使用 `Annotated`
- 这个字段只会被单个节点更新吗？ → 不需要 `Annotated`

**原则 2: 为累积型数据使用 Annotated**

以下类型的字段建议使用 `Annotated[List, operator.add]`：

```python
# ✅ 推荐使用 Annotated
messages: Annotated[List[BaseMessage], operator.add]           # 对话历史
retrieved_documents: Annotated[List[Any], operator.add]        # 检索结果
error_log: Annotated[List[str], operator.add]                 # 错误日志
steps: Annotated[List[DiagnosisStep], operator.add]           # 执行步骤
```

**原则 3: 为单值字段使用普通类型**

```python
# ✅ 不需要 Annotated
current_intent: Optional[str]                                  # 当前意图
intent_confidence: float                                       # 置信度
need_human_help: bool                                          # 是否需要人工
final_report: Optional[Dict[str, Any]]                         # 最终报告
```

### 2. 工作流设计建议

**建议 1: 使用 Fan-Out/Fan-In 模式**

当需要并行执行多个任务时，使用标准的扇出/扇入模式：

```python
# Fan-Out: 一个节点分发到多个并行节点
graph.add_edge("strategy_gen", "search_es")
graph.add_edge("strategy_gen", "search_baidu")
graph.add_edge("strategy_gen", "search_tools")

# Fan-In: 多个并行节点汇聚到一个合并节点
graph.add_edge("search_es", "merge_rerank")
graph.add_edge("search_baidu", "merge_rerank")
graph.add_edge("search_tools", "merge_rerank")
```

**建议 2: 在合并节点中处理数据**

不要在并行节点中做复杂的数据处理，将合并逻辑放在 Fan-In 节点：

```python
def node_merge_rerank(state: AgentState) -> dict:
    """合并并行节点的结果"""
    raw_docs = state.get("retrieved_documents", [])

    # 去重
    unique_docs = deduplicate(raw_docs)

    # 重排序
    ranked_docs = rerank(unique_docs)

    # 返回处理后的结果（覆盖原始数据）
    return {"retrieved_documents": ranked_docs}
```

---

## 相关资源

### LangGraph 官方文档

- [State Management](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Reducers](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers)
- [Parallel Execution](https://langchain-ai.github.io/langgraph/how-tos/branching/)

### 项目中的参考实现

- **正确示例**: `messages` 字段 ([state.py:39](../multi_agent/workflow/state.py#L39))
- **修复位置**: `retrieved_documents` 字段 ([state.py:58](../multi_agent/workflow/state.py#L58))
- **并行节点**: 搜索节点 ([search_nodes.py](../multi_agent/workflow/nodes/search_nodes.py))

---

## 总结

### 核心要点

1. **并行节点更新同一字段时，必须使用 `Annotated` + reducer**
2. **`operator.add` 是最常用的 reducer，用于列表追加**
3. **参考 `messages` 字段的实现方式**
4. **在设计状态时，提前考虑字段的更新模式**

### 记忆口诀

> **多节点同时写，Annotated 不能少**
> **列表追加用 add，字典合并用 or**
> **单节点独占写，普通类型就够了**

---

**修复状态**: ✅ 已修复
**修复文件**: `backend/app/multi_agent/workflow/state.py`
**修复内容**: 将 `retrieved_documents: List[Any]` 改为 `retrieved_documents: Annotated[List[Any], operator.add]`

