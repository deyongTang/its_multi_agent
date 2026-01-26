"""
Embedding 服务封装
负责文本向量化，支持批量处理
"""

from typing import List
from openai import OpenAI

try:
    from config.settings import settings
except ModuleNotFoundError:
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config.settings import settings
from infrastructure.logger import logger



class EmbeddingService:
    """文本向量化服务"""

    def __init__(self):
        """初始化 OpenAI 客户端"""
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL
        )
        self.model = settings.EMBEDDING_MODEL
        logger.info(f"✅ Embedding 服务初始化成功，模型: {self.model}")

    def embed_text(self, text: str) -> List[float]:
        """
        对单个文本进行向量化

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量表示
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ 文本向量化失败: {e}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        批量向量化文本

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            List[List[float]]: 向量列表
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
                logger.info(f"✅ 批量向量化进度: {len(all_embeddings)}/{len(texts)}")
            except Exception as e:
                logger.error(f"❌ 批量向量化失败 (batch {i//batch_size}): {e}")
                raise

        return all_embeddings


if __name__ == "__main__":
    # 测试代码
    service = EmbeddingService()

    # 测试单个文本
    text = "这是一个测试文本"
    vector = service.embed_text(text)
    print(f"向量维度: {len(vector)}")
    print(f"向量前5个值: {vector[:5]}")

    # 测试批量
    texts = ["文本1", "文本2", "文本3"]
    vectors = service.embed_batch(texts)
    print(f"批量向量化完成，共 {len(vectors)} 个向量")
