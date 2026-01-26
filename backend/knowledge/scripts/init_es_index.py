"""
Elasticsearch 索引初始化脚本
根据 RAG V2 架构设计创建 its_knowledge_index 索引
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.es_client import ESClient
from config.settings import settings



def get_index_mapping():
    """
    获取索引 Mapping 定义（根据 RAG V2 架构设计）

    Returns:
        Dict: 索引 Mapping 配置
    """
    return {
        "mappings": {
            "properties": {
                "doc_id": {
                    "type": "keyword"
                },
                "knowledge_no": {
                    "type": "keyword"
                },
                "doc_type": {
                    "type": "keyword"
                },
                # --- 搜索域 (Chunks 使用) ---
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "copy_to": "all_text"
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "copy_to": "all_text"
                },
                "all_text": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                "content_vector": {
                    "type": "dense_vector",
                    "dims": settings.ES_VECTOR_DIMS,
                    "index": True,
                    "similarity": "cosine"
                },
                "chunk_index": {
                    "type": "integer"
                },
                # --- 存储域 (Parent 使用) ---
                "full_content": {
                    "type": "text",
                    "index": False,
                    "store": True
                },
                "file_path": {
                    "type": "keyword"
                },
                "content_md5": {
                    "type": "keyword"
                },
                "source_url": {
                    "type": "keyword"
                },
                "created_at": {
                    "type": "date"
                }
            }
        }
    }


def init_index(force_recreate: bool = False):
    """
    初始化索引

    Args:
        force_recreate: 是否强制重建索引（删除已存在的索引）
    """
    try:
        es_client = ESClient()
        index_name = settings.ES_INDEX_NAME

        # 检查索引是否存在
        exists = es_client.index_exists(index_name)

        if exists:
            if force_recreate:
                logger.warning(f"⚠️ 索引 {index_name} 已存在，准备删除...")
                es_client.delete_index(index_name)
                logger.info(f"✅ 索引 {index_name} 已删除")
            else:
                logger.info(f"ℹ️ 索引 {index_name} 已存在，跳过创建")
                return

        # 创建索引
        mapping = get_index_mapping()
        success = es_client.create_index(index_name, mapping)

        if success:
            logger.info(f"✅ 索引 {index_name} 创建成功")
            logger.info(f"📊 向量维度: {settings.ES_VECTOR_DIMS}")
        else:
            logger.error(f"❌ 索引 {index_name} 创建失败")

        es_client.close()

    except Exception as e:
        logger.error(f"❌ 初始化索引失败: {e}")
        raise


if __name__ == "__main__":
    import argparse
    from infrastructure.logger import logger

    parser = argparse.ArgumentParser(description="初始化 Elasticsearch 索引")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重建索引（删除已存在的索引）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Elasticsearch 索引初始化")
    print("=" * 60)
    print(f"索引名称: {settings.ES_INDEX_NAME}")
    print(f"ES 地址: {settings.ES_SCHEME}://{settings.ES_HOST}:{settings.ES_PORT}")
    print(f"向量维度: {settings.ES_VECTOR_DIMS}")
    print("=" * 60)

    init_index(force_recreate=args.force)

    print("\n✅ 初始化完成")
