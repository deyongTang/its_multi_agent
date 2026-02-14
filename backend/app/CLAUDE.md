# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ITS 多智能体中枢（`backend/app`）— 为联想构建的智能技术服务系统的核心调度引擎。负责意图识别、任务拆解、智能体调度、外部工具调用，通过 SSE 流式响应返回结果。

与之配套的知识库平台在 `backend/knowledge`（RAG 系统，独立部署在 :8001）。设计哲学：**中枢不存知识只做决策，知识平台不碰业务只管问答**。

## Development Commands

```bash
# 启动后端（:8000）
python api/main.py

# 安装依赖
pip install -r requirements.txt

# 运行测试
cd tests && python -m pytest

# 启动前端（智能客服 UI）
cd ../../front/agent_web_ui && npm run dev
```

外部依赖：MySQL（服务站数据）、Redis（会话持久化 + 分布式锁）、知识库服务（:8001）。

## Architecture

### 请求处理流程（V2 - LangGraph）

```
POST /api/query → routers.py → MultiAgentServiceV2.process_task()
  → LangGraph Workflow (graph.py):
    intent → slot_filling ↔ ask_user (循环追问)
           → strategy_gen → dispatch:
               ├─ query_knowledge → kb_check → (miss) → search_web
               ├─ search_web
               └─ query_local_tools
           → merge_results → verify → generate_report / escalate
           → general_chat (闲聊直接结束)
  → SSE StreamingResponse
```

### 目录结构与职责

- `api/` — FastAPI 入口。`main.py` 管理生命周期（LangSmith 初始化、MCP 连接），`routers.py` 定义路由
- `multi_agent/` — 核心智能体层
  - `workflow/graph.py` — LangGraph 状态机定义，所有节点和边的编排
  - `workflow/state.py` — `AgentState` 黑板模式状态定义（意图、槽位、检索策略、文档、诊断步骤）
  - `workflow/nodes/` — 各处理节点（intent、slot_filling、strategy_gen、search、merge_verify、action）
  - `workflow/edges/` — 条件路由逻辑（route_intent、route_slot_check、route_dispatch、route_kb_check、route_verify_result）
  - `orchestrator_agent.py` / `technical_agent.py` / `service_agent.py` — 三大智能体定义
- `services/` — 业务逻辑层。`agent_service_v2.py` 是当前主入口（V1 已废弃），`session_service.py` 管理会话
- `infrastructure/` — 基础设施
  - `ai/` — LLM 客户端封装
  - `database/` — MySQL 连接池（PooledDB）
  - `tools/mcp/` — MCP 客户端（百度地图、搜索服务），`mcp_manager.py` 管理连接生命周期
  - `logging/` — 结构化日志
  - `middleware/` — TraceId 中间件
  - `observability/` — LangSmith 集成
  - `redis_client.py` / `redis_lock.py` — Redis 连接和分布式锁
- `config/settings.py` — Pydantic Settings 配置（从 `.env` 读取），必须配置至少一个 AI 服务（硅基流动或阿里百炼）
- `prompts/` — 智能体提示词文件，与代码分离便于维护
- `schemas/` — Pydantic 请求/响应模型

### LangGraph 工作流关键设计

- **状态机模式**：`AgentState`（TypedDict）作为共享黑板，节点通过更新状态字段传递信息
- **消息追加**：`messages` 字段使用 `Annotated[List, operator.add]` 确保多轮对话消息追加而非覆盖
- **显式顺序管线**：v1.4 移除了并行 fan-out，改为显式顺序 dispatch → 知识库优先 → Web 兜底
- **检查点持久化**：优先使用 `RedisSaver`，Redis 不可用时降级为 `MemorySaver`
- **槽位追问防死循环**：`ask_user_count` 字段限制追问次数

### 三大智能体边界

| 智能体 | 职责 | 工具 | 边界 |
|--------|------|------|------|
| Orchestrator | 意图识别、路由分发 | 无 | 只决策，不执行 |
| Technical Agent | 技术维修问答 | 知识库查询、Web 搜索 | 只问知识，不碰位置 |
| Service Agent | 服务站查询、导航 | MySQL、百度地图 MCP | 只查位置，不教维修 |

## API Endpoints

- `POST /api/query` — 主对话接口（SSE 流式），入参 `{query, context: {sessionId, userId}}`
- `POST /api/v2/query` — V2 对话接口（同上，两个端点当前行为一致）
- `POST /api/user_sessions` — 获取用户所有会话记忆数据

## Configuration

`.env` 文件放在 `backend/app/` 根目录，关键配置项：

- `SF_API_KEY` / `SF_BASE_URL` — 硅基流动 API（二选一必填）
- `AL_BAILIAN_API_KEY` / `AL_BAILIAN_BASE_URL` — 阿里百炼 API（二选一必填）
- `MAIN_MODEL_NAME` — 主模型（默认 `Qwen/Qwen3-32B`）
- `MYSQL_*` — MySQL 连接配置
- `REDIS_HOST` / `REDIS_PORT` — Redis 配置
- `KNOWLEDGE_BASE_URL` — 知识库服务地址（默认 `http://127.0.0.1:8001`）
- `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` — LangSmith 可观测性（可选）
- `BAIDUMAP_AK` — 百度地图 AK

配置加载优先级：环境变量 > `.env` 文件 > 默认值。启动时会校验至少配置了一个 AI 服务。

## Key Patterns

- **sys.path 操作**：`api/main.py` 启动时手动调整 `sys.path`，移除 knowledge 路径防止导入冲突，确保 app 路径优先
- **生命周期管理**：FastAPI lifespan 中初始化 LangSmith 和 MCP 连接，关闭时清理 MCP
- **SSE 流式**：所有对话接口返回 `StreamingResponse(media_type="text/event-stream")`
- **TraceId 中间件**：每个请求自动分配 trace_id，贯穿日志链路
- **中文注释**：代码库广泛使用中文注释
