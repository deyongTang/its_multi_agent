# ITS 多智能体系统

> **Intelligent Technical Service** — 为联想构建的 AI 客服系统，核心解决两个问题：
> **"我的设备坏了，怎么修？"** 和 **"去哪里修？怎么去？"**

---

## 项目简介

ITS 多智能体系统包含两个核心子系统，通过 **双引擎 + 职责分离** 架构协同工作：

| 子系统 | 路径 | 端口 | 职责 |
|--------|------|------|------|
| **ITS 智能客服** | `backend/app` | `8000` | 多智能体中枢，意图识别、任务调度、流式对话 |
| **ITS 知识库平台** | `backend/knowledge` | `8001` | RAG 系统，文档入库、语义检索、生成式问答 |

**核心原则：** 中枢不存知识只做决策，知识平台不碰业务只管问答。

---

## 系统架构

```
用户
 ↓
多智能体中枢（backend/app）
 ├─ 调度智能体 (Orchestrator)   → 识别意图，分发任务
 ├─ 技术顾问智能体               → 调知识库/搜索，回答"怎么修"
 └─ 全能业务智能体               → 查数据库/地图，回答"去哪修"
          ↓
知识库平台（backend/knowledge）
 └─ ChromaDB 向量库 + RAG 生成
```

### 三大智能体角色

| 智能体 | 文件 | 职责 | 工具 |
|--------|------|------|------|
| **调度智能体** | `core_agents/orchestrator.py` | 门房/总指挥：意图识别、路由分发 | — |
| **技术顾问** | `core_agents/technical_agent.py` | IT 维修专家：故障诊断、操作指南 | 知识库 API、Web 搜索 MCP |
| **全能业务助手** | `core_agents/comprehensive_service_agent.py` | 生活服务：服务站查询、导航 | MySQL、百度地图 MCP |

### 请求处理流程

```
前端请求 → routes.py → AgentService → SessionManager（历史）
  → Orchestrator（意图识别）
  → Handoff → TechnicalAgent / ComprehensiveAgent
  → 工具调用（知识库 / 地图 / 数据库）
  → SSE 流式输出给前端
```

---

## 技术栈

### 后端

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 多智能体编排 | OpenAI Agents SDK（Swarm 模式）|
| RAG 框架 | LangChain（langchain-core / community / openai / chroma）|
| 向量数据库 | ChromaDB（本地持久化）|
| 关系型数据库 | MySQL + pymysql + dbutils 连接池 |
| 外部服务集成 | MCP（百度地图、阿里百炼搜索）|
| LLM / Embedding | OpenAI API（兼容阿里百炼等）|
| 中文处理 | jieba 分词 |

### 前端

| 子系统 | 技术 |
|--------|------|
| ITS 智能客服 | Vue 3 + Vite + Element Plus + SSE 流式渲染 |
| 知识库平台 | Vue 3 + Vite + Element Plus + Axios + Vue Router |

---

## 项目结构

```
its_multi_agent/
├── backend/
│   ├── app/                        # ITS 智能客服后端（多智能体中枢）
│   │   ├── presentation/api/       # API 路由和数据模型
│   │   ├── application/            # 核心业务：AgentService、SessionManager、StreamProcessor
│   │   ├── core_agents/            # 三大智能体：Orchestrator、TechnicalAgent、ComprehensiveAgent
│   │   ├── infrastructure/         # 数据库、MCP 客户端、工具函数
│   │   ├── prompts/                # 智能体提示词（独立文件，便于维护）
│   │   └── docs/                   # 架构设计文档
│   │
│   └── knowledge/                  # ITS 知识库平台后端（RAG 系统）
│       ├── presentation/           # API 接口 + CLI 工具（爬虫、批量上传）
│       ├── business_logic/         # 文档处理、检索服务、生成服务
│       ├── data_access/            # ChromaDB 操作、文件读写、知识库 API 客户端
│       ├── config/                 # 环境配置和系统常量
│       └── chroma_kb/              # ChromaDB 持久化存储
│
├── front/
│   ├── its_front/                  # ITS 智能客服前端
│   └── knowlege_platform_ui/       # 知识库平台前端
│
└── deploy/                         # 部署脚本和 Nginx 配置
```

