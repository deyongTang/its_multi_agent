# ITS 多智能体系统架构升级计划 v2.0

> 日期: 2026-02-23 | 状态: Phase 3 进行中，Phase 4 规划中

---

## 1. 升级核心思路

**外层保持显式管道，检索环节内部引入自主循环。**

系统采用 LangGraph 显式编排管道，流程确定、可观测。在检索环节嵌入**带循环的子图**，让模型在受控范围内自主决策（改写 query、切换数据源）。验证环节作为主图中的独立节点，由 LLM 做质量把关。

```
外层管道（确定性）
  intent → slot_filling → [检索子图: 自主循环] → verify → generate_report → END
                                                    ↓ (验证失败)
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
| `ainvoke` 破坏流式 | 最终生成环节不是真流式 | `node_generate_report` 改用流式调用 | 🔲 待处理 |

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
| `route_verify_result` | `edges/routers_phase2.py` | 有文档 → generate_report，无文档 → escalate |

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

### Phase 3：验证 + 会话升级 🔧 进行中

1. ~~verify 节点引入 LLM 质量判断~~（已完成，作为主图节点实现）
2. `node_generate_report` 的 `ainvoke` → 流式调用（待处理）
3. `escalate` 对接工单系统（待处理）
4. ~~会话存储从 JSON 文件升级到 Redis/MySQL~~（已完成，见 4.5）

### Phase 4：工业级加固 📋 规划中

目标：将 Demo 级实现升级为生产可用，重点解决**可靠性、可观测性、健壮性**三大短板。

#### 4.1 LLM 输出结构化（优先级：P0）

**问题**：`evaluate` 和 `verify` 节点用 `json.loads` 解析 LLM 自由文本，生产环境下 JSON 格式错误率约 5-10%。

**方案**：
- 引入 `_safe_parse_json()` 工具函数，支持多种容错策略（正则提取、markdown 代码块剥离）
- 解析失败时返回安全默认值，而非直接 `except` 吞掉错误

**涉及文件**：
- `nodes/retrieval_subgraph_nodes.py` — `node_retrieval_evaluate`
- `nodes/merge_verify_nodes.py` — `node_verify`

#### 4.2 节点级超时 + 重试（优先级：P0）

**问题**：LLM 调用无超时保护，单次卡死会阻塞整条管道。外部服务（MCP、MySQL）同理。

**方案**：
- 实现 `async_retry_with_timeout` 装饰器：`asyncio.wait_for` 超时 + 指数退避重试（max 2 次）
- 应用到所有 LLM 调用和外部服务调用

**涉及文件**：
- 新增 `infrastructure/utils/resilience.py`
- `nodes/retrieval_subgraph_nodes.py` — search/evaluate/rewrite
- `nodes/merge_verify_nodes.py` — verify
- `nodes/action_nodes.py` — generate_report

#### 4.3 可观测性增强（优先级：P1）

**问题**：缺乏节点级耗时统计和 trace_id 贯穿，线上问题难以定位。

**方案**：
- 实现 `@node_timer` 装饰器，自动记录每个节点的执行耗时
- trace_id 从 `AgentState` 贯穿到子图日志

**涉及文件**：
- 新增 `infrastructure/utils/observability.py`
- 各节点文件（装饰器应用）

#### 4.4 generate_report 真流式（优先级：P1）

**问题**：`node_generate_report` 内部虽用 `astream`，但 LangGraph 节点返回时仍是一次性的，前端无法逐字显示。

**方案**：
- 利用 LangGraph `astream_events` 已有的事件流机制，确保 `generate_report` 的 LLM 调用事件能被 runner 捕获并透传到 SSE

**涉及文件**：
- `nodes/action_nodes.py` — `node_generate_report`
- `workflow/runner.py` — 事件过滤

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

## 6. 技术亮点总结

1. **确定性与智能性兼得** — 外层管道保证流程可控、可观测；检索子图让模型在受控范围内自主决策（改写 query、切换数据源）
2. **自我纠错能力** — 检索子图 evaluate→rewrite 循环，最多 3 次自动重试，不再依赖硬编码兜底
3. **质量把关闭环** — verify 节点让 LLM 做最终质量判断，不合格直接走 escalate 转人工
4. **状态隔离** — 主图 `AgentState` 与子图 `RetrievalSubState` 分离，通过桥接节点映射，互不污染
5. **渐进式升级** — Phase 1/2 已完成，Phase 3 进行中，每阶段独立可交付
6. **会话存储工业化** — MySQL 增量写入（INSERT IGNORE）+ Redis 缓存双层架构，写入代价从 O(n) 降为 O(1)，读取命中率接近 100%
