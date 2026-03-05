# ITS 多智能体系统架构升级计划 v2.0

> 日期: 2026-03-05 | 状态: Phase 4 ✅ 已完成，Phase 5 ✅ 已完成

---

## 1. 升级核心思路

**外层保持显式管道，检索环节内部引入自主循环。**

系统采用 LangGraph 显式编排管道，流程确定、可观测。在检索环节嵌入**带循环的子图**，让模型在受控范围内自主决策（改写 query、切换数据源）。验证环节作为主图中的独立节点，由 LLM 做质量把关。

```
外层管道（确定性）
  intent → slot_filling → [检索子图: 自主循环] → verify → generate_report → END
                ↑                                   ↓ (验证失败 & 首次)
                └────── intent_reflect（意图反思）──┘
                                                    ↓ (验证失败 & 已纠错)
                                                 escalate → END

内层子图（智能性）
  dispatch → search → evaluate → (不够好?) → rewrite → search → ...  (max 3 次)
```

---

## 2. 当前痛点与升级映射

| 当前问题 | 根因 | 升级方案 | 状态 |
| --------- | ------ | --------- | ---- |
| `verify` 节点是空壳 | 没有让模型判断结果质量 | verify 节点引入 LLM 质量判断，评估检索结果是否匹配用户问题 | ✅ 已完成 |
| `strategy_gen` 空转 | 生成的策略没被消费 | 融入检索子图 `rewrite` 节点，作为循环中的 query 改写环节 | ✅ 已完成 |
| KB miss → Web 兜底是硬编码 | 无法智能判断"结果不好但不是空" | 检索子图内 `evaluate` 节点自主判断结果质量，决定重试策略 | ✅ 已完成 |
| 双重 LLM 生成 | 知识库返回完整答案，report 又生成一遍 | 知识库改为返回 chunks，report 统一生成 | ✅ 已完成 |
| `ainvoke` 破坏流式 | 最终生成环节不是真流式 | `node_generate_report` 改用流式调用，`workflow_stream_service` 按节点来源过滤 `on_chat_model_stream` 事件 | ✅ 已完成 |

---

## 3. 当前架构（已实现）

### 3.1 整体拓扑

```
                        ┌→ general_chat → END
intent → route_intent ──┤
                        └→ slot_filling → route_slot_check ──┬→ ask_user → END
                                                             │
                                                             └→ retrieval(子图) → verify → route_verify ──┬→ generate_report → END
                                                                                                          └→ escalate → END
```

**主图节点：**

| 节点 | 文件 | 职责 |
|------|------|------|
| `intent` | `nodes/intent_node.py` | L1/L2 意图分类（tech_issue, service_station, poi_navigation, search_info, chitchat） |
| `slot_filling` | `nodes/slot_filling_node.py` | 根据意图提取所需槽位，增量合并策略 |
| `ask_user` | `nodes/ask_user_node.py` | 生成追问话术，最多 3 轮后升级人工 |
| `general_chat` | `nodes/general_chat_node.py` | 闲聊回复，引导用户回到业务问题 |
| `retrieval` | `graph.py::node_retrieval` | 桥接主图 ↔ 检索子图，状态映射 |
| `verify` | `nodes/merge_verify_nodes.py` | LLM 判断检索结果是否匹配用户问题 |
| `generate_report` | `nodes/action_nodes.py` | 综合检索结果生成最终答案 |
| `escalate` | `nodes/action_nodes.py` | 标记 `need_human_help=True`，转人工 |

**路由函数：**

| 路由 | 文件 | 逻辑 |
|------|------|------|
| `route_intent` | `edges/route_intent.py` | chitchat → general_chat，其余 → slot_filling |
| `route_slot_check` | `edges/route_slot_check.py` | 有缺失槽位 → ask_user，槽位齐全 → retrieval |
| `route_verify_result` | `edges/routers_phase2.py` | 有文档 → generate_report，无文档&首次 → intent_reflect，无文档&已纠错 → escalate |
| `route_after_reflect` | `edges/routers_phase2.py` | 意图已纠正 → slot_filling，意图未变 → escalate |

### 3.2 检索子图（已实现）

