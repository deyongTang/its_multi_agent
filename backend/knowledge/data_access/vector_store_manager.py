"""
向量存储管理器
负责向量数据库的初始化、向量化、检索等操作
"""
from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config.settings import settings
from data_access.dashscope_embeddings import DashScopeEmbeddings
from infrastructure.logger import logger



class VectorStoreManager:
    """
    向量存储管理器
    封装向量数据库的操作，提供统一的接口
    """

    def __init__(self):
        """
        初始化向量存储管理器

        注意：使用延迟初始化，避免在导入时就创建连接
        """
        self._embedding = None
        self._vector_store = None

    @property
    def embedding(self) -> DashScopeEmbeddings:
        """
        延迟初始化 embedding 模型

        Returns:
            DashScopeEmbeddings: 阿里百炼嵌入模型实例
        """
        if self._embedding is None:
            self._embedding = DashScopeEmbeddings(
                model=settings.EMBEDDING_MODEL
            )
            logger.info(f"✅ Embedding 模型已初始化: {settings.EMBEDDING_MODEL}")
        return self._embedding

    @property
    def vector_store(self) -> Chroma:
        """
        延迟初始化向量数据库

        Returns:
            Chroma: ChromaDB 向量数据库实例
        """
        if self._vector_store is None:
            self._vector_store = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                collection_name="its-knowledge",
                embedding_function=self.embedding
            )
            logger.info(f"✅ 向量数据库已初始化: {settings.VECTOR_STORE_PATH}")
        return self._vector_store

    def embed_query(self, text: str) -> List[float]:
        """
        对查询文本进行向量化

        Args:
            text: 查询文本

        Returns:
            List[float]: 文本的向量表示
        """
        return self.embedding.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对文档列表进行向量化

        Args:
            texts: 文档文本列表

        Returns:
            List[List[float]]: 文档向量列表
        """
        return self.embedding.embed_documents(texts)

    def get_retriever(self, search_kwargs: dict = None):
        """
        获取向量检索器

        Args:
            search_kwargs: 检索参数，例如 {"k": 5} 表示返回前5个结果

        Returns:
            VectorStoreRetriever: 向量检索器实例
        """
        if search_kwargs is None:
            search_kwargs = {"k": settings.TOP_FINAL}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量，默认使用配置中的 TOP_FINAL

        Returns:
            List[Document]: 相似文档列表
        """
        if k is None:
            k = settings.TOP_FINAL

        return self.vector_store.similarity_search(query, k=k)

