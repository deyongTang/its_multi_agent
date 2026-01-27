"""
数据库初始化脚本
用于创建用户表
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.database import get_connection
from infrastructure.logger import logger


def init_users_table():
    """初始化用户表"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 创建用户表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
            email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
            hashed_password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
            is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活 1-激活 0-禁用',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
        """

        cursor.execute(create_table_sql)
        conn.commit()

        logger.info("✅ 用户表创建成功")
        print("✅ 用户表创建成功")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ 创建用户表失败: {e}")
        print(f"❌ 创建用户表失败: {e}")
        raise e
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("开始初始化数据库...")
    init_users_table()
    print("数据库初始化完成!")
