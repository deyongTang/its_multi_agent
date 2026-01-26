"""
文件存储服务

负责文件的保存、读取、哈希计算等操作
使用 MinIO 作为后端存储 (OSS)
"""
import hashlib
from typing import Tuple
from infrastructure.logger import logger
from infrastructure.object_storage import MinioStorageClient


class FileStorageService:
    """文件存储服务 (MinIO Backend)"""

    def __init__(self):
        self.minio_client = MinioStorageClient()

    def save_file(self, file_content: bytes, knowledge_no: str) -> Tuple[str, str]:
        """
        保存文件到存储 (MinIO)

        Args:
            file_content: 文件内容 (字节)
            knowledge_no: 知识编号

        Returns:
            Tuple[str, str]: (oss_path, md_hash)
        """
        try:
            # 1. 计算 SHA256 哈希
            md_hash = self._calculate_hash(file_content)

            # 2. 生成存储路径 (Object Name): {knowledge_no}/{md_hash}.md
            file_name = f"{md_hash}.md"
            oss_path = f"{knowledge_no}/{file_name}"

            # 3. 上传到 MinIO
            self.minio_client.upload_file(
                object_name=oss_path,
                data=file_content,
                content_type="text/markdown"
            )

            logger.info(f"文件已保存到 MinIO: {oss_path}")
            return oss_path, md_hash

        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise e

    def _calculate_hash(self, file_content: bytes) -> str:
        """
        计算文件内容的 SHA256 哈希

        Args:
            file_content: 文件内容 (字节)

        Returns:
            str: SHA256 哈希值
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        return sha256_hash.hexdigest()

    def get_file_path(self, knowledge_no: str, md_hash: str) -> str:
        """
        根据知识编号和哈希获取文件路径 (Object Name)

        Args:
            knowledge_no: 知识编号
            md_hash: 内容哈希

        Returns:
            str: 文件路径 (Object Name)
        """
        return f"{knowledge_no}/{md_hash}.md"

    def file_exists(self, oss_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            oss_path: 文件路径 (Object Name)

        Returns:
            bool: 文件是否存在
        """
        return self.minio_client.file_exists(oss_path)

    def read_file(self, oss_path: str) -> bytes:
        """
        读取文件内容

        Args:
            oss_path: 文件路径 (Object Name)

        Returns:
            bytes: 文件内容
        """
        try:
            return self.minio_client.download_file(oss_path)
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            raise
