import os
import sys
import time
from typing import Any, Optional

# Ensure the project root (backend/knowledge) is on sys.path when run as a script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import os
import sys

# Ensure the project root (backend/knowledge) is on sys.path when run as a script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from business_logic.crawler_service import CrawlerService

def main():
    """
    爬虫 CLI 入口
    用于手动触发爬取任务，方便开发调试。
    """
    # 1. 初始化爬虫服务
    crawler = CrawlerService()
    print("Starting crawler CLI... (正在启动爬虫 CLI)")
    
    # 2. 执行爬取任务
    # 默认爬取 ID 1 到 1000。生产环境可以通过 argparse 接收参数
    # 结果会上传到 MinIO 并记录到数据库 (Status=NEW)
    result = crawler.crawl_range(1, 1000)
    
    print(f"\nCrawl complete! Success: {result['success']}, Failed: {result['fail']}")

if __name__ == '__main__':
    main()



if __name__ == '__main__':
    main()