```
┌──────────────────────────────────────────────────┐
│  检索子图 (Retrieval SubGraph)                    │
│  文件: retrieval_subgraph.py                      │
│                                                  │
│  dispatch → search → evaluate ──→ exit (返回主图) │
│               ↑         ↓                        │
│               └── rewrite (max 3 次)             │
│                                                  │
│  evaluate 通过 → exit                            │
│  达到 max_retries → exit (强制退出)               │
└──────────────────────────────────────────────────┘
```

**子图节点（`nodes/retrieval_subgraph_nodes.py`）：**

- `dispatch`：根据意图映射首选数据源（tech_issue→kb, search_info→web, service_station/poi_navigation→local_tools）
- `search`：执行实际检索，根据 `source` 调用 `query_knowledge()`、`bailian_web_search()` 或本地工具（MySQL + MCP）
- `evaluate`：LLM 判断检索结果是否足够回答用户问题，返回 `is_sufficient` + `suggestion`
- `rewrite`：根据 suggestion 切换数据源（仅 kb→web 单向兜底）或 LLM 改写 query

**子图路由（`route_evaluate`）：**
- `is_sufficient=True` → exit
- `loop_count >= max_retries` → exit（确定性兜底）
- 否则 → rewrite（循环重试）

**子图状态（`RetrievalSubState`）：**

```python
class RetrievalSubState(TypedDict):
    query: str              # 当前检索 query（可被 rewrite 改写）
    original_query: str     # 原始用户 query（不变）
    intent: str             # 意图类型
    slots: Dict[str, Any]   # 槽位
    source: str             # 当前数据源: kb / web / local_tools
    documents: List[Dict]   # 本轮检索结果
    is_sufficient: bool     # evaluate 判定结果
    suggestion: str         # 建议: pass / retry_same / switch_source
    loop_count: int         # 当前循环次数
    max_retries: int        # 最大循环次数（默认 3）
```

### 3.3 验证节点（已实现）

验证环节最终实现为主图中的独立节点（非子图），由 LLM 做质量把关：

- 判断检索结果是否匹配用户问题
- 质量不合格时清空 `retrieved_documents`，触发 `route_verify_result` 走 escalate 分支
- 通过 `route_verify_result` 路由：有文档 → generate_report，无文档 → escalate

---

## 4. 不变的部分

以下环节保持当前管道模式，不引入自主循环：

| 环节 | 理由 |
|------|------|
| 意图识别 | 意图类型固定（5 种），单次 LLM 调用足够，不需要自旋 |
| 槽位填充 | 追问逻辑是确定性的（缺什么问什么），已有 `ask_user_count` 防死循环 |
| 答案生成 | 生成就是一次调用，输入（检索结果）已经过验证 |
| 会话管理 | Redis + JSON 双层架构已设计好，按 Phase 路线升级即可 |

---

## 5. 实施计划

### Phase 1：基础修复 ✅ 已完成

1. ~~知识库平台增加 `/retrieve` 接口，返回原始 chunks 而非完整答案~~
2. ~~`search_nodes.py` 对接新的 `/retrieve` 接口~~
3. ~~清理 Agents SDK 残留代码~~

### Phase 2：检索子图 ✅ 已完成

1. ~~定义 `RetrievalSubState`（`state.py`）~~
2. ~~实现 `evaluate` 节点（LLM 质量判断）~~
3. ~~实现 `rewrite` 节点（LLM query 改写 + 换源）~~
4. ~~实现 `dispatch` + `search` 节点~~
5. ~~构建子图（`retrieval_subgraph.py`），嵌入主图替代原有硬编码检索~~
6. ~~移除 `strategy_gen_node`（职责被 `rewrite` 吸收）~~

### Phase 3：验证 + 会话升级 ✅ 已完成

1. ~~verify 节点引入 LLM 质量判断~~（已完成，作为主图节点实现）
2. ~~`node_generate_report` 的 `ainvoke` → 流式调用~~（已完成：`astream` 直接在节点上下文调用，`workflow_stream_service` 按 `langgraph_node` 元数据过滤来源，只有 `generate_report`/`general_chat`/`ask_user` 节点的 token 才透传为 `ANSWER`）
3. `escalate` 对接工单系统（待处理）
4. ~~会话存储从 JSON 文件升级到 Redis/MySQL~~（已完成，见 4.5）

### Phase 4：工业级加固 ✅ 已完成

