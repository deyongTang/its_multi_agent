# ITS 多智能体系统

> **Intelligent Technical Service** — 为联想构建的 AI 客服系统，解决两个核心问题：
> **"我的设备坏了，怎么修？"** 和 **"去哪里修？怎么去？"**

---

## 系统概览

两个独立后端，职责严格分离：

| 子系统 | 路径 | 端口 | 职责 |
|--------|------|------|------|
| **ITS 智能客服** | `backend/app` | `8000` | LangGraph 工作流引擎，意图识别、槽位填充、检索生成 |
| **ITS 知识库平台** | `backend/knowledge` | `8001` | RAG 系统，文档管理、ES 混合检索、生成式问答 |

**核心设计边界：中枢不存知识只做决策，知识平台不碰业务只管问答。**

---

## 系统架构

### 多智能体对话流程（LangGraph V2.1）

```
用户输入 → POST /api/query
  │
  ├─ SessionService — 加载多轮历史（最近 3 轮）
  │
  └─ LangGraph Workflow（graph.py）
       │
       ├─ [intent]        — L1+L2 双层意图识别（technical / location / chitchat）
       │    └─ chitchat → general_chat → END
       │
       ├─ [slot_filling]  — 槽位提取与验证
       │    └─ 缺失 → [ask_user]（追问，ask_user_count 防死循环）
       │
       ├─ [retrieval]     — 检索子图（自主循环，最多 3 次）
       │    └─ dispatch → search → evaluate → rewrite → search...
       │
       ├─ [verify]        — 验证结果充分性
       │    ├─ 通过           → [generate_report] → END
       │    ├─ 失败 & 首次    → [intent_reflect]（意图自纠错，V2.1 新增）
       │    │                      └─ 纠正意图 → 回到 slot_filling（最多 1 次）
       │    └─ 失败 & 已纠错  → [escalate] → END
       │
       └─ SSE 流式输出给前端
```

**意图自纠错机制**：verify 阶段若发现答案质量差，系统会反思"是不是意图识别错了"，自动纠正后重走 slot_filling 流程，消除"意图错误 → 虚假答案"的恶性循环。最多纠错 1 次（`intent_retry_count` 防死循环）。

### 知识库检索流程（RAG V2.0 — N+1 存储 + 混合检索）

```
文档入库（N+1 存储）:
  原文 → TextProcessor 切片 → EmbeddingService 向量化 → jieba 分词
       → ES Bulk 写入:
            ├─ 1 个 Parent（doc_type=parent，保存 full_content）
            └─ N 个 Chunks（doc_type=chunk，保存 content + content_vector）

知识检索（混合检索）:
  用户问题
    ├─ Path 1: BM25 关键词检索（ES multi_match）
    └─ Path 2: KNN 向量检索（ES native HNSW）
    ↓
  RRF 融合（k=60）— 合并两路，按文档折叠
    ↓
  [可选] Cross-Encoder Rerank（硅基流动 bge-reranker-v2-m3）
    ↓
  回填 Parent 文档（保证上下文完整性）
    ↓
  LLM 流式生成答案
```

---

## 技术栈

### 后端

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 高性能异步服务 |
| 工作流引擎 | **LangGraph ≥ 0.2** | 多智能体状态机编排 |
| RAG 框架 | LangChain ≥ 0.3 | 向量化、提示词链 |
| 向量检索 | **Elasticsearch 8.12** | KNN（HNSW）+ BM25 混合检索 |
| Embedding | 阿里百炼 API | text-embedding-v3 |
| Reranker | 硅基流动 API | bge-reranker-v2-m3（Feature Flag 控制） |
| LLM | 阿里百炼 / 硅基流动 | OpenAI 兼容接口，默认 Qwen3-32B |
| 关系数据库 | MySQL 8.0+ | 服务站数据、用户信息、会话历史 |
| 缓存 / 锁 | Redis 5.0+ | 会话热缓存（TTL 24h）、分布式写锁 |
| 对象存储 | MinIO | 文档备份、爬虫产物 |
| 中文处理 | jieba | 分词、关键词提取 |
| 可观测性 | LangSmith | LLM 调用链路追踪（可选） |
| 外部服务 | MCP 协议 | 百度地图、Web 搜索 |

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 + Vite | 组件化开发，智能客服 UI（`front/agent_web_ui`） |
| Vue 3 + Vite + Vue Router | 知识库管理 UI（`front/knowlege_platform_ui`） |
| Element Plus | UI 组件库 |
| Axios | HTTP 请求（知识库 UI） |
| fetch + ReadableStream | SSE 流式响应处理（智能客服 UI） |
| marked | Markdown 渲染 |

