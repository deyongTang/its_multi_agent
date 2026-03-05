# LangGraph 工作流引擎 - v2.2 (意图纠错精准化)

## 概述

基于 LangGraph 的状态机编排引擎，实现意图识别、槽位填充、检索子图自主循环、意图自纠错等功能。

**当前版本：v2.2**
- v1.x：Phase 1，基础意图 + 槽位填充
- v2.0：混合架构，外层显式管道 + 内层检索子图自主循环
- v2.1：意图自纠错（verify 失败 → 反思意图 → 重走流程）
- v2.2：意图纠错精准化
  - verify 节点不再因质量问题清空文档，改为"只告知，不拦截"
  - 意图纠错仅对本地工具路径（service_station / poi_navigation）生效
  - tech_issue / search_info 的检索子图内部已有网络搜索兜底，无需纠错意图

## 目录结构

```
workflow/
├── __init__.py
├── state.py                   # AgentState + RetrievalSubState 定义
├── graph.py                   # 主图定义（所有节点和边的编排）
├── retrieval_subgraph.py      # 检索子图定义
├── runner.py                  # WorkflowRunner（LangSmith 集成）
├── nodes/
│   ├── intent_node.py                 # 意图识别（L1/L2）
│   ├── slot_filling_node.py           # 槽位填充（增量合并）
│   ├── ask_user_node.py               # 追问生成
│   ├── general_chat_node.py           # 闲聊回复
│   ├── retrieval_subgraph_nodes.py    # 子图：dispatch/search/evaluate/rewrite
│   ├── evaluation_strategies.py       # 评估策略（KB/Web/LocalTools 分策略）
│   ├── intent_reflect_node.py         # 意图自纠错节点（v2.1 新增）
│   ├── merge_verify_nodes.py          # 结果质量校验（LLM 判断）
│   └── action_nodes.py                # generate_report + escalate
└── edges/
    ├── route_intent.py                # 意图路由
    ├── route_slot_check.py            # 槽位完整性路由
    ├── route_ask_user.py              # 追问结果路由
    └── routers_phase2.py              # route_verify_result + route_after_reflect
```

## 完整流程图（v2.1）

```
START
  ↓
node_intent（意图识别：tech_issue / service_station / poi_navigation / search_info / chitchat）
  ↓
route_intent
  ├─→ chitchat → node_general_chat → END
  └─→ business → node_slot_filling（槽位提取）
                    ↓
                  route_slot_check
                    ├─→ 缺失槽位 → node_ask_user → END（等待用户补充）
                    └─→ 槽位齐全 → node_retrieval（检索子图桥接）

                          ┌──────────────────────────────────┐
                          │  检索子图（max 3 loops）          │
                          │  dispatch → search → evaluate    │
                          │    ↑           ↓（不够好）        │
                          │    └── rewrite（改写/换源）       │
                          └──────────────────────────────────┘
                                  ↓
                          node_verify（LLM 质量校验，只告知不拦截）
                                  ↓
                          route_verify_result
                            ├─→ 有文档                                  → node_generate_report → END
                            ├─→ 无文档 & service_station/poi & 首次失败  → node_intent_reflect（意图反思）
                            │                              ↓
                            │                        route_after_reflect
                            │                          ├─→ 意图已纠正 → node_slot_filling（重走流程）
                            │                          └─→ 意图正确   → node_escalate → END
                            └─→ 无文档 & 其他意图 / 已纠错过             → node_escalate → END

  注：tech_issue 和 search_info 检索子图内部已有 KB→Web 换源兜底，
      若仍无结果说明系统里确实没有答案，直接转人工，无需纠错意图。
```

## 节点说明

### 主图节点

| 节点 | 文件 | 职责 |
|------|------|------|
| `intent` | `nodes/intent_node.py` | L1/L2 意图分类 |
| `slot_filling` | `nodes/slot_filling_node.py` | 根据意图提取槽位，增量合并 |
| `ask_user` | `nodes/ask_user_node.py` | 生成追问，最多 3 轮后升级人工 |
| `general_chat` | `nodes/general_chat_node.py` | 闲聊回复 |
| `retrieval` | `graph.py::node_retrieval` | 桥接主图 ↔ 检索子图 |
| `verify` | `nodes/merge_verify_nodes.py` | LLM 判断检索结果质量（只告知，不清空文档、不拦截流程） |
| `intent_reflect` | `nodes/intent_reflect_node.py` | 反思意图是否识别错误（仅对本地工具意图触发，最多 1 次） |
| `generate_report` | `nodes/action_nodes.py` | 综合检索结果生成最终答案（流式） |
| `escalate` | `nodes/action_nodes.py` | 标记 `need_human_help=True`，转人工 |

### 检索子图节点

| 节点 | 职责 |
|------|------|
| `dispatch` | 意图 → 数据源映射（tech→kb, search_info→web, service/poi→local_tools） |
| `search` | 执行检索（知识库 API / Web 搜索 / MySQL+MCP） |
| `evaluate` | 按数据源分策略评估结果质量（KB 用规则，Web 用 LLM，LocalTools 用字段校验） |
| `rewrite` | LLM 改写 query 或切换数据源（kb→web 单向兜底） |

## 路由说明

| 路由函数 | 位置 | 逻辑 |
|----------|------|------|
| `route_intent` | `edges/route_intent.py` | chitchat→general_chat，其余→slot_filling |
| `route_slot_check` | `edges/route_slot_check.py` | 有缺失→ask_user，齐全→retrieval；**意图纠错回流时有缺失也直接→retrieval（不再追问）** |
| `route_evaluate` | `retrieval_subgraph.py` | sufficient 或达上限→exit，否则→rewrite |
| `route_verify_result` | `edges/routers_phase2.py` | 有文档→report；无文档&本地工具意图&首次→intent_reflect；其余→escalate |
| `route_after_reflect` | `edges/routers_phase2.py` | 意图已纠正→slot_filling，意图未变→escalate |

## 状态定义

### AgentState（主图黑板）

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    user_id: str
    trace_id: str
    current_intent: Optional[str]    # L2 意图
    intent_confidence: float
    slots: Dict[str, Any]
    missing_slots: List[str]
    ask_user_count: int              # 追问计数（max 3）
    original_query: Optional[str]   # 原始问题（追问场景保留）
    retrieved_documents: List[Any]
    need_human_help: bool
    final_report: Optional[Dict]
    intent_retry_count: int          # 意图纠错次数（max 1，v2.1 新增）
    intent_corrected: bool           # 本轮意图是否已被纠正（v2.1 新增）
```

### RetrievalSubState（检索子图隔离状态）

```python
class RetrievalSubState(TypedDict):
    query: str              # 当前 query（可被 rewrite 改写）
    original_query: str     # 原始 query（不变）
    intent: str
    slots: Dict[str, Any]
    source: str             # kb / web / local_tools
    documents: List[Dict]
    is_sufficient: bool
    suggestion: str         # pass / retry_same / switch_source
    loop_count: int
    max_retries: int        # 默认 3
```

## 快速上手

```bash
# 安装依赖
pip install -r requirements.txt

# 运行工作流测试
python -m multi_agent.workflow.test_workflow

# 查看 ASCII 流程图
python -c "from multi_agent.workflow.graph import create_workflow_graph; g = create_workflow_graph(); g.get_graph().print_ascii()"
```

## 参考文档

- `docs/architecture/workflow-engine.md` — 详细设计文档（节点/边/状态全量定义）
- `docs/architecture/upgrade-plan-v2.md` — 各阶段升级计划与进度
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
