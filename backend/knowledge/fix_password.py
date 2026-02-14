#!/usr/bin/env python3
"""
自动修复用户密码脚本
在服务器上运行此脚本即可自动修复密码问题
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from infrastructure.database import get_connection

def fix_password():
    """修复用户密码"""
    print("=" * 60)
    print("开始修复用户密码...")
    print("=" * 60)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 正确的密码哈希值（使用截断后的密码生成）
        correct_hash = '$2b$12$/Xhk1XhKYpgKqQZSvW8Kt.GXSES/fxEL9whj4yMDgZrIcVIH802jy'

        # 更新密码
        sql = """
        UPDATE users
        SET hashed_password = %s
        WHERE username = %s
        """
        cursor.execute(sql, (correct_hash, 'deyong'))
        conn.commit()

        print("\n✅ 密码已更新")

        # 验证更新结果
        cursor.execute("""
            SELECT id, username, email, LENGTH(hashed_password) as hash_len,
                   LEFT(hashed_password, 20) as hash_preview
            FROM users
            WHERE username = %s
        """, ('deyong',))

        result = cursor.fetchone()
        if result:
            print(f"\n用户信息:")
            print(f"  ID: {result[0]}")
            print(f"  用户名: {result[1]}")
            print(f"  邮箱: {result[2]}")
            print(f"  密码哈希长度: {result[3]} (应该是 60)")
            print(f"  密码哈希预览: {result[4]}...")

            if result[3] == 60:
                print("\n✅ 密码修复成功！")
                print("\n现在可以使用以下信息登录:")
                print(f"  用户名: deyong")
                print(f"  密码: tang@4896")
            else:
                print("\n❌ 密码长度不正确，可能需要检查数据库字段长度")
        else:
            print("\n❌ 未找到用户")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    fix_password()