---

## 项目结构

```
its_multi_agent/
├── backend/
│   ├── app/                           # 多智能体中枢（:8000）
│   │   ├── api/                       # FastAPI 入口（main.py + routers.py）
│   │   ├── multi_agent/               # 核心工作流
│   │   │   └── workflow/
│   │   │       ├── graph.py           # 主工作流状态机
│   │   │       ├── state.py           # AgentState 黑板模式定义
│   │   │       ├── retrieval_subgraph.py  # 检索子图（自主循环）
│   │   │       ├── nodes/             # 12 个工作流节点
│   │   │       └── edges/             # 条件路由逻辑
│   │   ├── services/                  # 业务逻辑（agent_service_v2.py 为主入口）
│   │   ├── infrastructure/            # AI 客户端、MySQL、Redis、MCP、日志
│   │   ├── repositories/              # 数据访问（会话存储）
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── prompts/                   # 智能体提示词（与代码分离）
│   │   └── config/settings.py         # Pydantic Settings 配置
│   │
│   └── knowledge/                     # 知识库平台（:8001）
│       ├── api/                       # FastAPI 入口
│       ├── services/                  # 核心服务
│       │   ├── es_retrieval_service.py    # 混合检索（KNN + BM25 + RRF）
│       │   ├── es_ingestion_processor.py  # N+1 入库处理器
│       │   ├── embedding_service.py       # 向量化服务
│       │   ├── reranker_service.py        # Reranker 重排服务
│       │   ├── text_processor.py          # 文本切分
│       │   └── crawler/                   # 联想知识库爬虫
│       ├── business_logic/            # 业务逻辑（Worker、同步、查询）
│       ├── infrastructure/            # ES 客户端、MinIO、JWT 认证
│       ├── repositories/              # 数据访问层
│       ├── cli/                       # CLI 工具（爬虫、批量入库）
│       ├── docs/                      # 架构设计文档
│       └── config/settings.py         # 配置
│
├── front/
│   ├── agent_web_ui/                  # 智能客服前端
│   └── knowlege_platform_ui/          # 知识库管理前端
│
└── deploy/                            # Nginx 配置、部署脚本、SQL 初始化
```

---

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 5.0+
- Elasticsearch 8.12
- MinIO（知识库平台需要）
- 阿里百炼 API Key **或** 硅基流动 API Key（至少一个）

### 1. 启动知识库平台（:8001）

```bash
cd backend/knowledge
cp .env.example .env    # 填写 ES、MinIO、AI 服务配置
pip install -r requirements.txt
python api/main.py
```

### 2. 启动多智能体中枢（:8000）

> 依赖知识库平台已启动

```bash
cd backend/app
cp .env.example .env    # 填写 AI 服务、MySQL、Redis、百度地图配置
pip install -r requirements.txt
python api/main.py
```

### 3. 启动前端

```bash
# 智能客服 UI
cd front/agent_web_ui
npm install && npm run dev

# 知识库管理 UI
cd front/knowlege_platform_ui
npm install && npm run dev
```

---

## 配置说明

### 多智能体中枢（backend/app/.env）

```env
# AI 服务（二选一必填）
SF_API_KEY=...
SF_BASE_URL=https://api.siliconflow.cn/v1
# AL_BAILIAN_API_KEY=...
# AL_BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

MAIN_MODEL_NAME=Qwen/Qwen3-32B     # 主模型

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=...
MYSQL_DATABASE=its_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 外部服务
KNOWLEDGE_BASE_URL=http://127.0.0.1:8001
BAIDUMAP_AK=...

# 可观测性（可选）
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=...
```

