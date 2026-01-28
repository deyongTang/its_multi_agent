#!/usr/bin/env python
"""诊断 settings 加载问题"""

import sys
import os

print("=" * 60)
print("Settings 加载诊断")
print("=" * 60)

# 1. 检查工作目录
print(f"\n1. 当前工作目录: {os.getcwd()}")

# 2. 检查 .env 文件
from pathlib import Path
env_file = Path(".env")
print(f"2. .env 文件存在: {env_file.exists()}")
if env_file.exists():
    print(f"   .env 文件路径: {env_file.absolute()}")

# 3. 导入 settings
print("\n3. 导入 settings...")
from config.settings import settings

# 4. 检查 settings 对象
print(f"4. settings 对象类型: {type(settings)}")
print(f"   settings 对象 ID: {id(settings)}")

# 5. 检查属性访问方式
print("\n5. 测试不同的属性访问方式:")

# 方式 1: 直接访问
try:
    value = settings.LANGCHAIN_TRACING_V2
    print(f"   直接访问 settings.LANGCHAIN_TRACING_V2: {value}")
except AttributeError as e:
    print(f"   直接访问失败: {e}")

# 方式 2: getattr
value = getattr(settings, 'LANGCHAIN_TRACING_V2', 'NOT_FOUND')
print(f"   getattr(settings, 'LANGCHAIN_TRACING_V2', 'NOT_FOUND'): {value}")

# 方式 3: hasattr
has_attr = hasattr(settings, 'LANGCHAIN_TRACING_V2')
print(f"   hasattr(settings, 'LANGCHAIN_TRACING_V2'): {has_attr}")

# 方式 4: __dict__
print(f"\n6. settings.__dict__ 中的键:")
for key in sorted(settings.__dict__.keys()):
    if not key.startswith('_'):
        print(f"   - {key}")

# 7. 检查 model_fields
print(f"\n7. settings.model_fields 中的键:")
if hasattr(settings, 'model_fields'):
    for key in sorted(settings.model_fields.keys()):
        print(f"   - {key}")

# 8. 尝试访问所有关键配置
print(f"\n8. 尝试访问关键配置:")
keys_to_check = [
    'LANGCHAIN_TRACING_V2',
    'LANGCHAIN_API_KEY',
    'DASHSCOPE_BASE_URL',
    'BAIDUMAP_AK',
]

for key in keys_to_check:
    try:
        value = getattr(settings, key)
        print(f"   ✅ {key}: {value}")
    except AttributeError:
        print(f"   ❌ {key}: AttributeError")

print("\n" + "=" * 60)
