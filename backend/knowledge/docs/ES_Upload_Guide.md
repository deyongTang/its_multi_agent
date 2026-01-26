# Elasticsearch 文档上传功能使用说明

## 概述

本功能实现了基于 RAG V2 架构设计的文档上传到 Elasticsearch 的完整流程，采用 **N+1 存储模式**：
- **N 个切片 (Chunks)**: 用于搜索，包含向量和分词后的文本
- **1 个全文 (Parent)**: 用于展示，存储完整文档内容

## 架构特点

### 1. N+1 存储模式
- **Chunks**: 切分后的文本片段，经过向量化和中文分词，用于高效检索
- **Parent**: 完整文档，不参与搜索，仅用于返回完整上下文给 LLM

### 2. 核心组件

#### 服务层
- `services/embedding_service.py` - 文本向量化服务
- `services/text_processor.py` - 文本切分和中文分词
- `services/es_ingestion_processor.py` - ES 入库处理器

#### 基础设施层
- `infrastructure/es_client.py` - ES 客户端封装

#### API 层
- `api/routers.py` - 新增 `/upload_es` 接口

## 快速开始

### 步骤 1: 初始化 Elasticsearch 索引

```bash
cd backend/knowledge
python scripts/init_es_index.py
```

如果需要强制重建索引：
```bash
python scripts/init_es_index.py --force
```

### 步骤 2: 启动后端服务

```bash
cd backend/knowledge
python api/main.py
```

服务将运行在 `http://127.0.0.1:8001`

### 步骤 3: 上传文档

使用 curl 测试：
```bash
curl -X POST "http://127.0.0.1:8001/upload_es" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.md"
```

或使用 Python requests：
```python
import requests

url = "http://127.0.0.1:8001/upload_es"
files = {"file": open("document.md", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## 配置说明

在 `config/settings.py` 中配置以下参数：

```python
# Elasticsearch 配置
ES_HOST = "118.195.198.38"
ES_PORT = 9200
ES_SCHEME = "http"
ES_USERNAME = "elastic"
ES_PASSWORD = "your_password"
ES_INDEX_NAME = "its_knowledge_index"
ES_VECTOR_DIMS = 1536  # text-embedding-3-small 维度

# 文本切分配置
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 200

# OpenAI API 配置
API_KEY = "your_api_key"
BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"
```

## 数据流程详解

### 入库流程 (Write Path)

```
文件上传
  ↓
1. 保存临时文件
  ↓
2. 读取文件内容
  ↓
3. 生成 knowledge_no (MD5 hash)
  ↓
4. 文本切分 (RecursiveCharacterTextSplitter)
  ↓
5. 批量向量化 (OpenAI Embeddings)
  ↓
6. 中文分词 (jieba)
  ↓
7. 构造 ES 文档
   - 1 个 Parent 文档 (全文)
   - N 个 Chunk 文档 (切片 + 向量)
  ↓
8. 批量写入 ES (Bulk API)
  ↓
9. 返回结果
```

### ES 文档结构

#### Parent 文档 (全文存储)
```json
{
  "doc_id": "{knowledge_no}_parent",
  "knowledge_no": "abc123...",
  "doc_type": "parent",
  "title": "文档标题",
  "full_content": "完整文档内容...",
  "file_path": "/path/to/file.md",
  "created_at": "2026-01-23T10:00:00"
}
```

#### Chunk 文档 (用于搜索)
```json
{
  "doc_id": "{knowledge_no}_chunk_0",
  "knowledge_no": "abc123...",
  "doc_type": "chunk",
  "title": "文档 标题",
  "content": "这是 一个 测试 文档",
  "content_vector": [0.123, -0.456, ...],
  "chunk_index": 0,
  "file_path": "/path/to/file.md",
  "created_at": "2026-01-23T10:00:00"
}
```

## API 接口说明

### POST /upload_es

上传文档到 Elasticsearch

**请求参数:**
- `file`: 文件对象 (multipart/form-data)

**响应示例:**

```json
{
  "status": "success",
  "message": "文档已成功上传到 Elasticsearch",
  "file_name": "test_document.md",
  "chunks_added": 5
}
```

**说明:**
- `chunks_added`: 包含 N 个 chunks + 1 个 parent 的总数

## 技术特点

### 1. 中文分词 (Client-Side Tokenization)

使用 jieba 在 Python 端进行分词，降低 ES 运维复杂度：

```python
# 原文: "这是一个测试文档"
# 分词后: "这是 一个 测试 文档"
```

### 2. 智能文本切分

- 优先在语义边界切分（段落、句子）
- 支持重叠（默认 200 字符）
- 小于 chunk_size 的文档不切分

### 3. 批量向量化

- 批次大小: 32
- 自动重试机制
- 进度日志输出

### 4. 原子写入

使用 ES Bulk API 一次性写入所有文档，确保数据一致性。

## 故障排查

### 问题 1: ES 连接失败

**错误信息:**
```
❌ ES 连接失败: ConnectionError
```

**解决方案:**
1. 检查 ES 服务是否运行
2. 验证 `ES_HOST` 和 `ES_PORT` 配置
3. 检查网络连接和防火墙设置

### 问题 2: 向量化失败

**错误信息:**
```
❌ 文本向量化失败: API key invalid
```

**解决方案:**
1. 检查 `API_KEY` 是否正确
2. 验证 `BASE_URL` 是否可访问
3. 确认 API 配额是否充足

### 问题 3: 索引不存在

**错误信息:**
```
❌ 索引 its_knowledge_index 不存在
```

**解决方案:**

```bash
python scripts/init_es_index.py
```

## 性能优化建议

### 1. 批量上传

对于大量文档，建议编写批量上传脚本：

```python
import os
import requests

def batch_upload(folder_path):
    url = "http://127.0.0.1:8001/upload_es"
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'rb') as f:
                files = {"file": f}
                response = requests.post(url, files=files)
                print(f"✅ {filename}: {response.json()}")

batch_upload("./data/documents")
```

### 2. 调整切分参数

根据文档特点调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP`：

- **短文档** (< 1000 字): `CHUNK_SIZE=3000`, `CHUNK_OVERLAP=0`
- **长文档** (> 5000 字): `CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`

### 3. 向量维度选择

根据精度和性能需求选择 Embedding 模型：

- `text-embedding-3-small` (1536 维): 平衡性能和精度
- `text-embedding-3-large` (3072 维): 更高精度，更大存储

## 下一步计划

根据 RAG V2 架构设计，后续需要实现：

1. **混合检索接口** - 结合向量检索和关键词检索
2. **Collapse 折叠** - 按 knowledge_no 去重
3. **动态截断** - 根据分数梯度智能截断结果
4. **多模态支持** - 图片内容语义化处理

## 参考文档

- [RAG_V2_Architecture_Design.md](RAG_V2_Architecture_Design.md) - 完整架构设计文档
- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
