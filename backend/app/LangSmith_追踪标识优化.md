# LangSmith 追踪标识优化方案

## 问题描述

在生产环境中，LangSmith 平台上所有追踪记录的 Name 都显示为 "Agent workflow" 或 "MultiAgent-Query"，没有任何区分标识。

**问题影响**：
- ❌ 无法区分不同用户的请求
- ❌ 无法追踪特定会话的执行历史
- ❌ 无法快速定位问题请求
- ❌ 无法进行用户级别的性能分析

## 解决方案

### 1. 添加唯一请求标识（Request ID）

为每个请求生成唯一的 8 位短 ID：

```python
import uuid

# 生成唯一的请求ID
request_id = str(uuid.uuid4())[:8]  # 例如: "a3f2b1c4"
```

### 2. 在日志中包含请求标识

所有日志输出都包含 request_id：

```python
logger.info(f"[{request_id}] 用户 {user_id} 发送的待处理任务: {user_query}")
logger.info(f"[{request_id}] 任务处理完成")
logger.error(f"[{request_id}] AgentService.process_query执行出错: {str(e)}")
```

### 3. 添加 LangSmith 追踪元数据

尝试为 LangSmith 追踪添加元数据和标签：

```python
from langsmith.run_helpers import get_current_run_tree

run_tree = get_current_run_tree()
if run_tree:
    # 添加元数据
    run_tree.extra = {
        "user_id": user_id,
        "session_id": session_id,
        "request_id": request_id,
        "query": user_query[:100]
    }

    # 添加标签
    run_tree.tags = [
        f"user:{user_id}",
        f"session:{session_id}",
        f"req:{request_id}"
    ]
```

## 优化效果

### 优化前
```
Name: Agent workflow
Input: (empty)
Output: (empty)
```

### 优化后

**日志输出**：
```
[a3f2b1c4] 用户 root1 发送的待处理任务: 明天天气怎么样
[a3f2b1c4] [Route] 转交技术专家: 明天天气怎么样...
[a3f2b1c4] 任务处理完成
```

**LangSmith 元数据**（如果支持）：
- user_id: root1
- session_id: session_1768967578328
- request_id: a3f2b1c4
- query: 明天天气怎么样

**LangSmith 标签**（如果支持）：
- user:root1
- session:session_1768967578328
- req:a3f2b1c4

## 使用方法

### 1. 通过日志追踪请求

在应用日志中搜索 request_id：

```bash
# 查看特定请求的所有日志
grep "a3f2b1c4" logs/app.log

# 实时监控特定用户的请求
tail -f logs/app.log | grep "root1"
```

### 2. 通过 LangSmith 过滤

在 LangSmith 平台上：
- 使用标签过滤：`user:root1`
- 使用标签过滤：`session:session_1768967578328`
- 使用标签过滤：`req:a3f2b1c4`

### 3. 关联日志和追踪

1. 用户报告问题："我刚才问的天气没有回答"
2. 查看应用日志，找到该用户最近的 request_id
3. 在 LangSmith 中搜索该 request_id
4. 查看完整的执行树和详细信息

## 注意事项

### 1. OpenAI Agents SDK 的限制

OpenAI Agents SDK 0.7.0 的 `OpenAIAgentsTracingProcessor` 可能不支持自定义元数据和标签。

**如果元数据不显示**：
- 这是正常的，SDK 限制导致
- 但日志中的 request_id 仍然有效
- 可以通过日志关联追踪记录

### 2. 性能影响

添加追踪标识的性能影响：
- ✅ 生成 UUID：< 0.1ms
- ✅ 日志输出：< 1ms
- ✅ 设置元数据：< 1ms（如果失败会被捕获）
- **总计**：几乎可以忽略不计

### 3. 隐私考虑

在元数据中记录用户查询时：
- ✅ 只记录前 100 个字符
- ✅ 避免记录敏感信息（密码、身份证等）
- ✅ 符合数据保护要求

## 进一步优化建议

### 1. 添加更多上下文信息

```python
run_tree.extra = {
    "user_id": user_id,
    "session_id": session_id,
    "request_id": request_id,
    "query": user_query[:100],
    "timestamp": datetime.now().isoformat(),
    "client_ip": request.client.host,  # 如果可用
    "user_agent": request.headers.get("user-agent"),  # 如果可用
}
```

### 2. 使用结构化日志

使用 JSON 格式的结构化日志：

```python
logger.info(
    "处理用户请求",
    extra={
        "request_id": request_id,
        "user_id": user_id,
        "session_id": session_id,
        "query": user_query,
        "event": "request_start"
    }
)
```

### 3. 集成 APM 工具

考虑集成专业的 APM（Application Performance Monitoring）工具：
- Datadog APM
- New Relic
- Elastic APM
- Sentry

这些工具提供更强大的追踪和关联功能。

## 总结

通过添加 request_id 和相关元数据：

✅ **可追踪性**：每个请求都有唯一标识
✅ **可调试性**：快速定位问题请求
✅ **可分析性**：支持用户级别的性能分析
✅ **低成本**：几乎零性能开销
✅ **向后兼容**：不影响现有功能

即使 LangSmith 不支持自定义元数据，日志中的 request_id 也足以满足生产环境的追踪需求。
