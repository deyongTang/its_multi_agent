"""
ES 混合检索服务 (RAG V2.0)
实现基于 Elasticsearch 的混合检索：BM25 关键词检索 + 向量语义检索
"""

from typing import List, Dict, Any, Optional

try:
    from infrastructure.es_client import ESClient
    from services.embedding_service import EmbeddingService
    from services.text_processor import TextProcessor
    from config.settings import settings
    from infrastructure.logger import logger
except ModuleNotFoundError:
    import sys
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from infrastructure.es_client import ESClient
    from services.embedding_service import EmbeddingService
    from services.text_processor import TextProcessor
    from config.settings import settings
    from infrastructure.logger import logger


class ESRetrievalService:
    """
    ES 混合检索服务 (RAG V2.0)

    核心特性：
    1. 混合检索：BM25 关键词匹配 + KNN 向量语义检索
    2. Collapse 折叠：按 knowledge_no 去重，返回不重复的知识点
    3. 父子文档：检索用 Chunk，展示用 Parent
    """

    def __init__(self):
        """初始化检索服务"""
        self.es_client = ESClient()
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        self.index_name = settings.ES_INDEX_NAME
        logger.info(f"✅ ES 混合检索服务初始化成功，索引: {self.index_name}")

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        keyword_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        混合检索：BM25 + 向量检索 + Collapse 折叠

        Args:
            query: 用户查询
            top_k: 返回的知识点数量
            keyword_weight: 关键词检索权重
            vector_weight: 向量检索权重

        Returns:
            List[Dict]: 检索结果列表，每个元素包含 knowledge_no 和 score
        """
        try:
            # 1. 预处理查询
            query_segmented = self.text_processor.segment_chinese(query)
            query_vector = self.embedding_service.embed_text(query)

            logger.info(f"🔍 开始混合检索: {query}")
            logger.info(f"   分词结果: {query_segmented[:100]}...")

            # 2. 构造混合检索 DSL
            search_body = self._build_hybrid_search_dsl(
                query_segmented=query_segmented,
                query_vector=query_vector,
                top_k=top_k,
                keyword_weight=keyword_weight,
                vector_weight=vector_weight,
            )

            # 3. 执行检索
            response = self.es_client.search(self.index_name, search_body)

            # 4. 解析结果
            results = self._parse_search_results(response)

            logger.info(f"✅ 检索完成，返回 {len(results)} 个知识点")
            return results

        except Exception as e:
            logger.error(f"❌ 混合检索失败: {e}")
            raise

    def _build_hybrid_search_dsl(
        self,
        query_segmented: str,
        query_vector: List[float],
        top_k: int,
        keyword_weight: float,
        vector_weight: float,
    ) -> Dict[str, Any]:
        """
        构造混合检索 DSL 查询

        核心逻辑：
        1. Filter: 只检索 doc_type=chunk
        2. Should: BM25 关键词 + KNN 向量
        3. Collapse: 按 knowledge_no 折叠去重

        Args:
            query_segmented: 分词后的查询
            query_vector: 查询向量
            top_k: 返回数量
            keyword_weight: 关键词权重
            vector_weight: 向量权重

        Returns:
            Dict: ES DSL 查询体
        """
        dsl = {
            "size": top_k * 3,  # 折叠前多召回一些
            "query": {
                "bool": {
                    "filter": [{"term": {"doc_type": "chunk"}}],  # 只检索 chunk
                    "should": [
                        # 路径 1: BM25 关键词检索
                        {
                            "multi_match": {
                                "query": query_segmented,
                                "fields": ["title^2", "content"],  # title 权重 2 倍
                                "type": "best_fields",
                                "boost": keyword_weight,
                            }
                        },
                        # 路径 2: KNN 向量检索
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                    "params": {"query_vector": query_vector},
                                },
                                "boost": vector_weight,
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            },
            # Collapse 折叠：按 knowledge_no 去重
            "collapse": {"field": "knowledge_no"},
            # 返回字段
            "_source": ["doc_id", "knowledge_no", "title", "content", "chunk_index"],
        }

        return dsl

    def _parse_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 ES 检索结果

        Args:
            response: ES 响应

        Returns:
            List[Dict]: 解析后的结果列表
        """
        results = []
        hits = response.get("hits", {}).get("hits", [])

        for hit in hits:
            source = hit.get("_source", {})
            results.append(
                {
                    "knowledge_no": source.get("knowledge_no"),
                    "doc_id": source.get("doc_id"),
                    "title": source.get("title"),
                    "content": source.get("content"),
                    "chunk_index": source.get("chunk_index"),
                    "score": hit.get("_score", 0),
                }
            )

        return results

    def get_parent_documents(self, knowledge_nos: List[str]) -> Dict[str, str]:
        """
        批量获取父文档的完整内容

        Args:
            knowledge_nos: 知识点 ID 列表

        Returns:
            Dict[str, str]: {knowledge_no: full_content}
        """
        try:
            if not knowledge_nos:
                return {}

            # 构造批量查询
            parent_ids = [f"{kno}_parent" for kno in knowledge_nos]

            # 使用 mget 批量获取
            docs = self.es_client.mget(self.index_name, parent_ids)

            # 解析结果
            # 注意：es_client.mget() 返回的是 _source 内容列表，不是完整文档结构
            result = {}
            for doc in docs:
                if doc:  # doc 已经是 _source 的内容
                    knowledge_no = doc.get("knowledge_no")
                    full_content = doc.get("full_content", "")
                    if knowledge_no and full_content:
                        result[knowledge_no] = full_content

            logger.info(f"✅ 获取了 {len(result)} 个父文档")
            return result

        except Exception as e:
            logger.error(f"❌ 获取父文档失败: {e}")
            return {}

    def _keyword_search(self, query_segmented: str, top_k: int) -> List[Dict[str, Any]]:
        """
        纯关键词检索（BM25）

        Args:
            query_segmented: 分词后的查询
            top_k: 返回数量

        Returns:
            List[Dict]: 检索结果
        """
        dsl = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": [{"term": {"doc_type": "chunk"}}],
                    "must": [
                        {
                            "multi_match": {
                                "query": query_segmented,
                                "fields": ["title^2", "content"],
                                "type": "best_fields",
                            }
                        }
                    ],
                }
            },
            "_source": ["doc_id", "knowledge_no", "title", "content", "chunk_index"],
        }

        response = self.es_client.search(self.index_name, dsl)
        return self._parse_search_results(response)

    def _vector_search(
        self, query_vector: List[float], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        纯向量检索（KNN）

        Args:
            query_vector: 查询向量
            top_k: 返回数量

        Returns:
            List[Dict]: 检索结果
        """
        dsl = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": [{"term": {"doc_type": "chunk"}}],
                    "must": [
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                    "params": {"query_vector": query_vector},
                                },
                            }
                        }
                    ],
                }
            },
            "_source": ["doc_id", "knowledge_no", "title", "content", "chunk_index"],
        }

        response = self.es_client.search(self.index_name, dsl)
        return self._parse_search_results(response)

    def _rrf_fusion(
        self,
        keyword_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        RRF (Reciprocal Rank Fusion) 融合排序算法

        核心公式：score(doc) = Σ 1/(k + rank_i(doc))
        其中 k=60 是常用的平滑参数

        Args:
            keyword_results: BM25 关键词检索结果
            vector_results: 向量检索结果
            k: RRF 平滑参数（默认 60）

        Returns:
            List[Dict]: 融合后的结果列表
        """
        rrf_scores = {}

        # 1. 计算关键词检索的 RRF 分数
        for rank, result in enumerate(keyword_results, start=1):
            knowledge_no = result["knowledge_no"]
            score = 1.0 / (k + rank)
            if knowledge_no not in rrf_scores:
                rrf_scores[knowledge_no] = {
                    "knowledge_no": knowledge_no,
                    "doc_id": result["doc_id"],
                    "title": result["title"],
                    "content": result["content"],
                    "chunk_index": result["chunk_index"],
                    "rrf_score": 0.0,
                    "keyword_rank": rank,
                    "vector_rank": None,
                }
            rrf_scores[knowledge_no]["rrf_score"] += score

        # 2. 计算向量检索的 RRF 分数
        for rank, result in enumerate(vector_results, start=1):
            knowledge_no = result["knowledge_no"]
            score = 1.0 / (k + rank)
            if knowledge_no not in rrf_scores:
                rrf_scores[knowledge_no] = {
                    "knowledge_no": knowledge_no,
                    "doc_id": result["doc_id"],
                    "title": result["title"],
                    "content": result["content"],
                    "chunk_index": result["chunk_index"],
                    "rrf_score": 0.0,
                    "keyword_rank": None,
                    "vector_rank": rank,
                }
            else:
                rrf_scores[knowledge_no]["vector_rank"] = rank
            rrf_scores[knowledge_no]["rrf_score"] += score

        # 3. 按 RRF 分数排序
        sorted_results = sorted(
            rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True
        )

        logger.info(f"✅ RRF 融合完成: {len(sorted_results)} 个唯一知识点")
        return sorted_results

    def rrf_search(
        self, query: str, top_k: int = 5, rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        基于 RRF 的混合检索（用于 A/B 测试）

        流程：
        1. 分别执行 BM25 关键词检索和向量检索
        2. 使用 RRF 算法融合两路结果
        3. 按 knowledge_no 去重（已在 RRF 融合中完成）

        Args:
            query: 用户查询
            top_k: 返回的知识点数量
            rrf_k: RRF 平滑参数

        Returns:
            List[Dict]: 检索结果列表
        """
        try:
            # 1. 预处理查询
            query_segmented = self.text_processor.segment_chinese(query)
            query_vector = self.embedding_service.embed_query(query)

            logger.info(f"🔍 开始 RRF 混合检索: {query}")

            # 2. 分别执行两路检索（召回更多候选）
            keyword_results = self._keyword_search(query_segmented, top_k=top_k * 3)
            vector_results = self._vector_search(query_vector, top_k=top_k * 3)

            logger.info(f"   关键词检索: {len(keyword_results)} 个结果")
            logger.info(f"   向量检索: {len(vector_results)} 个结果")

            # 3. RRF 融合排序
            fused_results = self._rrf_fusion(keyword_results, vector_results, k=rrf_k)

            # 4. 取 Top-K
            final_results = fused_results[:top_k]

            logger.info(f"✅ RRF 检索完成，返回 {len(final_results)} 个知识点")
            return final_results

        except Exception as e:
            logger.error(f"❌ RRF 检索失败: {e}")
            raise

    def retrieve(
        self, query: str, top_k: int = 5, return_full_content: bool = True
    ) -> List[Dict[str, Any]]:
        """
        完整的检索流程（RAG V2.0）

        流程：
        1. 混合检索（BM25 + 向量）
        2. Collapse 折叠去重
        3. 获取父文档完整内容

        Args:
            query: 用户查询
            top_k: 返回的知识点数量
            return_full_content: 是否返回完整内容（Parent）

        Returns:
            List[Dict]: 检索结果，包含完整内容
        """
        try:
            # 1. 混合检索
            search_results = self.hybrid_search(query, top_k=top_k)

            if not search_results:
                logger.warning("⚠️ 未找到匹配的文档")
                return []

            # 2. 提取 knowledge_no
            knowledge_nos = [r["knowledge_no"] for r in search_results]

            # 3. 获取父文档
            if return_full_content:
                parent_docs = self.get_parent_documents(knowledge_nos)

                # 4. 合并结果
                for result in search_results:
                    kno = result["knowledge_no"]
                    result["full_content"] = parent_docs.get(kno, "")

            return search_results

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    from infrastructure.logger import logger

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    print("\n" + "=" * 60)
    print("测试 ES 混合检索服务 (RAG V2.0)")
    print("=" * 60)

    # 初始化服务
    service = ESRetrievalService()

    # 测试查询
    test_queries = ["联想手机K900如何插拔SIM卡", "电池续航问题", "如何连接WiFi"]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")

        try:
            results = service.retrieve(query, top_k=3)

            if results:
                print(f"✅ 找到 {len(results)} 个结果:\n")
                for i, result in enumerate(results, 1):
                    print(f"--- 结果 {i} ---")
                    print(f"Knowledge No: {result['knowledge_no']}")
                    print(f"标题: {result['title'][:50]}...")
                    print(f"分数: {result['score']:.4f}")
                    print(f"完整内容长度: {len(result.get('full_content', ''))} 字符")
                    print()
            else:
                print("⚠️ 未找到匹配结果")

        except Exception as e:
            print(f"❌ 查询失败: {e}")
