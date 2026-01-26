"""
文档摄入 Worker 服务

后台任务,处理待向量化的文档
"""
from typing import Dict
from data_access.knowledge_asset_repository import KnowledgeAssetRepository
from business_logic.file_storage_service import FileStorageService
from services.es_ingestion_processor import ESIngestionProcessor
from config.settings import settings
from infrastructure.logger import logger


class IngestionWorkerService:
    """文档摄入 Worker 服务"""

    def __init__(self):
        self.asset_repo = KnowledgeAssetRepository()
        self.file_storage = FileStorageService()
        self.es_ingestion_processor = ESIngestionProcessor()

    def process_pending_documents(self, batch_size: int = None) -> Dict:
        """
        处理待向量化的文档

        Args:
            batch_size: 批次大小 (默认从配置读取)

        Returns:
            Dict: {processed, success, failed}
        """
        if batch_size is None:
            batch_size = settings.WORKER_BATCH_SIZE

        # 统计信息
        processed = 0
        success = 0
        failed = 0

        try:
            # 1. 获取待处理文档列表 (状态: NEW)
            pending_docs = self.asset_repo.list_by_status('NEW', batch_size)

            if not pending_docs:
                logger.info("没有待处理的文档")
                return {'processed': 0, 'success': 0, 'failed': 0}

            logger.info(f"开始处理 {len(pending_docs)} 个待处理文档")

            # 2. 遍历每个文档
            for doc in pending_docs:
                knowledge_no = doc['knowledge_no']
                asset_uuid = doc.get('asset_uuid')
                oss_path = doc['latest_oss_path']
                processed += 1
                
                if not asset_uuid:
                    logger.error(f"文档缺失 asset_uuid: {knowledge_no}, 跳过处理")
                    failed += 1
                    continue

                try:
                    # a. 从 MinIO 读取文件内容
                    file_bytes = self.file_storage.read_file(oss_path)
                    file_content = file_bytes.decode('utf-8')
                    
                    # b. 获取标题 (简单处理，实际可能需要从内容解析)
                    title = "" 

                    # c. 调用 es_ingestion_processor.ingest_content()
                    chunks_count = self.es_ingestion_processor.ingest_content(
                        content=file_content,
                        title=title,
                        asset_uuid=asset_uuid,
                        knowledge_no=knowledge_no,
                        source_path=oss_path
                    )

                    # d. 更新状态为 INGESTED (使用 asset_uuid)
                    self.asset_repo.update_status(asset_uuid, 'INGESTED')

                    # e. 更新 chunks_count (使用 asset_uuid)
                    self.asset_repo.update_chunks_count(asset_uuid, chunks_count)

                    success += 1
                    logger.info(f"文档处理成功: {knowledge_no} (UUID: {asset_uuid}, {chunks_count} 块)")

                except Exception as e:
                    # 处理失败 (使用 asset_uuid)
                    error_message = str(e)
                    self.asset_repo.update_status(asset_uuid, 'FAILED', error_message)
                    self.asset_repo.increment_retry_count(asset_uuid)
                    failed += 1
                    logger.error(f"文档处理失败: {knowledge_no} - {error_message}")

            logger.info(f"批次处理完成: 处理={processed}, 成功={success}, 失败={failed}")
            return {'processed': processed, 'success': success, 'failed': failed}

        except Exception as e:
            logger.error(f"处理待处理文档失败: {str(e)}")
            return {'processed': processed, 'success': success, 'failed': failed}

    def retry_failed_documents(self, max_retry: int = None) -> Dict:
        """
        重试失败的文档

        Args:
            max_retry: 最大重试次数 (默认从配置读取)

        Returns:
            Dict: {processed, success, failed}
        """
        if max_retry is None:
            max_retry = settings.WORKER_MAX_RETRY

        # 统计信息
        processed = 0
        success = 0
        failed = 0

        try:
            # 1. 获取失败文档列表 (状态: FAILED, retry_count < max_retry)
            failed_docs = self.asset_repo.list_by_status('FAILED', 100)

            # 过滤出重试次数未超限的文档
            retry_docs = [doc for doc in failed_docs if doc['retry_count'] < max_retry]

            if not retry_docs:
                logger.info("没有需要重试的文档")
                return {'processed': 0, 'success': 0, 'failed': 0}

            logger.info(f"开始重试 {len(retry_docs)} 个失败文档")

            # 2. 遍历每个文档
            for doc in retry_docs:
                knowledge_no = doc['knowledge_no']
                asset_uuid = doc.get('asset_uuid')
                oss_path = doc['latest_oss_path']
                processed += 1
                
                if not asset_uuid:
                    logger.error(f"文档缺失 asset_uuid: {knowledge_no}, 无法重试")
                    failed += 1
                    continue

                try:
                    # a. 从 MinIO 读取文件内容
                    file_bytes = self.file_storage.read_file(oss_path)
                    file_content = file_bytes.decode('utf-8')

                    # b. 调用 es_ingestion_processor.ingest_content()
                    chunks_count = self.es_ingestion_processor.ingest_content(
                        content=file_content,
                        title="",
                        asset_uuid=asset_uuid,
                        knowledge_no=knowledge_no,
                        source_path=oss_path
                    )

                    # 更新状态为 INGESTED (使用 asset_uuid)
                    self.asset_repo.update_status(asset_uuid, 'INGESTED')
                    self.asset_repo.update_chunks_count(asset_uuid, chunks_count)

                    success += 1
                    logger.info(f"文档重试成功: {knowledge_no}")

                except Exception as e:
                    # 重试失败 (使用 asset_uuid)
                    error_message = str(e)
                    self.asset_repo.update_status(asset_uuid, 'FAILED', error_message)
                    self.asset_repo.increment_retry_count(asset_uuid)
                    failed += 1
                    logger.error(f"文档重试失败: {knowledge_no} - {error_message}")

            logger.info(f"重试完成: 处理={processed}, 成功={success}, 失败={failed}")
            return {'processed': processed, 'success': success, 'failed': failed}

        except Exception as e:
            logger.error(f"重试失败文档失败: {str(e)}")
            return {'processed': processed, 'success': success, 'failed': failed}