目标：将 Demo 级实现升级为生产可用，重点解决**可靠性、可观测性、健壮性**三大短板。

#### 4.1 LLM 输出结构化（优先级：P0）✅ 已完成

**问题**：`evaluate` 和 `verify` 节点用 `json.loads` 解析 LLM 自由文本，生产环境下 JSON 格式错误率约 5-10%。

**方案**：
- 引入 `safe_parse_json()` 工具函数，支持多种容错策略（正则提取、markdown 代码块剥离、截断修复）
- 解析失败时返回安全默认值，而非直接 `except` 吞掉错误

**涉及文件**：
- `infrastructure/utils/resilience.py` — `safe_parse_json` 实现
- `nodes/retrieval_subgraph_nodes.py` — `node_retrieval_evaluate` 已应用
- `nodes/merge_verify_nodes.py` — `node_verify` 已应用

#### 4.2 节点级超时 + 重试（优先级：P0）✅ 已完成

**问题**：LLM 调用无超时保护，单次卡死会阻塞整条管道。

**方案**：
- `async_retry_with_timeout` 装饰器：`asyncio.wait_for` 超时 + 指数退避重试（max 2 次）
- 应用到所有 LLM 调用节点的内部函数

**涉及文件**：
- `infrastructure/utils/resilience.py` — 装饰器实现
- `nodes/retrieval_subgraph_nodes.py` — `_llm_evaluate` / `_llm_rewrite` 已应用（timeout=20s, max_retries=2）
- `nodes/merge_verify_nodes.py` — `_llm_verify` 已应用（timeout=20s, max_retries=2）
- `nodes/action_nodes.py` — `generate_report` 用 `asyncio.wait_for` 保护（timeout=60s）

#### 4.3 可观测性增强（优先级：P1）✅ 已完成

**问题**：缺乏节点级耗时统计，线上问题难以定位。

**方案**：
- `@node_timer` 装饰器，自动记录每个节点的执行耗时（ms 级）
- 已覆盖所有主图节点和子图节点

**涉及文件**：
- `infrastructure/utils/observability.py` — 装饰器实现
- 各节点文件均已应用

#### 4.4 generate_report 真流式（优先级：P1）✅ 已完成

**问题**：`node_generate_report` 内部虽用 `astream`，但中间节点的 LLM 输出也会被当作 `ANSWER` 发给前端。

**方案**：
- `astream` 调用保持在节点函数上下文内（不包装为嵌套函数），确保 `astream_events` 能正确追踪 `langgraph_node` 元数据
- `workflow_stream_service` 读取 `event.metadata.langgraph_node`，只有 `_ANSWER_NODES`（`generate_report`/`general_chat`/`ask_user`）的 token 才透传为 `ANSWER`，其余节点的 LLM 输出静默过滤

**涉及文件**：
- `nodes/action_nodes.py` — `_collect_stream()` 内联在节点上下文
- `services/workflow_stream_service.py` — `_ANSWER_NODES` 白名单过滤

#### 4.5 会话管理升级（优先级：P1）✅ 已完成

**问题**：原方案每次保存会话时 DELETE 全部历史再全量 INSERT，随对话轮数增加代价线性增长；且无缓存层，每次加载都直接查 MySQL。

**方案**：MySQL 持久化 + Redis 缓存双层架构

```
写入路径：save_session
  → INSERT IGNORE（唯一索引保证幂等，已存在的消息自动跳过）
  → 更新 Redis 缓存（最近 7 条，TTL 24h）
  → 同步追问状态到 Redis（is_ask_user / pending_intent）

读取路径：load_session
  → 查 Redis 缓存（命中直接返回）
  → Cache miss → 查 MySQL 全量
  → 回写 Redis 缓存
```

**关键设计决策**：

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 写入策略 | `INSERT IGNORE` 增量写 | 每轮只写 2 条（user+assistant），代价恒定 |
| 缓存粒度 | 最近 7 条（system×1 + 3轮×2） | 覆盖 `prepare_history` 的 `max_turn=3` 窗口，命中率接近 100% |
| 缓存失效 | TTL 24h，写时更新 | 用户不活跃自动清理，无需主动失效 |
| 降级策略 | Redis 异常 → 直接查 MySQL | 缓存层故障不影响主流程 |

