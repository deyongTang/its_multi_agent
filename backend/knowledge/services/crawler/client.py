import os.path
import sys
from http.client import HTTPException
from typing import Any, Optional

# Allow running this file directly without package import errors.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.crawler.parser import HtmlParser
from config.settings import settings
import requests


class KnowledgeApiClient:
    """主要提供一个方法 获取网络知识"""

    @staticmethod
    def fetch_knowledge_content(knowledge_no: str) -> Optional[dict[str, Any]]:
        """根据知识库编号 获取联想知识库内容(data部分)"""
        try:
            # 1.定义URL

            # https://iknow.lenovo.com.cn/knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=9999
            knowledge_base_url=f"{settings.KNOWLEDGE_BASE_URL}/knowledgeapi/api/knowledge/knowledgeDetails"

            # 2.定义param
            params={"knowledgeNo":knowledge_no}

            # 3.发送请求
            response=requests.get(url=knowledge_base_url, params=params,timeout=10)
            response.raise_for_status()

            # 4.得到结果(知识库内容)
            response_dict = response.json()
            # 5.获取data
            return response_dict.get("data")
        except HTTPException as  e:
            raise HTTPException(f"发送知识库请求失败:{e}")


if __name__ == '__main__':

    knowledge_content=KnowledgeApiClient.fetch_knowledge_content(knowledge_no = '437040')

    print(f"知识库1数据内容:\n{knowledge_content}")

    # 检查 knowledge_content 是否为 None
    if knowledge_content is None:
        print("错误: 未能获取知识库内容")
        sys.exit(1)

    parser=HtmlParser()
    md_content=parser.parse_html_to_markdown('437040',knowledge_content)

    file_name_path=os.path.dirname(__file__)

    file_name=os.path.join(file_name_path,"test_01.md")

    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(md_content)






