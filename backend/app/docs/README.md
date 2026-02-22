# ITS 多智能体中枢 — 项目文档索引

## 架构设计 (`architecture/`)

| 文档 | 说明 |
| :--- | :--- |
| [detailed-design.md](architecture/detailed-design.md) | 工业级 ITS 智能运维编排引擎详细设计（分层架构、FSM 引擎、安全合规、可观测性） |
| [workflow-engine.md](architecture/workflow-engine.md) | LangGraph 工作流引擎技术方案（v1.5），含节点/边定义、状态流转拓扑图 |
| [intent-design.md](architecture/intent-design.md) | 多智能体角色定义与二级意图体系设计（L1/L2 意图映射、路由逻辑） |
| [upgrade-plan.md](architecture/upgrade-plan.md) | 从 Demo 级原型向工业级分层系统的演进规划（Phase 1-3 路线图） |
| [agent-design-pattern.md](architecture/agent-design-pattern.md) | Agent 设计模式：自适应策略 vs 显式编排的选型决策 + Agent-as-Tool 适配器模式 |

## 使用指南 (`guides/`)

| 文档 | 说明 |
| :--- | :--- |
| [system-overview.md](guides/system-overview.md) | 系统业务介绍（定位、两大子系统、业务场景、架构哲学） |
| [startup.md](guides/startup.md) | 系统完整启动流程详解（6 个阶段、常见问题排查、启动优化建议） |
| [tools-and-mcp.md](guides/tools-and-mcp.md) | Tools 与 MCP 使用指南（核心概念、对比分析、决策树、实战案例） |
| [session-persistence.md](guides/session-persistence.md) | 会话持久化架构设计与部署指南（双层存储、Redis 分布式锁、部署步骤） |
| [study-guide.md](guides/study-guide.md) | 项目学习与调试指南（静态代码分析 → 动态调试的学习路径） |

## 开发日志 (`devlog/`)

| 文档 | 说明 |
| :--- | :--- |
| [langsmith-tracing.md](devlog/langsmith-tracing.md) | LangSmith 追踪问题完整复盘 + 追踪标识优化方案 |
| [langgraph-state-conflict.md](devlog/langgraph-state-conflict.md) | LangGraph 并行节点状态冲突问题（Annotated + Reducer 解决方案） |
| [intent-optimization.md](devlog/intent-optimization.md) | 意图识别性能优化（单次 LLM 调用完成多层识别，延迟降低 41%，成本降低 50%） |
| [misc.md](devlog/misc.md) | 杂项修复记录（知识库服务 401、JSON 解析失败等） |

## 总结报告 (`reports/`)

| 文档 | 说明 |
| :--- | :--- |
| [langgraph-phase1.md](reports/langgraph-phase1.md) | LangGraph 重构 Phase 1 完成总结（核心功能、技术亮点、验收标准） |
| [industrial-upgrade.md](reports/industrial-upgrade.md) | 从 Demo 到工业级核心竞争力升级报告（FSM 编排、韧性架构、全链路可观测性） |

---

**建议阅读顺序**（新人入门）：
1. `guides/study-guide.md` → 了解项目全貌
2. `guides/startup.md` → 跑起来
3. `architecture/detailed-design.md` → 理解架构
4. `architecture/agent-design-pattern.md` → 理解设计决策
5. `guides/tools-and-mcp.md` → 理解工具体系
