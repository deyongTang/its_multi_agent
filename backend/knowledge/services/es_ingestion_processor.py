"""
ES 入库处理器
负责将文档处理并写入 Elasticsearch（N+1 存储模式）
"""

from typing import List, Dict, Any
import os
from datetime import datetime
import uuid

try:
    from infrastructure.es_client import ESClient
    from services.embedding_service import EmbeddingService
    from services.text_processor import TextProcessor
    from config.settings import settings
    from infrastructure.logger import logger
except ModuleNotFoundError:
    import sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from infrastructure.es_client import ESClient
    from services.embedding_service import EmbeddingService
    from services.text_processor import TextProcessor
    from config.settings import settings
    from infrastructure.logger import logger


class ESIngestionProcessor:
    """ES 入库处理器 - 实现 N+1 存储模式"""

    def __init__(self):
        """初始化处理器"""
        self.es_client = ESClient()
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        self.index_name = settings.ES_INDEX_NAME
        logger.info(f"✅ ES 入库处理器初始化成功，索引: {self.index_name}")

    def ingest_file(
        self, file_path: str, title: str = "", knowledge_no: str = None
    ) -> int:
        """
        处理并入库单个文件（N+1 模式）

        Args:
            file_path: 文件路径
            title: 文档标题（可选）
            knowledge_no: 知识点编号（可选）。如果不传，则根据 file_path 生成。

        Returns:
            int: 入库的文档数量
        """
        try:
            # 1. 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                full_content = f.read()

            # 如果没有提供标题，使用文件名
            if not title:
                title = os.path.splitext(os.path.basename(file_path))[0]

            logger.info(f"📄 开始处理文件: {title}")

            # 2. 生成 knowledge_no
            if not knowledge_no:
                knowledge_no = TextProcessor.generate_knowledge_no(file_path)

            # 3. 调用核心入库逻辑
            return self.ingest_content(
                content=full_content,
                title=title,
                knowledge_no=knowledge_no,
                source_path=file_path
            )

        except Exception as e:
            logger.error(f"❌ 文件入库失败: {e}")
            raise

    def ingest_content(
        self, content: str, title: str, asset_uuid: str, knowledge_no: str, source_path: str = ""
    ) -> int:
        """
        处理并入库内存中的文本内容

        Args:
            content: 文本内容
            title: 标题
            asset_uuid: 内部业务ID (用于生成 ES _id)
            knowledge_no: 外部知识编号 (仅存储用于展示)
            source_path: 源路径（可选，用于记录元数据）

        Returns:
            int: 入库数量
        """
        try:
            logger.info(f"🔑 Processing Asset UUID: {asset_uuid} (External: {knowledge_no})")

            # --- MD5 优化开始 ---
            import hashlib
            content_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()

            try:
                # 尝试获取 Parent 文档 (ID 使用 asset_uuid)
                existing_parent = self.es_client.get_document(
                    self.index_name, f"{asset_uuid}_parent"
                )
                if existing_parent:
                    old_md5 = existing_parent.get("content_md5")
                    if old_md5 == content_md5:
                        logger.info(f"⏭️ 文档内容未变更 (MD5: {content_md5})，跳过入库")
                        return 0
                    else:
                        logger.info(
                            f"🔄 文档内容变更 (Old: {old_md5} -> New: {content_md5})，准备更新"
                        )
            except Exception as e:
                logger.warning(f"⚠️ 检查旧版本失败，继续执行入库: {e}")
            # --- MD5 优化结束 ---

            # 清理旧数据 (使用 asset_uuid 查询)
            deleted_count = self.es_client.delete_by_query(
                self.index_name, query={"term": {"asset_uuid": asset_uuid}}
            )
            if deleted_count > 0:
                logger.info(f"🧹 清理旧数据: 删除了 {deleted_count} 条关联文档")

            # 文本切分
            chunks = self.text_processor.split_text(content, title)
            logger.info(f"✂️ 文本切分完成: {len(chunks)} 个 chunks")

            # 准备文档
            documents = self._prepare_documents(
                asset_uuid=asset_uuid,
                knowledge_no=knowledge_no,
                title=title,
                full_content=content,
                chunks=chunks,
                file_path=source_path,
                content_md5=content_md5,
            )

            # 批量写入
            success_count = self._bulk_write_to_es(documents)

            logger.info(f"✅ 入库完成: {title}, 共 {success_count} 条记录")
            return success_count

        except Exception as e:
            logger.error(f"❌ 内容入库失败: {e}")
            raise

    def _prepare_documents(
        self,
        asset_uuid: str,
        knowledge_no: str,
        title: str,
        full_content: str,
        chunks: List[Dict[str, Any]],
        file_path: str,
        content_md5: str = "",
    ) -> List[Dict[str, Any]]:
        """
        准备写入 ES 的文档（N+1 模式）
        """
        documents = []
        current_time = datetime.utcnow().isoformat()

        # 1. 创建 Parent 文档
        parent_doc = {
            "doc_id": f"{asset_uuid}_parent",
            "asset_uuid": asset_uuid,
            "knowledge_no": knowledge_no,
            "doc_type": "parent",
            "title": title,
            "full_content": full_content,
            "file_path": file_path,
            "content_md5": content_md5,
            "created_at": current_time,
        }
        documents.append(parent_doc)
        logger.info(f"📝 创建 Parent 文档: {parent_doc['doc_id']}")

        # 2. 处理 Chunks
        chunk_texts = [chunk["content"] for chunk in chunks]
        logger.info(f"🔄 开始向量化 {len(chunk_texts)} 个 chunks...")
        chunk_vectors = self.embedding_service.embed_batch(chunk_texts)
        title_segmented = self.text_processor.segment_chinese(title)

        for i, (chunk, vector) in enumerate(zip(chunks, chunk_vectors)):
            content_segmented = self.text_processor.segment_chinese(chunk["content"])

            chunk_doc = {
                "doc_id": f"{asset_uuid}_chunk_{i}",
                "asset_uuid": asset_uuid,
                "knowledge_no": knowledge_no,
                "doc_type": "chunk",
                "title": title_segmented,
                "content": content_segmented,
                "content_vector": vector,
                "chunk_index": chunk["chunk_index"],
                "file_path": file_path,
                "created_at": current_time,
            }
            documents.append(chunk_doc)

        return documents

    def _bulk_write_to_es(self, documents: List[Dict[str, Any]]) -> int:
        """
        批量写入文档到 ES

        Args:
            documents: 文档列表

        Returns:
            int: 成功写入的文档数量
        """
        try:
            # 构造 bulk 操作
            actions = []
            for doc in documents:
                action = {
                    "_index": self.index_name,
                    "_id": doc["doc_id"],
                    "_source": doc,
                }
                actions.append(action)

            # 执行批量写入
            success, failed = self.es_client.bulk_index(actions)

            # failed 是一个列表，包含失败的操作
            failed_count = len(failed) if isinstance(failed, list) else 0
            if failed_count > 0:
                logger.warning(
                    f"⚠️ 部分文档写入失败: 成功 {success}, 失败 {failed_count}"
                )
                # 记录失败的文档 ID
                for fail_item in failed[:5]:  # 只记录前5个失败项
                    logger.error(f"  失败项: {fail_item}")

            return success

        except Exception as e:
            logger.error(f"❌ 批量写入 ES 失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    import sys
    from infrastructure.logger import logger

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # 创建测试文件
    test_file = "/tmp/test_document.md"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 测试文档\n\n这是一个测试文档，用于验证 ES 入库功能。\n\n" * 100)

        # 测试入库
    processor = ESIngestionProcessor()
    count = processor.ingest_file(test_file, "测试文档标题")
    print(f"\n✅ 测试完成，入库 {count} 条记录")