### 知识库平台（backend/knowledge/.env）

```env
# AI 服务
AL_BAILIAN_API_KEY=...             # Embedding + LLM
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v3

# Elasticsearch
ES_HOST=localhost
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=...
ES_INDEX_NAME=knowledge

# MinIO
MINIO_ENDPOINT=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...

# Reranker（可选，Feature Flag 控制）
RERANKER_ENABLED=false
SILICONFLOW_API_KEY=...
RERANKER_MODEL=BAAI/bge-reranker-v2-m3

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=...
DB_NAME=its_knowledge
```

---

## API 接口

### 多智能体中枢（:8000）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/query` | POST | 主对话接口，SSE 流式响应 |
| `/api/v2/query` | POST | V2 对话接口（行为同上） |
| `/api/user_sessions` | POST | 获取用户所有会话记忆 |

**请求示例：**

```json
{
  "query": "K900 蓝屏怎么修",
  "context": {
    "user_id": "user_123",
    "session_id": "sess_456"
  }
}
```

### 知识库平台（:8001）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/upload_es` | POST | 上传文档并入库 ES（N+1 模式） |
| `/retrieve` | POST | 纯检索（不经过 LLM） |
| `/query` | POST | 混合检索 + LLM 流式生成（SSE） |
| `/query_sync` | POST | 混合检索 + LLM 同步生成 |
| `/tasks/crawl` | POST | 触发后台爬虫任务 |
| `/tasks/ingest` | POST | 触发后台入库任务（处理队列中的新文档） |
| `/es` | GET | 测试 ES 连接状态 |

---

## CLI 工具

```bash
cd backend/knowledge

# 批量上传本地文档到知识库
python cli/upload_cli.py

# 爬取联想官方知识库（指定文章 ID 范围）
python cli/crawl_cli.py --start 1 --end 1000 --delay 0.2
```

---

## 部署

### Nginx 反向代理

知识库平台前端构建后通过 Nginx 代理到后端服务：

```bash
cd deploy
chmod +x build.sh && ./build.sh    # 构建前端产物
# 将 dist/ 上传到服务器
# 按 deploy/nginx.conf 配置 Nginx 代理到 localhost:8001
```

### Docker 部署知识库平台

```bash
cd backend/knowledge
cp .env.example .env
./deploy.sh
```

详细步骤参考 `deploy/README.md`。

---

## 开发文档

详细设计文档位于 `backend/app/docs/` 和 `backend/knowledge/docs/`：

| 文档 | 说明 |
|------|------|
| `backend/app/docs/architecture/` | 分层架构、工作流引擎、意图设计、Agent 设计模式 |
| `backend/app/docs/guides/` | 启动流程、工具与 MCP 使用、会话持久化、新人入门 |
| `backend/knowledge/docs/Roadmap.md` | 系统演进路线图（当前 V3.2，规划至 V4.0） |
| `backend/knowledge/docs/Current_ES_Chunking_Flow.md` | ES 切片入库流程详解 |
| `backend/knowledge/docs/RAG_Design_Philosophy.md` | RAG 设计哲学 |
| `backend/knowledge/docs/V3.3_升级设计方案.md` | Native KNN + Reranker 升级方案 |

---

## 版本路线图

| 版本 | 重点特性 | 状态 |
|------|---------|------|
| **V3.2（当前）** | N+1 存储、RRF 混合检索、LangGraph 意图自纠错 | ✅ 已上线 |
| **V3.3** | Native KNN、Cross-Encoder 精排、动态阈值 | 📅 规划中 |
| **V3.4** | 多模态基础（MinIO 图片、VLM 描述） | 📅 规划中 |
| **V4.0** | 智能爬虫、Agentic Retrieval | 📅 远期 |

---

## License

本项目为联想 ITS 内部项目，仅用于学习和演示目的。
