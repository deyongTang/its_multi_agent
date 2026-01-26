import os.path
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool

from services.ingestion.ingestion_processor import IngestionProcessor
from schemas.schema import UploadResponse, QueryRequest, QueryResponse
from services.retrieval_service import RetrievalService
from business_logic.query_service import QueryService

from infrastructure.es_client import ESClient
from services.es_ingestion_processor import ESIngestionProcessor
from services.es_retrieval_service import ESRetrievalService

# 引入业务服务
from business_logic.document_sync_service import DocumentSyncService
from business_logic.crawler_service import CrawlerService
from business_logic.ingestion_worker_service import IngestionWorkerService
from datetime import datetime

# 使用新的日志系统
from infrastructure.logger import logger

from fastapi import BackgroundTasks

# 1.创建APIRouter
router = APIRouter()

# ... (existing code)

# --- 任务调度接口 (Task Endpoints) ---

def _run_crawl_task(start_id: int, end_id: int):
    """
    [后台任务] 执行爬虫任务
    Pipeline 1: Crawler -> OSS
    步骤: 抓取 -> 清洗 -> 存入 MinIO -> 数据库标记为 NEW
    """
    logger.info(f"🚀 [后台任务启动] 爬虫任务: ID {start_id} 到 {end_id}")
    crawler = CrawlerService()
    crawler.crawl_range(start_id, end_id)
    logger.info("✅ [后台任务完成] 爬虫任务结束")

@router.post("/tasks/crawl", summary="触发后台爬虫任务 (Pipeline 1)")
async def trigger_crawl_task(
    background_tasks: BackgroundTasks,
    start_id: int = 1,
    end_id: int = 100
):
    """
    启动后台爬虫任务 (Pipeline 1: Crawler -> OSS)
    
    - **start_id**: 起始知识点 ID
    - **end_id**: 结束知识点 ID
    
    此接口会立即返回，并在后台异步执行抓取逻辑。
    """
    background_tasks.add_task(_run_crawl_task, start_id, end_id)
    return {
        "status": "accepted",
        "message": f"爬虫任务已提交 (Range: {start_id}-{end_id})",
        "task_type": "crawler"
    }

def _run_ingestion_task(batch_size: int, retry: bool):
    """
    [后台任务] 执行入库任务
    Pipeline 2: MinIO -> ES
    步骤: 扫描 NEW 文档 -> 下载 -> 切分/向量化 -> 写入 ES -> 标记为 INGESTED
    """
    logger.info(f"🚀 [后台任务启动] 入库任务 (Batch: {batch_size}, Retry: {retry})")
    worker = IngestionWorkerService()
    
    # 1. 处理状态为 NEW 的新文档
    worker.process_pending_documents(batch_size=batch_size)
    
    # 2. (可选) 重试状态为 FAILED 的文档
    if retry:
        worker.retry_failed_documents()
        
    logger.info("✅ [后台任务完成] 入库任务结束")

@router.post("/tasks/ingest", summary="触发后台入库任务 (Pipeline 2)")
async def trigger_ingest_task(
    background_tasks: BackgroundTasks,
    batch_size: int = 100,
    retry: bool = False
):
    """
    启动后台入库任务 (Pipeline 2: MinIO -> ES)
    
    - **batch_size**: 本次处理的文档数量
    - **retry**: 是否重试之前失败的任务
    
    此接口会立即返回，并在后台异步执行入库逻辑。
    """
    background_tasks.add_task(_run_ingestion_task, batch_size, retry)
    return {
        "status": "accepted",
        "message": "入库任务已提交",
        "task_type": "ingestion"
    }

