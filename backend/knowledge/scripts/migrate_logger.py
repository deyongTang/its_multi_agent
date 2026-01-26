"""
日志迁移脚本

将所有使用 logging 的文件迁移到 loguru
"""

import os
import re
from pathlib import Path


def migrate_file(file_path: Path):
    """迁移单个文件的日志导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        modified = False

        # 1. 替换 import logging
        if 'import logging' in content:
            # 如果已经有 from infrastructure.logger import logger，跳过
            if 'from infrastructure.logger import logger' not in content:
                # 移除 import logging
                content = re.sub(r'import logging\n', '', content)

                # 移除 logging.basicConfig
                content = re.sub(r'logging\.basicConfig\([^)]*\)\n', '', content)

                # 替换 logger = logging.getLogger(__name__)
                content = re.sub(
                    r'logger\s*=\s*logging\.getLogger\([^)]*\)\n',
                    '',
                    content
                )

                # 在合适的位置添加新的导入
                # 找到最后一个 import 语句的位置
                import_lines = []
                lines = content.split('\n')
                last_import_idx = -1

                for idx, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        last_import_idx = idx

                if last_import_idx >= 0:
                    # 在最后一个 import 后添加
                    lines.insert(last_import_idx + 1, 'from infrastructure.logger import logger')
                    content = '\n'.join(lines)
                    modified = True

        # 2. 只有在内容发生变化时才写入
        if modified and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已迁移: {file_path}")
            return True
        else:
            print(f"⏭️  跳过: {file_path} (无需修改)")
            return False

    except Exception as e:
        print(f"❌ 迁移失败: {file_path} - {e}")
        return False


def main():
    """批量迁移所有文件"""
    # 需要迁移的文件列表
    files_to_migrate = [
        "services/es_retrieval_service.py",
        "services/es_ingestion_processor.py",
        "services/text_processor.py",
        "scripts/init_es_index.py",
        "infrastructure/es_client.py",
        "services/embedding_service.py",
        "data_access/vector_store_manager.py",
        "repositories/vector_store_repository.py",
        "business_logic/ingestion_worker_service.py",
        "business_logic/document_sync_service.py",
        "business_logic/file_storage_service.py",
        "data_access/sync_cursor_repository.py",
        "data_access/knowledge_version_repository.py",
        "data_access/knowledge_asset_repository.py",
        "infrastructure/database.py",
    ]

    project_root = Path(__file__).parent.parent
    success_count = 0
    skip_count = 0
    fail_count = 0

    print("🚀 开始迁移日志系统...\n")

    for file_path in files_to_migrate:
        full_path = project_root / file_path
        if full_path.exists():
            result = migrate_file(full_path)
            if result:
                success_count += 1
            else:
                skip_count += 1
        else:
            print(f"⚠️  文件不存在: {full_path}")
            fail_count += 1

    print(f"\n📊 迁移完成:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ⏭️  跳过: {skip_count}")
    print(f"   ❌ 失败: {fail_count}")


if __name__ == '__main__':
    main()
