# ITS Multi-Agent Knowledge System

## Project Overview

This project is the backend for the ITS Multi-Agent Knowledge System. It is designed to implement a Retrieval-Augmented Generation (RAG) pipeline. The system crawls knowledge base articles, stores them in an Object Storage Service (OSS, specifically MinIO), and indexes them into Elasticsearch and ChromaDB for hybrid retrieval.

### Key Technologies
*   **Framework:** FastAPI (Python 3.10+)
*   **Orchestration:** LangChain
*   **Vector Store:** ChromaDB (Local), Elasticsearch (Hybrid Search)
*   **Object Storage:** MinIO
*   **Database:** MySQL (Metadata & Sync Status)
*   **NLP:** Jieba (Chinese Segmentation), OpenAI/LangChain Embeddings

### Architecture

The system follows a two-pipeline architecture:

1.  **Ingestion Pipeline (Crawler -> OSS):**
    *   Crawls content from Lenovo Knowledge Base.
    *   Parses HTML to Markdown.
    *   Uploads raw Markdown to MinIO (OSS).
    *   Registers metadata in MySQL (`knowledge_asset` table).

2.  **Indexing Pipeline (OSS -> Vector Store):**
    *   **Ingestion Worker** polls MySQL for new content.
    *   Downloads content from MinIO.
    *   Chunks and embeds text (using OpenAI/DashScope models).
    *   Indexes vectors into ChromaDB and/or Elasticsearch.

## Setup & Configuration

### Prerequisites
*   Python 3.10+
*   MySQL Server
*   MinIO Server
*   Elasticsearch 8.12.0
*   OpenAI Compatible API Key

### Environment Variables
Create a `.env` file in the root directory based on `config/settings.py`. Key variables include:

```env
API_KEY=your_openai_api_key
BASE_URL=your_openai_base_url
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
MINIO_ENDPOINT=localhost:9000
ES_HOST=localhost
```

### Installation
```bash
pip install -r requirements.txt
```

### Database Initialization
Initialize the MySQL database and tables:
```bash
python scripts/init_db.py
```

## Running the Application

### 1. Start the API Server
The FastAPI application serves the knowledge retrieval API.
```bash
python api/main.py
# Runs on http://127.0.0.1:8001 by default
```
Or via uvicorn directly:
```bash
uvicorn api.main:create_fast_api --factory --host 0.0.0.0 --port 8001
```

### 2. CLI Tools

**Crawler CLI:**
Manually triggers the crawler for a range of knowledge IDs.
```bash
python cli/crawl_cli.py
```

**Upload CLI:**
Batch uploads local markdown files to the vector store.
```bash
python cli/upload_cli.py
```

**Ingestion Worker CLI:**
Runs the worker process to sync data from MinIO to Elasticsearch.
```bash
# Run once
python cli/worker_cli.py

# Run in daemon mode (loop)
python cli/worker_cli.py --loop --interval 10
```

## Directory Structure

*   `api/`: FastAPI application entry point and routers.
*   `business_logic/`: Core service logic (Crawler, Sync, Query).
*   `cli/`: Command-line interface scripts for maintenance tasks.
*   `config/`: Configuration management (pydantic settings).
*   `data/`: Local data storage (crawled files, OSS simulation).
*   `docs/`: Architecture design documents.
*   `infrastructure/`: Low-level infrastructure code (DB, Logger, ES Client).
*   `migrations/`: SQL migration scripts.
*   `repositories/`: Data access layer.
*   `scripts/`: Initialization and utility scripts.
*   `services/`: Service implementations (Embedding, Retrieval).
