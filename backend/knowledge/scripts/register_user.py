"""
用户注册脚本
用于后台管理员通过命令行注册用户
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from business_logic.auth_service import AuthService
from infrastructure.logger import logger


def register_user():
    """注册新用户"""
    print("=" * 50)
    print("ITS 知识库管理系统 - 用户注册")
    print("=" * 50)

    # 获取用户输入
    username = input("请输入用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        return

    email = input("请输入邮箱: ").strip()
    if not email:
        print("❌ 邮箱不能为空")
        return

    password = input("请输入密码: ").strip()
    if not password:
        print("❌ 密码不能为空")
        return

    if len(password) < 6:
        print("❌ 密码长度不能少于6位")
        return

    confirm_password = input("请再次输入密码: ").strip()
    if password != confirm_password:
        print("❌ 两次输入的密码不一致")
        return

    # 注册用户
    print("\n正在注册用户...")
    auth_service = AuthService()
    result = auth_service.register(username, email, password)

    if result:
        print(f"\n✅ 用户注册成功!")
        print(f"用户ID: {result['id']}")
        print(f"用户名: {result['username']}")
        print(f"邮箱: {result['email']}")
    else:
        print("\n❌ 用户注册失败,用户名可能已存在")


if __name__ == "__main__":
    try:
        register_user()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.error(f"用户注册失败: {e}")
