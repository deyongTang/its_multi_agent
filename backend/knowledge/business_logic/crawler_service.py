from typing import Any, Optional
import time
from datetime import datetime
from services.crawler.client import KnowledgeApiClient
from services.crawler.parser import HtmlParser
from utils.text_utils import TextUtils
from business_logic.document_sync_service import DocumentSyncService
from infrastructure.logger import logger

class CrawlerService:
    """
    爬虫服务 (Crawler Service)
    
    核心职责:
    1. 负责调度数据的抓取 (Fetching)
    2. 执行内容的解析与清洗 (Parsing & Cleaning)
    3. 调用同步服务将数据归档 (Syncing to OSS & DB)
    """

    def __init__(self):
        # 初始化文档同步服务，用于后续的上传和数据库记录
        self.sync_service = DocumentSyncService()

    def crawl_range(self, start_id: int, end_id: int, delay: float = 0.05) -> dict:
        """
        批量爬取指定范围的知识文档
        
        Args:
            start_id (int): 起始知识点 ID
            end_id (int): 结束知识点 ID
            delay (float): 每次请求的间隔时间(秒)，防止对源站造成过大压力

        Returns:
            dict: 统计结果 {success: 成功数, fail: 失败数}
        """
        success = 0
        fail = 0
        
        logger.info(f"启动爬虫任务: ID范围 {start_id} 到 {end_id}")

        for i in range(start_id, end_id + 1):
            knowledge_no = str(i)
            logger.info(f"[{i}/{end_id}] 正在获取知识点 KnowledgeNo: {knowledge_no}")

            try:
                # 1. 获取原始内容 (Fetch)
                # 调用 KnowledgeApiClient 从源站接口获取 JSON 数据
                knowledge_content: Optional[dict[str, Any]] = KnowledgeApiClient.fetch_knowledge_content(
                    knowledge_no=knowledge_no
                )

                content = knowledge_content.get("content") if knowledge_content else None
                
                if knowledge_content and content:
                    # 2. 解析 HTML 转 Markdown (Parse)
                    # 使用 HtmlParser 去除无关标签，保留核心语义
                    parser = HtmlParser()
                    md_content = parser.parse_html_to_markdown(knowledge_no, knowledge_content)

                    # 3. 清洗文件名 (Clean)
                    # 提取标题并去除非法字符，限制长度，确保能作为文件名使用
                    md_title = knowledge_content.get('title', "无标题")
                    clean_title = TextUtils.clean_filename(md_title.strip())
                    if len(clean_title) > 50:
                        clean_title = clean_title[:50].rstrip("_")

                    # 4. 上传 OSS 并同步数据库 (Sync)
                    # 将 Markdown 内容转为字节流，调用 sync_service 处理
                    # 这一步会：上传 MinIO -> 计算 Hash -> 写入 knowledge_asset 表 (状态 NEW)
                    file_content_bytes = md_content.encode('utf-8')
                    result = self.sync_service.upload_document(
                        file_content=file_content_bytes,
                        knowledge_no=knowledge_no,
                        source_update_time=datetime.now()
                    )
                    
                    status = result.get('status')
                    md_hash = result.get('md_hash')
                    
                    if status == 'duplicate':
                         logger.info(f" {knowledge_no}-> [重复] 跳过: {clean_title} (Hash: {md_hash})")
                    else:
                         logger.info(f" {knowledge_no}-> [成功] 上传: {clean_title} (Hash: {md_hash})")
                    
                    success += 1
                else:
                    logger.warning(f" {knowledge_no}-> [空] 无内容或不存在")
                    fail += 1

            except Exception as e:
                logger.error(f" {knowledge_no}-> [异常] 发生错误: {str(e)}")
                fail += 1

            # 礼貌性延时
            time.sleep(delay)

        logger.info(f"爬虫任务完成. 成功: {success}, 失败: {fail}")
        return {"success": success, "fail": fail}
