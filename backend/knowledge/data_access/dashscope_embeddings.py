"""
阿里百炼 DashScope Embeddings 实现
解决 OpenAI 兼容模式下 embedding API 的格式问题
"""
import requests
from typing import List
from langchain_core.embeddings import Embeddings
from config.settings import settings


class DashScopeEmbeddings(Embeddings):
    """阿里百炼原生 Embeddings 实现"""

    def __init__(self, model: str = "text-embedding-v3"):
        self.model = model
        self.api_key = settings.API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对文档列表进行向量化
        阿里百炼限制：每次最多处理 10 个文本

        Args:
            texts: 文档文本列表

        Returns:
            List[List[float]]: 文档向量列表
        """
        # 阿里百炼的批处理限制
        BATCH_SIZE = 10
        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        处理单个批次的文本向量化

        Args:
            texts: 文档文本列表（不超过 10 个）

        Returns:
            List[List[float]]: 文档向量列表
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "input": {
                "texts": texts
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            embeddings = [item["embedding"] for item in result["output"]["embeddings"]]
            return embeddings

        except requests.exceptions.HTTPError as e:
            # 获取详细的错误信息
            error_detail = ""
            try:
                error_detail = response.text
            except:
                pass
            raise RuntimeError(f"阿里百炼 embedding HTTP 错误: {e}, 详情: {error_detail}")
        except Exception as e:
            raise RuntimeError(f"阿里百炼 embedding 调用失败: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        """
        对查询文本进行向量化

        Args:
            text: 查询文本

        Returns:
            List[float]: 文本的向量表示
        """
        # 调用 embed_documents 并返回第一个结果
        embeddings = self.embed_documents([text])
        return embeddings[0]
