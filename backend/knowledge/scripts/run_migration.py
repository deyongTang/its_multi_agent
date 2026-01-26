import sys
import os
import pymysql

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import settings

def run_migration():
    print(f"🔌 连接数据库: {settings.DB_HOST}")
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4'
    )
    
    # 手动处理: 因为 DROP PRIMARY KEY 在没有 PK 时会报错，我们先检查结构
    cursor = conn.cursor()
    
    try:
        # 1. 检查 knowledge_asset 主键
        cursor.execute("SHOW KEYS FROM knowledge_asset WHERE Key_name = 'PRIMARY'")
        pk = cursor.fetchone()
        if pk and pk[4] == 'knowledge_no':
            print("⚠️ 发现旧主键 knowledge_no，正在删除...")
            cursor.execute("ALTER TABLE knowledge_asset DROP PRIMARY KEY")
            conn.commit()
        
        # 2. 读取并执行 migration SQL
        sql_path = os.path.join(PROJECT_ROOT, "migrations", "002_add_asset_uuid.sql")
        print(f"🚀 执行迁移脚本: {sql_path}")
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        statements = content.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt: continue
            
            try:
                # 跳过注释行
                if stmt.startswith('--'): continue
                
                cursor.execute(stmt)
                conn.commit()
            except Exception as e:
                print(f"⚠️ 跳过/失败 (可能列已存在): {str(e)[:100]}...")
                
        print("✅ 迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
