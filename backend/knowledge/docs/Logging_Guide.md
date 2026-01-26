# 日志系统使用指南

## 概述

本项目使用 **loguru** 作为日志框架，提供以下核心功能：

1. ✅ **TraceId 追踪** - 每个请求自动生成唯一 ID，便于链路追踪
2. ✅ **文件输出** - 日志自动写入文件，按日期轮转
3. ✅ **彩色输出** - 控制台日志带颜色，易于阅读
4. ✅ **结构化日志** - 支持 JSON 格式，便于日志采集系统解析
5. ✅ **异常追踪** - 自动记录完整的异常堆栈和变量值

---

## 快速开始

### 1. 安装依赖

```bash
pip install loguru
```

### 2. 在代码中使用日志

```python
from infrastructure.logger import logger

# 基本使用
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")

# 带变量的日志
user_id = 12345
logger.info(f"用户 {user_id} 登录成功")

# 异常日志（自动记录堆栈）
try:
    result = 1 / 0
except Exception as e:
    logger.exception(f"计算出错: {e}")
```

---

## TraceId 使用

### 自动注入（推荐）

FastAPI 中间件会自动为每个请求生成 traceId：

```python
# 在 main.py 中已配置
app.add_middleware(TraceIdMiddleware)
```

每个请求的日志都会自动包含 traceId：

```
2026-01-24 10:30:15.123 | INFO     | traceId=a1b2c3d4-e5f6-7890 | api.routers:upload_file:147 - 📁 临时文件已保存
```

### 手动设置 TraceId

在非 HTTP 请求场景（如定时任务、CLI 工具）：

```python
from infrastructure.logger import logger, set_trace_id
import uuid

# 生成并设置 traceId
trace_id = str(uuid.uuid4())
set_trace_id(trace_id)

logger.info("开始执行定时任务")
```

### 获取当前 TraceId

```python
from infrastructure.logger import get_trace_id

current_trace_id = get_trace_id()
print(f"当前请求 ID: {current_trace_id}")
```

---

## 日志级别

loguru 支持以下日志级别（从低到高）：

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| `DEBUG` | 调试信息，详细的执行流程 | `logger.debug("SQL 查询: SELECT * FROM users")` |
| `INFO` | 正常的业务流程 | `logger.info("用户登录成功")` |
| `WARNING` | 警告信息，不影响运行 | `logger.warning("缓存未命中，使用数据库查询")` |
| `ERROR` | 错误信息，需要关注 | `logger.error("文件上传失败")` |
| `CRITICAL` | 严重错误，系统可能崩溃 | `logger.critical("数据库连接失败")` |

---

## 日志文件

### 文件位置

日志文件默认保存在 `./logs/` 目录：

```
logs/
├── app_2026-01-24.log       # 所有级别的日志
├── error_2026-01-24.log     # 仅 ERROR 及以上级别
└── app_2026-01-24.json      # JSON 格式（可选）
```

### 文件轮转策略

- **按时间轮转**: 每天午夜 00:00 自动创建新文件
- **保留时间**: 默认保留 30 天
- **自动清理**: 超过保留期的日志自动删除

### 自定义配置

在 `main.py` 中修改 `setup_logger()` 参数：

```python
setup_logger(
    log_dir="./logs",           # 日志目录
    log_level="INFO",           # 日志级别
    rotation="00:00",           # 轮转策略（时间）
    # rotation="500 MB",        # 或按大小轮转
    retention="30 days",        # 保留时间
    enable_json=False           # 是否启用 JSON 格式
)
```

---

## 最佳实践

### 1. 使用结构化日志

❌ **不推荐**：
```python
logger.info("用户123上传了文件abc.txt，大小456KB")
```

✅ **推荐**：
```python
logger.info(f"📁 文件上传 | 用户: {user_id} | 文件: {filename} | 大小: {size}KB")
```

### 2. 使用 Emoji 增强可读性

```python
logger.info("🚀 服务启动成功")
logger.info("📥 收到请求")
logger.info("📤 返回响应")
logger.warning("⚠️ 缓存未命中")
logger.error("❌ 操作失败")
```

### 3. 记录关键业务节点

```python
@router.post("/upload")
async def upload_file(file: UploadFile):
    logger.info(f"📥 开始上传 | 文件: {file.filename}")

    # 业务逻辑
    chunks_added = process_file(file)

    logger.info(f"✅ 上传完成 | 文件: {file.filename} | 切片数: {chunks_added}")
```

### 4. 异常处理

```python
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"❌ 参数错误: {e}")
    raise
except Exception as e:
    logger.exception(f"❌ 未知错误: {e}")  # 自动记录堆栈
    raise
```

---

## 接入日志采集系统

### 方案 1: 文件采集（推荐）

使用 Filebeat、Fluentd 等工具采集日志文件：

```yaml
# filebeat.yml 示例
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /path/to/logs/app_*.log
    fields:
      service: its-knowledge-platform
```

### 方案 2: JSON 格式输出

启用 JSON 格式便于 ELK/Loki 解析：

```python
setup_logger(
    enable_json=True  # 启用 JSON 格式
)
```

JSON 日志示例：
```json
{
  "text": "文件上传成功",
  "record": {
    "time": {"timestamp": 1706054400},
    "level": {"name": "INFO"},
    "extra": {"trace_id": "a1b2c3d4-e5f6-7890"},
    "file": {"name": "routers.py", "path": "/app/api/routers.py"},
    "line": 147
  }
}
```

---

## 常见问题

### Q1: 如何在分布式系统中传递 traceId？

在调用下游服务时，将 traceId 放入请求头：

```python
import httpx
from infrastructure.logger import get_trace_id

async def call_downstream_service():
    trace_id = get_trace_id()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://downstream-service/api",
            headers={"X-Trace-Id": trace_id}
        )
```

### Q2: 如何临时提高日志级别？

修改 `main.py` 中的 `log_level` 参数：

```python
setup_logger(log_level="DEBUG")  # 临时开启 DEBUG 级别
```

### Q3: 日志文件太大怎么办？

使用按大小轮转：

```python
setup_logger(
    rotation="500 MB",  # 每 500MB 创建新文件
    retention="10 days"  # 只保留 10 天
)
```

---

## 迁移指南

如果你的代码还在使用 `logging` 模块，可以使用迁移脚本：

```bash
python scripts/migrate_logger.py
```

脚本会自动：
1. 移除 `import logging`
2. 移除 `logging.basicConfig()`
3. 移除 `logger = logging.getLogger(__name__)`
4. 添加 `from infrastructure.logger import logger`

---

## 参考资料

- [loguru 官方文档](https://loguru.readthedocs.io/)
- [FastAPI 中间件文档](https://fastapi.tiangolo.com/tutorial/middleware/)
