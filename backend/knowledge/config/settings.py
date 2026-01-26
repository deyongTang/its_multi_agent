from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    API_KEY: str = Field(default="")
    BASE_URL: str = Field(default="")
    MODEL: str = Field(default="gpt-3.5-turbo")
    EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002")

    # 数据库配置
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_USER: str = Field(default="root")
    DB_PASSWORD: str = Field(default="")
    DB_NAME: str = Field(default="its_knowledge")

    # knowledge/config
    KNOWLEDGE_BASE_URL: str = Field(default="http://localhost:8000")

    _current_dir = os.path.dirname(os.path.abspath(__file__))
    # knowledge
    _project_root = os.path.dirname(_current_dir)
    
    VECTOR_STORE_PATH: str = os.path.join(_project_root, "chroma_kb")

    # 文件存储配置
    OSS_STORAGE_PATH: str = os.path.join(_project_root, "data", "oss")
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = Field(default="118.195.198.38:9000")
    MINIO_ACCESS_KEY: str = Field(default="its_appkey")
    MINIO_SECRET_KEY: str = Field(default="its_secret123")
    MINIO_BUCKET: str = Field(default="knowledge-base")
    MINIO_SECURE: bool = Field(default=False)  # True for HTTPS, False for HTTP

    # Default directories
    CRAWL_OUTPUT_DIR: str = os.path.join(_project_root, "data", "crawl")
    # Using 'data/crawl' as the default location for markdown files
    MD_FOLDER_PATH: str = CRAWL_OUTPUT_DIR
    
    # Text splitting configuration
    CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 200

    # Retrieval configuration
    TOP_ROUGH: int = 50
    TOP_FINAL: int = 5

    # Elasticsearch 配置
    ES_HOST: str = Field(default="118.195.198.38")
    ES_PORT: int = Field(default=9200)
    ES_SCHEME: str = Field(default="http")
    ES_USERNAME: str = Field(default="elastic")
    ES_PASSWORD: str = Field(default="RrnmPnSkNFm0AiNmJiIp")
    ES_INDEX_NAME: str = Field(default="")
    ES_VECTOR_DIMS: int = Field(default=1024)  # 1024 dimensions

    # Worker 配置
    WORKER_BATCH_SIZE: int = 10
    WORKER_MAX_RETRY: int = 3
    WORKER_INTERVAL_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=os.path.join(_project_root, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# 必须要实例化
settings = Settings()
