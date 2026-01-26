# Elasticsearch 日志采集指南

## 概述

本系统支持将日志实时写入 Elasticsearch，便于集中管理、查询和分析。

## 核心功能

✅ **实时写入** - 日志直接写入 ES，无需中间件
✅ **自动索引** - 按日期自动创建索引（app-logs-YYYY.MM.DD）
✅ **结构化存储** - 日志以 JSON 格式存储，便于查询
✅ **TraceId 追踪** - 支持按 traceId 追踪完整请求链路
✅ **异常容错** - ES 故障不影响应用运行

---

## 快速开始

### 1. 创建索引模板

首先创建 ES 索引模板（只需执行一次）：

```bash
cd backend/knowledge
python scripts/init_log_index_template.py
```

输出：
```
✅ 索引模板创建成功: app-logs-template
📋 模板匹配模式: app-logs-*
```

### 2. 启用 ES 日志输出

在 `api/main.py` 中配置：

```python
from infrastructure.logger import setup_logger
from infrastructure.es_client import ESClient

# 初始化 ES 客户端
es_client = ESClient()

# 配置日志系统（启用 ES 输出）
setup_logger(
    log_dir="./logs",
    log_level="INFO",
    enable_es=True,  # 启用 ES 输出
    es_client=es_client.client,
    es_index_prefix="app-logs"
)
```

### 3. 验证日志写入

运行测试脚本验证：

```bash
python examples/test_es_logging.py
```

---

## 日志索引结构

### 索引命名规则

```
app-logs-YYYY.MM.DD
```

示例：
- `app-logs-2026.01.24` - 2026年1月24日的日志
- `app-logs-2026.01.25` - 2026年1月25日的日志

### 文档字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `@timestamp` | date | 日志时间戳（Unix 时间戳） |
| `level` | keyword | 日志级别（INFO, WARNING, ERROR 等） |
| `message` | text | 日志消息内容 |
| `trace_id` | keyword | 请求追踪 ID |
| `module` | keyword | 模块名 |
| `function` | keyword | 函数名 |
| `line` | integer | 代码行号 |
| `file_path` | keyword | 文件路径 |
| `process_id` | integer | 进程 ID |
| `thread_id` | long | 线程 ID |
| `exception` | object | 异常信息（可选） |

---

## 查询示例

### 1. 查询所有日志

```python
from infrastructure.es_client import ESClient
from datetime import datetime

es_client = ESClient()
today = datetime.now().strftime("%Y.%m.%d")
index_name = f"app-logs-{today}"

query = {
    "query": {"match_all": {}},
    "size": 10,
    "sort": [{"@timestamp": "desc"}]
}

results = es_client.search(index_name=index_name, query=query)
```

### 2. 按 TraceId 查询（追踪完整请求链路）

```python
query = {
    "query": {
        "match": {
            "trace_id": "87d63199-cf89-4efa-99a3-6350fe1bbe3c"
        }
    },
    "sort": [{"@timestamp": "asc"}]
}

results = es_client.search(index_name=index_name, query=query)
```

### 3. 按日志级别查询

```python
# 查询所有错误日志
query = {
    "query": {
        "term": {
            "level": "ERROR"
        }
    },
    "size": 50
}

results = es_client.search(index_name=index_name, query=query)
```

### 4. 按时间范围查询

```python
query = {
    "query": {
        "range": {
            "@timestamp": {
                "gte": "now-1h",  # 最近1小时
                "lte": "now"
            }
        }
    }
}

results = es_client.search(index_name=index_name, query=query)
```

### 5. 全文搜索

```python
# 搜索包含特定关键词的日志
query = {
    "query": {
        "match": {
            "message": "用户操作"
        }
    }
}

results = es_client.search(index_name=index_name, query=query)
```

---

## Kibana 可视化

### 1. 创建索引模式

在 Kibana 中创建索引模式：

1. 打开 Kibana: `http://localhost:5601`
2. 进入 **Management** → **Index Patterns**
3. 创建索引模式: `app-logs-*`
4. 选择时间字段: `@timestamp`

### 2. 查看日志

进入 **Discover** 页面，即可查看和搜索日志。

### 3. 常用查询语法

```
# 按级别过滤
level: ERROR

# 按 TraceId 过滤
trace_id: "87d63199-cf89-4efa-99a3-6350fe1bbe3c"

# 按模块过滤
module: "api.routers"

# 组合查询
level: ERROR AND module: "api.routers"
```

---

## 性能优化

### 1. 索引生命周期管理（ILM）

建议配置 ILM 策略自动管理日志索引：

```json
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "1d"
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### 2. 批量写入优化

如果日志量很大，可以启用批量写入（修改 `es_logger_handler.py`）：

```python
# 累积 100 条日志后批量写入
batch_size = 100
```

---

## 故障排查

### 问题 1: 日志未写入 ES

**检查步骤：**

1. 确认 ES 连接正常
```bash
curl http://localhost:9200
```

2. 检查索引是否存在
```bash
curl http://localhost:9200/_cat/indices?v | grep app-logs
```

3. 查看日志系统初始化信息
```
✅ ES 日志输出已启用 | 索引前缀: app-logs
```

### 问题 2: 查询不到日志

**可能原因：**

1. ES 索引刷新延迟（默认 5 秒）
2. 索引名称不匹配
3. 时间字段格式问题

**解决方案：**

```python
# 手动刷新索引
es_client.client.indices.refresh(index=index_name)
```

---

## 最佳实践

### 1. 日志级别设置

- **开发环境**: `DEBUG` - 查看详细信息
- **测试环境**: `INFO` - 记录关键流程
- **生产环境**: `WARNING` - 只记录警告和错误

### 2. 敏感信息处理

避免在日志中记录敏感信息：

```python
# ❌ 不推荐
logger.info(f"用户登录: {username} / {password}")

# ✅ 推荐
logger.info(f"用户登录: {username}")
```

### 3. 日志保留策略

建议配置：
- **热数据**: 7 天（快速查询）
- **温数据**: 30 天（归档存储）
- **删除**: 30 天后自动删除

---

## 参考资料

- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Kibana 用户指南](https://www.elastic.co/guide/en/kibana/current/index.html)
- [loguru 文档](https://loguru.readthedocs.io/)
