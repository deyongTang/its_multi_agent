"""
文档同步服务

协调文档上传、存储、数据库记录
"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid
from business_logic.file_storage_service import FileStorageService
from data_access.knowledge_asset_repository import KnowledgeAssetRepository
from data_access.knowledge_version_repository import KnowledgeVersionRepository
from infrastructure.logger import logger



class DocumentSyncService:
    """文档同步服务"""

    def __init__(self):
        self.file_storage = FileStorageService()
        self.asset_repo = KnowledgeAssetRepository()
        self.version_repo = KnowledgeVersionRepository()

    def upload_document(
        self,
        file_content: bytes,
        knowledge_no: str,
        source_update_time: Optional[datetime] = None
    ) -> Dict:
        """
        上传文档
        (架构升级: 使用 asset_uuid 作为 MinIO 和 ES 的关联键)

        Args:
            file_content: 文件内容 (字节)
            knowledge_no: 知识编号
            source_update_time: 源数据更新时间

        Returns:
            Dict: {status, knowledge_no, md_hash, is_duplicate}
        """
        try:
            # 1. 确定 asset_uuid
            # 先查库，如果已存在则复用 UUID，否则生成新的
            existing_asset = self.asset_repo.get_by_knowledge_no(knowledge_no)
            if existing_asset and existing_asset.get('asset_uuid'):
                asset_uuid = existing_asset['asset_uuid']
            else:
                asset_uuid = uuid.uuid4().hex

            # 2. 保存文件到 OSS (MinIO)
            # 路径规则: {asset_uuid}/{hash}.md
            oss_path, md_hash = self.file_storage.save_file(file_content, asset_uuid)

            # 3. 检查版本是否已存在 (幂等性)
            is_duplicate = self.version_repo.version_exists(asset_uuid, md_hash)

            if is_duplicate:
                logger.info(f"文档版本已存在,跳过: {knowledge_no} (UUID: {asset_uuid}) - {md_hash}")
                return {
                    'status': 'duplicate',
                    'knowledge_no': knowledge_no,
                    'asset_uuid': asset_uuid,
                    'md_hash': md_hash,
                    'is_duplicate': True
                }

            # 4. 插入/更新 knowledge_asset (状态: NEW)
            self.asset_repo.insert_or_update(
                knowledge_no=knowledge_no,
                md_hash=md_hash,
                oss_path=oss_path,
                asset_uuid=asset_uuid,
                source_update_time=source_update_time
            )

            # 5. 插入 knowledge_version
            self.version_repo.insert_version(
                knowledge_no=knowledge_no,
                asset_uuid=asset_uuid,
                md_hash=md_hash,
                oss_path=oss_path,
                source_update_time=source_update_time
            )

            logger.info(f"文档上传成功: {knowledge_no} (UUID: {asset_uuid}) - {md_hash}")
            return {
                'status': 'success',
                'knowledge_no': knowledge_no,
                'asset_uuid': asset_uuid,
                'md_hash': md_hash,
                'is_duplicate': False
            }

        except Exception as e:
            logger.error(f"文档上传失败: {str(e)}")
            raise e

    def get_document_status(self, knowledge_no: str) -> Optional[Dict]:
        """
        查询文档状态

        Args:
            knowledge_no: 知识编号

        Returns:
            Optional[Dict]: 文档状态信息
        """
        return self.asset_repo.get_by_knowledge_no(knowledge_no)

    def list_pending_documents(self, limit: int = 100) -> List[Dict]:
        """
        获取待处理文档列表

        Args:
            limit: 返回记录数限制

        Returns:
            List[Dict]: 待处理文档列表
        """
        return self.asset_repo.list_by_status('NEW', limit)