**数据库变更**：

```sql
-- 唯一索引（支持 INSERT IGNORE 幂等写入）
UNIQUE KEY uniq_session_seq (user_id, session_id, seq_id)
```

**涉及文件**：
- `repositories/session_repository.py` — 核心改造（INSERT IGNORE + Redis 缓存层）
- `init_db.sql` — 建表语句（含唯一索引）

---

### Phase 5：意图自纠错 ✅ 已完成

目标：verify 失败时不直接转人工，先反思意图是否识别错误，纠正后重走完整流程。

#### 5.1 新增节点：intent_reflect

**问题**：verify 判定结果为空时直接 escalate，但有可能是意图识别错误导致检索方向偏了。

**方案**：
- 新增 `node_intent_reflect` 节点，触发时机：verify 失败 且 `intent_retry_count == 0`
- LLM 对比原始问题与当前意图，判断是否存在误分类
- 意图纠正 → 清空旧槽位，回到 `slot_filling` 重走完整流程
- 意图正确 → 确认检索失败非意图问题，走 escalate
- `intent_retry_count` 计数器确保最多触发 1 次，防止死循环

**图拓扑变化（v2.0 → v2.1）**：
```
verify (失败) → intent_reflect → slot_filling（意图已纠正）
                              └→ escalate    （意图正确，确实找不到）
```

**涉及文件**：
- `nodes/intent_reflect_node.py` — 新节点实现
- `edges/routers_phase2.py` — `route_verify_result` 新增 intent_reflect 分支，新增 `route_after_reflect`
- `edges/route_slot_check.py` — 意图纠错回流时（`intent_corrected=True`）跳过 ask_user，直接走 retrieval
- `graph.py` — 注册新节点，接入条件边
- `state.py` — `AgentState` 新增 `intent_retry_count` 和 `intent_corrected` 字段
- `runner.py` — `initial_state` 初始化 `intent_retry_count=0`

**UX 设计说明**：意图纠错后回到 `slot_filling` 时，若新意图的槽位仍有缺失，不再向用户追问。原因：用户已说明需求，是系统误判了意图，不应让用户重复作答。直接用现有消息中已有信息检索，实在找不到再转人工。

#### 5.2 评估节点策略模式重构

**问题**：`node_retrieval_evaluate` 对所有数据源用同一套 LLM 评估逻辑，KB 场景不必要地调用 LLM（KB 内部已 Rerank 保障质量）。

**方案**：
- 新增 `evaluation_strategies.py`，定义三种评估策略：
  - `KBEvaluationStrategy`：规则判断（文档数 > 0 即通过）
  - `WebEvaluationStrategy`：LLM 语义评估（Web 结果质量不稳定）
  - `LocalToolsEvaluationStrategy`：结构字段校验（按 schema 判断）
- `node_retrieval_evaluate` 节点只负责选策略 + 调用，不含判断逻辑
- 新增数据源时只需在 `STRATEGY_REGISTRY` 注册

**涉及文件**：
- `nodes/evaluation_strategies.py` — 三种策略实现
- `nodes/retrieval_subgraph_nodes.py` — 节点改为调用策略，移除冗余 LLM 调用

---

## 6. 技术亮点总结

1. **确定性与智能性兼得** — 外层管道保证流程可控、可观测；检索子图让模型在受控范围内自主决策（改写 query、切换数据源）
2. **检索自纠错** — 检索子图 evaluate→rewrite 循环，最多 3 次自动重试，不再依赖硬编码兜底
3. **意图自纠错**（v2.1）— verify 失败时先反思意图是否识别错误，纠正后回 slot_filling 重走完整流程，最多触发 1 次防死循环
4. **质量把关闭环** — verify 节点让 LLM 做最终质量判断，不合格先纠错，纠错无效再转人工
5. **评估策略模式** — 不同数据源用不同评估策略（KB 规则/Web LLM/LocalTools 字段校验），新增数据源只需注册
6. **状态隔离** — 主图 `AgentState` 与子图 `RetrievalSubState` 分离，通过桥接节点映射，互不污染
7. **会话存储工业化** — MySQL 增量写入（INSERT IGNORE）+ Redis 缓存双层架构，写入代价从 O(n) 降为 O(1)，读取命中率接近 100%
