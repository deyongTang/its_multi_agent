from langchain_chroma import Chroma
from config.settings import settings
from langchain_openai.embeddings import OpenAIEmbeddings
from infrastructure.logger import logger


class VectorStoreRepository:
    """
     作用：对向量数据库做场景读写

    """

    def __init__(self):
        """
        创建向量数据库实例
        创建嵌入模型的实例
        向量数据库能力: 1.存储向量数据 2.搜索能力（向量数据库检索器）

        注意：环境变量由 main.py 统一设置，这里直接使用
        """
        self._embedding = None
        self._vector_database = None

    @property
    def embedding(self):
        """延迟初始化 embedding"""
        if self._embedding is None:
            self._embedding = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL
            )
        return self._embedding

    @property
    def vector_database(self):
        """延迟初始化 vector_database"""
        if self._vector_database is None:
            self._vector_database = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                collection_name="its-knowledge",
                embedding_function=self.embedding
            )
        return self._vector_database


    def  add_documents(self,documents:list,batch_size:int=16)->int:
        """
        将切分之后的文档块保存到向量数据库中

        Args:
            documents: 切分之后的文档块
            batch_size: 分批保存文档块的批次大小

        Returns:
            int:成功添加到向量数据库中文档块的数量(服务前端展示)

        """

        # 1. 获取到文档块的总数量
        total_documents_chunks=len(documents)

        # 2. 分批次保存
        # 场景：documents:[1,2,3,4,5] batch_size:2 遍历3次 第一次取到[1,2]  第二次取到[3,4]    第三次取到[5]
        documents_chunks_added=0
        try:
            for i in range(0,total_documents_chunks,batch_size):
                bath=documents[i:batch_size+i]
                self.vector_database.add_documents(bath)
                documents_chunks_added=documents_chunks_added+len(bath)
                logger.info(f"成功将文档块:{documents_chunks_added}/{total_documents_chunks}保存到向量数据库...")
            return documents_chunks_added
        except Exception as e:
            logger.error(f"文档块列表:{documents}保存到向量数据库失败: {str(e)}")
            raise e















