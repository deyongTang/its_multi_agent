#!/usr/bin/env python3
"""
生成正确的密码哈希值
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_hash(password: str) -> str:
    """
    生成密码哈希（正确处理 bcrypt 72 字节限制）

    Args:
        password: 明文密码

    Returns:
        加密后的密码哈希值
    """
    # bcrypt 限制密码最长 72 字节，需要截断
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)

if __name__ == "__main__":
    password = "tang@4896"

    print("=" * 60)
    print("生成密码哈希值")
    print("=" * 60)
    print(f"\n明文密码: {password}")
    print(f"密码字节长度: {len(password.encode('utf-8'))} 字节")

    # 生成哈希
    hashed = generate_hash(password)

    print(f"\n生成的哈希值:")
    print(hashed)
    print(f"\n哈希值长度: {len(hashed)} 字符")

    # 验证
    password_bytes = password.encode('utf-8')[:72]
    is_valid = pwd_context.verify(password_bytes, hashed)
    print(f"\n验证结果: {'✅ 成功' if is_valid else '❌ 失败'}")

    print("\n" + "=" * 60)