@router.post("/test/upload_to_oss", summary="测试：上传文件到 MinIO 并注册资产")
async def test_upload_to_oss(
    file: UploadFile = File(...),
    knowledge_no: str = "test-001"
):
    """
    测试接口：上传文件到 MinIO 并注册到数据库 (状态: NEW)
    用于验证 'Crawler -> OSS' 链路
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 初始化服务
        sync_service = DocumentSyncService()
        
        # 执行上传
        result = await run_in_threadpool(
            sync_service.upload_document,
            file_content=content,
            knowledge_no=knowledge_no,
            source_update_time=datetime.now()
        )
        
        return {
            "status": "success",
            "message": "文件已上传到 MinIO",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"测试上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 2. 延迟初始化服务实例（避免在导入时创建，此时环境变量可能未设置）
_ingestion_processor = None
_retrieval_service = None
_query_service = None
_es_ingestion_processor = None
_es_retrieval_service = None


def get_ingestion_processor():
    global _ingestion_processor
    if _ingestion_processor is None:
        _ingestion_processor = IngestionProcessor()
    return _ingestion_processor


def get_retrieval_service():
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


def get_query_service():
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service


def get_es_ingestion_processor():
    global _es_ingestion_processor
    if _es_ingestion_processor is None:
        _es_ingestion_processor = ESIngestionProcessor()
    return _es_ingestion_processor


def get_es_retrieval_service():
    global _es_retrieval_service
    if _es_retrieval_service is None:
        _es_retrieval_service = ESRetrievalService()
    return _es_retrieval_service


# IO(对文件读写) 执行SQL 网络请求 典型耗时任务
@router.post("/upload", response_model=UploadResponse, summary="处理知识库上传")
async def upload_file(file: UploadFile = File(...)):
    # "0430-联想手机K900常见问题汇总.md"
    temp_file_path = ""

    try:
        # 检查文件名是否存在
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        file_suffix = os.path.splitext(file.filename)[1]
        # 1. 处理临时文件
        async with aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=file_suffix
        ) as temp_file:

            # a. 读取上传文件的内容 # 对象（异步协程）缓冲区【1M】空间
            while content := await file.read(1024 * 1024):
                # b. 将读取到上传文件的内容写入到临时文件
                await temp_file.write(content)

            # c. 获取临时文件的路径 # C:\Users\Administrator\AppData\Local\Temp\tmpe1puxhk7
            temp_file_path = str(temp_file.name)

        # 2. 磁盘写入完成,入库操作  # TODO(去重)
        chunks_added = await run_in_threadpool(
            get_ingestion_processor().ingest_file, temp_file_path
        )
        print(f"临时文件路径:{temp_file_path}")

        # 3.构建文件上传的响应对象
        return UploadResponse(
            status="success",
            message="文档上传知识库成功",
            file_name=file.filename,
            chunks_added=chunks_added,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传到知识库失败:{str(e)}")

    finally:
        # 4. 清空临时文件路径(磁盘空间不足)
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"临时文件:{temp_file_path}已删除...")


@router.post("/upload_es", response_model=UploadResponse, summary="上传文档到 Elasticsearch")
async def upload_file_to_es(file: UploadFile = File(...)):
    """
    上传文档到 Elasticsearch（N+1 存储模式）
    - N 个切片用于搜索（带向量）
    - 1 个全文用于展示
    """
    temp_file_path = ""

    try:
        # 1. 检查文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        file_suffix = os.path.splitext(file.filename)[1]

        # 2. 保存临时文件
        async with aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=file_suffix
        ) as temp_file:
            while content := await file.read(1024 * 1024):
                await temp_file.write(content)
            temp_file_path = str(temp_file.name)

        logger.info(f"📁 临时文件已保存: {temp_file_path}")

        # 3. 生成稳定的 knowledge_no (基于原始文件名)
        # 即使每次上传生成不同的临时文件路径，只要原始文件名相同，ID 就相同
        import hashlib
        knowledge_no = hashlib.md5(file.filename.encode('utf-8')).hexdigest()
        logger.info(f"🔑 生成 stable ID: {knowledge_no} (from {file.filename})")

        # 4. 调用 ES 入库处理器
        chunks_added = await run_in_threadpool(
            get_es_ingestion_processor().ingest_file,
            temp_file_path,
            os.path.splitext(file.filename)[0],  # 使用文件名作为标题
            knowledge_no  # 传入稳定的 ID
        )

        # 5. 返回响应
        return UploadResponse(
            status="success",
            message="文档已成功上传到 Elasticsearch",
            file_name=file.filename,
            chunks_added=chunks_added,
        )

    except Exception as e:
        logger.error(f"❌ 文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    finally:
        # 6. 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"🗑️ 临时文件已删除: {temp_file_path}")


@router.post("/query", summary="查询知识库（流式输出）")
async def query_knowledge(request: QueryRequest):
    """
    流式查询知识库接口
    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    async def generate_stream():
        """生成流式响应的异步生成器"""
        try:
            logger.info(f"🔎 原始问题: {request.question}")

            # 1. 查询重写 (利用 LLM 优化检索词)
            query_service = get_query_service()
            rewritten_query = await run_in_threadpool(query_service.rewrite_query, request.question)

            logger.info(f"✨ 重写后问题: {rewritten_query}")

            # 2. 使用 ES 混合检索（新方案 - RAG V2.0）
            es_results = await run_in_threadpool(
                get_es_retrieval_service().retrieve,
                rewritten_query,
                top_k=5,  # 限制为 5 个文档
                return_full_content=True
            )

            # 将 ES 结果转换为 LangChain Document 格式
            from langchain_core.documents import Document
            docs = [
                Document(
                    page_content=result.get("full_content", result.get("content", "")),
                    metadata={
                        "knowledge_no": result.get("knowledge_no"),
                        "title": result.get("title"),
                        "score": result.get("score", 0)
                    }
                )
                for result in es_results
            ]

            logger.info(f"📚 ES 检索到 {len(docs)} 个文档")
            logger.info(f"🤖 开始生成答案 | 上下文文档数: {len(docs)}")

            # 3. 流式生成答案
            for chunk in query_service.generate_answer_stream(request.question, docs):
                # 以 SSE 格式输出
                yield f"data: {chunk}\n\n"

            logger.info("✅ 答案生成完成")

        except Exception as e:
            logger.error(f"❌ 查询出错: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@router.get("/es", summary="测试 ES 连接")
def testEs():
    """测试 Elasticsearch 连接和查询功能"""
    try:
        es_client = ESClient()
        index_name = "test_index"

        # ES 8.x 正确的查询格式：完整的查询 DSL
        query = {
            "query": {
                "match_all": {}
            }
        }

        results = es_client.search(index_name=index_name, query=query)
        print("搜索结果:", results)

        # 返回测试结果
        return {
            "status": "success",
            "message": "ES 连接测试成功",
            "results": results
        }
    except Exception as e:
        print(f"ES 测试失败: {e}")
        return {
            "status": "error",
            "message": f"ES 连接测试失败: {str(e)}"
        }