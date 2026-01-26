import sys
import os
import pymysql

# 将项目根目录添加到 python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import settings
from infrastructure.logger import logger

def init_database():
    """初始化数据库和表结构"""
    
    print(f"🔌 正在连接数据库: {settings.DB_HOST}:{settings.DB_PORT} (User: {settings.DB_USER})")

    # 1. 连接 MySQL Server (不指定 DB) 以创建数据库
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # 创建数据库
            db_name = settings.DB_NAME
            print(f"🛠️  检查并创建数据库: {db_name}")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return

    # 2. 连接指定数据库并执行建表脚本
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset='utf8mb4'
        )
        
        sql_file_path = os.path.join(PROJECT_ROOT, "migrations", "001_create_sync_tables.sql")
        print(f"📂 读取 SQL 文件: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 简单的 SQL 分割逻辑 (按分号分割)
        # 注意: 如果 SQL 内容中有分号字符串，这种分割会出错，但当前脚本是安全的
        statements = sql_content.split(';')
        
        with conn.cursor() as cursor:
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                
                try:
                    # 打印正在执行的语句前缀
                    print(f"   -> 执行 SQL: {stmt[:30].replace(chr(10), ' ')}...")
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"   ⚠️ SQL 执行警告: {e}")
                    # 通常 CREATE TABLE IF NOT EXISTS 不会报错，但如果有语法错误会在这里抛出
                    raise e
                    
        conn.commit()
        conn.close()
        print("✅ 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化表结构失败: {e}")

if __name__ == "__main__":
    # 确保依赖已安装
    # os.system("pip install pymysql") 
    init_database()