---

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+（用于服务站数据）
- OpenAI API Key（或兼容接口，如阿里百炼）

### 1. 启动 ITS 智能客服系统

**配置环境变量：**

```bash
cd backend/app
cp .env.example .env   # 按需修改
```

`.env` 示例：

```env
API_KEY=your_openai_api_key
BASE_URL=https://api.openai.com/v1
MODEL=gpt-4

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=its_service_stations

MCP_BAIDU_MAP_SERVER=path_to_baidu_map_mcp_server
MCP_SEARCH_SERVER=path_to_search_mcp_server
```

**安装依赖并启动后端：**

```bash
cd backend/app
pip install -r requirements.txt
python presentation/api/main.py
# 服务运行在 http://127.0.0.1:8000
```

**启动前端：**

```bash
cd front/its_front
npm install
npm run dev
```

---

### 2. 启动 ITS 知识库平台

**配置环境变量：**

```bash
cd backend/knowledge
cp .env.example .env   # 按需修改
```

`.env` 示例：

```env
API_KEY=your_openai_api_key
BASE_URL=https://api.openai.com/v1
MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

VECTOR_STORE_PATH=./chroma_kb
CHUNK_SIZE=3000
CHUNK_OVERLAP=200
TOP_ROUGH=50
TOP_FINAL=5
```

**安装依赖并启动后端：**

```bash
cd backend/knowledge
pip install -r requirements.txt
python presentation/api/main.py
# 服务运行在 http://127.0.0.1:8001
```

**启动前端：**

```bash
cd front/knowlege_platform_ui
npm install
npm run dev
```

---

## API 接口

### ITS 智能客服（端口 8000）

```
POST /api/query
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string | 用户问题 |
| `context.sessionId` | string | 会话 ID |
| `context.userId` | string | 用户 ID |

返回 SSE 流式响应，实时推送智能体思考过程和最终答案。

---

### ITS 知识库平台（端口 8001）

```
POST /upload        # 上传文档并向量化入库
POST /query         # 语义检索 + LLM 生成回答
```

**上传接口** — `multipart/form-data`：

```json
{ "status": "ok", "message": "...", "file_name": "xxx.md", "chunks_added": 3 }
```

**查询接口** — 请求体 `{"question": "..."}` → 返回 `{"answer": "..."}`

---

## CLI 工具

```bash
# 批量上传文档到知识库
cd backend/knowledge
python presentation/cli/upload_cli.py

# 爬取联想官方知识库（指定文章范围）
python presentation/cli/crawl_cli.py --start 1 --end 1000 --out ./data/raw --delay 0.2
```

---

## 文档索引

详细设计文档位于 `backend/app/docs/`：

| 文档 | 说明 |
|------|------|
| `architecture/detailed-design.md` | 分层架构、FSM 引擎、安全合规、可观测性 |
| `architecture/workflow-engine.md` | LangGraph 工作流引擎方案 |
| `architecture/intent-design.md` | 多智能体角色与二级意图体系 |
| `architecture/agent-design-pattern.md` | Agent 设计模式选型决策 |
| `guides/startup.md` | 系统完整启动流程与常见问题 |
| `guides/tools-and-mcp.md` | Tools 与 MCP 使用指南 |
| `guides/session-persistence.md` | 会话持久化架构设计 |
| `guides/study-guide.md` | 新人入门学习路径 |

**建议阅读顺序（新人入门）：**

1. `guides/study-guide.md` — 了解项目全貌
2. `guides/startup.md` — 跑起来
3. `architecture/detailed-design.md` — 理解架构
4. `architecture/agent-design-pattern.md` — 理解设计决策
5. `guides/tools-and-mcp.md` — 理解工具体系

---

## 部署

### Docker 部署知识库平台

```bash
cd backend/knowledge
cp .env.example .env   # 配置环境变量
./deploy.sh            # 一键部署
```

### Nginx 部署前端

```bash
cd deploy
chmod +x build.sh
./build.sh             # 构建前端产物

# 将 dist/ 上传到服务器并配置 Nginx 代理到 localhost:8001
```

详细部署步骤参考 `deploy/README.md`。

---

## License

本项目为联想 ITS 内部项目，仅用于学习和演示目的。
