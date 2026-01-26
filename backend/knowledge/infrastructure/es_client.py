"""
Elasticsearch 原生客户端工具
纯粹的基础设施层，只提供 ES 原生操作封装，不包含业务逻辑
"""

from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

# 尝试相对导入，如果失败则使用绝对导入
try:
    from config.settings import settings
except ModuleNotFoundError:
    import sys
    import os
    # 添加项目根目录到 Python 路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config.settings import settings



class ESClient:
    """Elasticsearch 原生客户端封装"""

    def __init__(self):
        """初始化 ES 客户端连接"""
        es_url = f"{settings.ES_SCHEME}://{settings.ES_HOST}:{settings.ES_PORT}"

        if settings.ES_USERNAME and settings.ES_PASSWORD:
            self.client = Elasticsearch(
                [es_url],
                basic_auth=(settings.ES_USERNAME, settings.ES_PASSWORD),
                verify_certs=False,
                request_timeout=30,
            )
        else:
            self.client = Elasticsearch(
                [es_url], verify_certs=False, request_timeout=30
            )

        try:
            info = self.client.info()
            print(f"✅ ES 连接成功: {info['version']['number']}")
        except Exception as e:
            print(f"❌ ES 连接失败: {e}")
            raise

    def close(self):
        """关闭 ES 连接"""
        if self.client:
            self.client.close()
            print("ES 连接已关闭")

    # ==================== 索引管理 ====================

    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """
        创建索引

        Args:
            index_name: 索引名称
            mapping: 索引 Mapping 定义

        Returns:
            bool: 是否成功
        """
        try:
            # ES 8.x: 使用 **mapping 解包，不再使用 body 参数
            self.client.indices.create(index=index_name, **mapping)
            print(f"✅ 索引 {index_name} 创建成功")
            return True
        except Exception as e:
            print(f"❌ 索引创建失败: {e}")
            return False

    def delete_index(self, index_name: str) -> bool:
        """
        删除索引

        Args:
            index_name: 索引名称

        Returns:
            bool: 是否成功
        """
        try:
            self.client.indices.delete(index=index_name)
            print(f"✅ 索引 {index_name} 删除成功")
            return True
        except Exception as e:
            print(f"❌ 索引删除失败: {e}")
            return False

    def index_exists(self, index_name: str) -> bool:
        """
        检查索引是否存在

        Args:
            index_name: 索引名称

        Returns:
            bool: 是否存在
        """
        # ES 8.x: exists() 返回 HeadApiResponse，需要转换为布尔值
        return bool(self.client.indices.exists(index=index_name))

    def refresh_index(self, index_name: str) -> bool:
        """
        刷新索引

        Args:
            index_name: 索引名称

        Returns:
            bool: 是否成功
        """
        try:
            self.client.indices.refresh(index=index_name)
            print(f"✅ 索引 {index_name} 刷新成功")
            return True
        except Exception as e:
            print(f"❌ 索引刷新失败: {e}")
            return False

    # ==================== 文档操作 ====================

    def index_document(
        self, index_name: str, doc_id: str, document: Dict[str, Any]
    ) -> bool:
        """
        索引单个文档

        Args:
            index_name: 索引名称
            doc_id: 文档 ID
            document: 文档内容

        Returns:
            bool: 是否成功
        """
        try:
            # ES 8.x: 使用 document 参数替代 body
            self.client.index(index=index_name, id=doc_id, document=document)
            print(f"✅ 文档 {doc_id} 索引成功")
            return True
        except Exception as e:
            print(f"❌ 文档索引失败: {e}")
            return False

    def bulk_index(self, actions: list) -> tuple:
        """
        批量索引文档

        Args:
            actions: 批量操作列表，格式：[{"_index": "...", "_id": "...", "_source": {...}}, ...]

        Returns:
            tuple: (成功数量, 失败的操作列表)
        """
        try:
            success, failed = bulk(self.client, actions, raise_on_error=False)
            failed_count = len(failed) if isinstance(failed, list) else failed
            print(f"✅ 批量索引完成: 成功 {success}, 失败 {failed_count}")
            return success, failed
        except Exception as e:
            print(f"❌ 批量索引失败: {e}")
            return 0, []

    def get_document(self, index_name: str, doc_id: str) -> Dict[str, Any]:
        """
        获取单个文档

        Args:
            index_name: 索引名称
            doc_id: 文档 ID

        Returns:
            Dict: 文档内容，如果不存在返回空字典
        """
        try:
            response = self.client.get(index=index_name, id=doc_id)
            return response.get("_source", {})
        except NotFoundError:
            # 文档不存在是正常情况，静默返回空字典
            return {}
        except Exception as e:
            print(f"❌ 获取文档失败: {e}")
            return {}

    def mget(self, index_name: str, doc_ids: list, source_fields: list = []) -> list:
        """
        批量获取文档

        Args:
            index_name: 索引名称
            doc_ids: 文档 ID 列表
            source_fields: 需要返回的字段列表，None 表示返回全部

        Returns:
            list: 文档列表
        """
        try:
            docs = [{"_id": doc_id} for doc_id in doc_ids]

            # ES 8.x: 使用 docs 参数替代 body，source_includes 指定返回字段
            if source_fields:
                response = self.client.mget(
                    index=index_name,
                    docs=docs,
                    source_includes=source_fields,
                )
            else:
                response = self.client.mget(
                    index=index_name,
                    docs=docs,
                )

            results = []
            for doc in response.get("docs", []):
                if doc.get("found"):
                    results.append(doc.get("_source", {}))

            return results
        except Exception as e:
            print(f"❌ 批量获取文档失败: {e}")
            return []

    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        删除单个文档

        Args:
            index_name: 索引名称
            doc_id: 文档 ID

        Returns:
            bool: 是否成功
        """
        try:
            self.client.delete(index=index_name, id=doc_id)
            print(f"✅ 文档 {doc_id} 删除成功")
            return True
        except Exception as e:
            print(f"❌ 删除文档失败: {e}")
            return False

    def delete_by_query(self, index_name: str, query: Dict[str, Any]) -> int:
        """
        根据查询条件删除文档

        Args:
            index_name: 索引名称
            query: 查询条件

        Returns:
            int: 删除的文档数量
        """
        try:
            # ES 8.x: 使用 query 参数替代 body
            response = self.client.delete_by_query(
                index=index_name, query=query
            )
            deleted = response.get("deleted", 0)
            print(f"✅ 删除了 {deleted} 条文档")
            return deleted
        except Exception as e:
            print(f"❌ 按查询删除失败: {e}")
            return 0

    # ==================== 搜索操作 ====================

    def search(self, index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索查询

        Args:
            index_name: 索引名称
            query: 查询 DSL

        Returns:
            Dict: 搜索结果
        """
        try:
            # ES 8.x: 直接解包 query 字典，不再使用 body 参数
            response = self.client.search(index=index_name, **query)
            # ES 8.x 返回 ObjectApiResponse，直接访问 body 属性
            return response.body
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}

    def count(self, index_name: str, query: Dict[str, Any] = {}) -> int:
        """
        统计文档数量

        Args:
            index_name: 索引名称
            query: 查询条件，None 表示统计全部

        Returns:
            int: 文档数量
        """
        try:
            # ES 8.x: 使用 query 参数替代 body
            if query:
                response = self.client.count(index=index_name, query=query)
            else:
                response = self.client.count(index=index_name)
            return response.get("count", 0)
        except Exception as e:
            print(f"❌ 统计失败: {e}")
            return 0

if __name__ == "__main__":
    # 测试代码
    import sys
    import os

    # 添加项目根目录到 Python 路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    from config.settings import settings

    print("=" * 50)
    print("测试 ES 客户端连接")
    print("=" * 50)

    try:
        # 初始化客户端
        es_client = ESClient()

        # 测试索引是否存在
        index_name = settings.ES_INDEX_NAME
        exists = es_client.index_exists(index_name)
        print(f"\n索引 '{index_name}' 是否存在: {exists}")

        # 关闭连接
        es_client.close()

        print("\n✅ 测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
   