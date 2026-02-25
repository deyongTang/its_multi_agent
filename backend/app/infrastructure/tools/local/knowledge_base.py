import httpx
from infrastructure.logging.logger import logger
from config.settings import settings


async def query_knowledge(question: str) -> str:
    """
    调用知识库平台 /query_sync 接口，获取完整的 RAG 答案。
    知识库内部已完成：检索 → query rewrite → LLM 生成，返回最终答案。
    """
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            headers = {}
            if settings.KNOWLEDGE_BASE_TOKEN:
                headers["Authorization"] = f"Bearer {settings.KNOWLEDGE_BASE_TOKEN}"

            response = await client.post(
                url=f"{settings.KNOWLEDGE_BASE_URL}/query_sync",
                json={"question": question},
                headers=headers,
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("answer", "")

        except httpx.HTTPError as e:
            logger.error(f"知识库查询失败: {e}")
            return ""
        except Exception as e:
            logger.error(f"知识库查询未知错误: {e}")
            return ""
