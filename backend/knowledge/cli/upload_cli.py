

from repositories.file_repository import FileRepository
from services.ingestion.ingestion_processor import IngestionProcessor
from config.settings import settings

from tqdm import tqdm
import  time


def  main():

    print("1.批量将文档存储到向量数据库...")

    file_repository=FileRepository()

    files_path=file_repository.list_files(settings.CRAWL_OUTPUT_DIR)
    print(f"2.扫描到指定目录下的文件数:{len(files_path)}")

    unique_files_path=file_repository.remove_duplicate_files(files_path)
    print(f"3.扫描到指定目录下的唯一的文件数:{len(unique_files_path)}")

    ingestion_processor=IngestionProcessor()
    success=0
    fail=0


    start_time=time.time()
    with tqdm(unique_files_path,desc="知识库上传进度统计") as pbar:  # 包装器思想
        for unique_file_path in pbar:
            try:
                ingestion_processor.ingest_file(unique_file_path)
                success += 1
            except Exception as e:
                fail += 1
            finally:
                pbar.set_postfix({"success": success, "fail": fail})

    end_time = time.time()

    total_time=end_time-start_time

    print(f"4.最终入库成功的结果:成功:{success}--->失败:{fail}")
    print(f"5. 最终入库成功的耗时:{total_time:.2f}s")




if __name__ == '__main__':
    main()


















