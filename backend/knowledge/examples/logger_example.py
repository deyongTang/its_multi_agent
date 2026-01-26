"""
日志系统使用示例

演示如何在不同场景下使用日志系统
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.logger import logger, setup_logger, set_trace_id
import uuid


def example_basic_logging():
    """示例 1: 基本日志使用"""
    logger.info("=" * 50)
    logger.info("示例 1: 基本日志使用")
    logger.info("=" * 50)

    logger.debug("这是 DEBUG 级别日志 - 用于调试信息")
    logger.info("这是 INFO 级别日志 - 用于正常业务流程")
    logger.warning("这是 WARNING 级别日志 - 用于警告信息")
    logger.error("这是 ERROR 级别日志 - 用于错误信息")
    logger.critical("这是 CRITICAL 级别日志 - 用于严重错误")


def example_with_variables():
    """示例 2: 带变量的日志"""
    logger.info("\n" + "=" * 50)
    logger.info("示例 2: 带变量的日志")
    logger.info("=" * 50)

    user_id = 12345
    username = "张三"
    action = "上传文件"

    logger.info(f"👤 用户操作 | ID: {user_id} | 用户名: {username} | 操作: {action}")

    file_name = "测试文档.pdf"
    file_size = 1024 * 512  # 512 KB
    chunks = 15

    logger.info(
        f"📁 文件处理 | 文件名: {file_name} | "
        f"大小: {file_size / 1024:.2f}KB | 切片数: {chunks}"
    )


def example_with_trace_id():
    """示例 3: 使用 TraceId"""
    logger.info("\n" + "=" * 50)
    logger.info("示例 3: 使用 TraceId")
    logger.info("=" * 50)

    # 模拟处理 3 个请求
    for i in range(3):
        # 为每个请求生成唯一的 traceId
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)

        logger.info(f"📥 请求 {i + 1} 开始处理")
        logger.info(f"🔍 查询数据库")
        logger.info(f"✅ 请求 {i + 1} 处理完成")


def example_exception_handling():
    """示例 4: 异常处理"""
    logger.info("\n" + "=" * 50)
    logger.info("示例 4: 异常处理")
    logger.info("=" * 50)

    # 示例 4.1: 捕获并记录异常
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"❌ 计算错误: {e}")

    # 示例 4.2: 记录完整的异常堆栈
    try:
        data = {"name": "test"}
        value = data["age"]  # KeyError
    except KeyError as e:
        logger.exception(f"❌ 数据访问错误: {e}")  # 使用 exception 记录完整堆栈


def example_structured_logging():
    """示例 5: 结构化日志"""
    logger.info("\n" + "=" * 50)
    logger.info("示例 5: 结构化日志（推荐）")
    logger.info("=" * 50)

    # 模拟文件上传流程
    logger.info("🚀 开始文件上传流程")

    logger.info("📥 步骤 1/4 | 接收文件")
    logger.info("💾 步骤 2/4 | 保存临时文件")
    logger.info("🔄 步骤 3/4 | 文档切分与向量化")
    logger.info("✅ 步骤 4/4 | 入库完成")

    logger.info("🎉 文件上传流程完成")


def main():
    """主函数"""
    # 初始化日志系统
    setup_logger(
        log_dir="./logs",
        log_level="DEBUG",  # 设置为 DEBUG 以查看所有日志
        rotation="00:00",
        retention="7 days",
        enable_json=False
    )

    logger.info("🚀 日志系统示例程序启动")

    # 运行各个示例
    example_basic_logging()
    example_with_variables()
    example_with_trace_id()
    example_exception_handling()
    example_structured_logging()

    logger.info("\n" + "=" * 50)
    logger.info("✅ 所有示例运行完成")
    logger.info("=" * 50)
    logger.info(f"📂 日志文件已保存到: {Path('./logs').absolute()}")


if __name__ == '__main__':
    main()
