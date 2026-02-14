# ITS 项目审计与演进总结报告 (2026-01-31)

## 1. 核心结论 (Executive Summary)
经过对项目的深度代码审计与架构评估，我们确认：
*   **后端知识库 (Knowledge)**: 处于 **准工业级** 状态。核心 ETL 逻辑扎实，足以支撑 T+1 离线增量更新场景。当前的主要任务是清理技术债（移除 Chroma）和优化索引（HNSW）。
*   **智能体系统 (Agent)**: 处于 **高级 Demo** 状态。存在架构分裂（LangGraph vs Agents SDK）和逻辑线性化问题。这是下一阶段开发的**绝对重心**。

## 2. 问题盘点 (Issues Inventory)

### 2.1 智能体 (Agent) - [Critical]
1.  **架构分裂**: 项目中存在两套 Agent 实现 (`orchestrator_agent.py` 使用 `agents` SDK，而 `graph.py` 使用 `langgraph`)。必须废弃前者，统一至 LangGraph。
2.  **伪智能体**: 当前逻辑主要是线性的函数调用 (`DAG`)，缺乏真正的 Agent 特性（如反思、自我纠错、分层协作）。
3.  **状态管理薄弱**: `AgentState` 过于扁平，无法支持复杂的长程任务。

### 2.2 知识库 (Knowledge) - [Major]
1.  **技术债 (Legacy Debt)**: 代码库中残留了早期的 Chroma 向量库代码 (`VectorStoreRepository`)，但实际上使用的是 ES。这导致了架构认知的混乱，必须清理。
2.  **入口简陋**: 爬虫入口 `crawler_service.crawl_range` 缺乏业务语义（如按时间、分类过滤）和自动化游标管理，无法满足自动化运维需求。
3.  **潜在性能瓶颈**: 向量检索目前使用 `script_score` (O(N))，在数据量增长后会成为查询瓶颈。

## 3. 演进路线图 (Evolution Roadmap)

### 阶段一：Agent 架构重塑 (立即启动)
*   **目标**: 解决“伪智能体”问题，建立 Supervisor-Worker 分层架构。
*   **依据**: `ARCHITECTURE_UPGRADE_PLAN.md` (Phase 1)
*   **动作**:
    1.  创建 `new_architecture` 目录。
    2.  定义 `GlobalState` 和 `SubAgentState`。
    3.  实现 Supervisor 路由骨架，废弃旧的 `orchestrator_agent.py`。

### 阶段二：Knowledge 扫除与优化 (穿插进行)
*   **目标**: 清理技术债，确保存储架构一致性。
*   **依据**: `KNOWLEDGE_OPTIMIZATION_PLAN.md`
*   **动作**:
    1.  **P0**: 删除 Chroma 相关代码与依赖。
    2.  **P0**: 将 ES 向量索引升级为 HNSW。

### 阶段三：爬虫策略升级 (后续规划)
*   **目标**: 实现全自动、智能化的数据摄入。
*   **动作**: 设计并实现基于 `SyncCursor` 和业务过滤器的任务策略模块 (Task Strategy)。

## 4. 决策留痕 (Decision Log)
*   **2026-01-31**: 确认 Knowledge 爬虫为 T+1 离线任务，**暂缓** 分布式 Worker 和 异步 I/O 的改造计划。当前单机同步架构满足需求。
*   **2026-01-31**: 确认弃用 `orchestrator_agent.py` 中的 `agents` SDK 实现，全面转向 **LangGraph** 技术栈。
*   **2026-01-31**: 确认 **Elasticsearch** 为唯一向量存储后端，废弃 Chroma。

---
*本报告由系统自动生成，作为后续开发的纲领性文件。*
