"""
Reranker 服务封装
使用硅基流动 Rerank API 对召回候选进行精排
"""

from typing import List, Dict, Any
import httpx

try:
    from config.settings import settings
    from infrastructure.logger import logger
except ModuleNotFoundError:
    import sys
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config.settings import settings
    from infrastructure.logger import logger


class RerankerService:
    """Cross-Encoder 重排服务（API 方式）"""

    def __init__(self) -> None:
        self.api_key: str = settings.SILICONFLOW_API_KEY
        self.base_url: str = settings.RERANKER_BASE_URL.rstrip("/")
        self.model: str = settings.RERANKER_MODEL
        self.timeout: int = settings.RERANKER_TIMEOUT
        self.enabled: bool = settings.RERANKER_ENABLED and bool(self.api_key)

        if settings.RERANKER_ENABLED and not self.api_key:
            logger.warning("⚠️ RERANKER_ENABLED=True 但未配置 SILICONFLOW_API_KEY，自动降级为 RRF")

        logger.info(
            f"✅ Reranker 服务初始化完成 | enabled={self.enabled} | model={self.model}"
        )

    async def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        对候选文档重排序，返回 Top-K（保持原数据结构，新增 rerank_score）
        """
        if not docs:
            return []

        if not self.enabled:
            return docs[:top_k]

        documents = [doc.get("content", "") for doc in docs]
        if not any(documents):
            return docs[:top_k]

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": min(top_k, len(docs)),
            "return_documents": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/rerank",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            raw_results = data.get("results", [])
            reranked = []
            for item in raw_results:
                index = item.get("index")
                score = item.get("relevance_score", 0.0)
                if isinstance(index, int) and 0 <= index < len(docs):
                    doc = dict(docs[index])
                    doc["rerank_score"] = score
                    reranked.append(doc)

            if reranked:
                logger.info(
                    f"✅ Rerank 完成 | 候选={len(docs)} | 返回={len(reranked)}"
                )
                return reranked[:top_k]

            logger.warning("⚠️ Rerank 返回空结果，降级使用原排序")
            return docs[:top_k]
        except Exception as e:
            logger.error(f"❌ Rerank 失败，降级使用原排序: {e}")
            return docs[:top_k]
