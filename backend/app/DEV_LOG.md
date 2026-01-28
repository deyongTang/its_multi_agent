# 研发日志 (Development Log)

## [2026-01-28] 修复知识库服务调用异常

### 问题描述
在调用知识库服务 `http://127.0.0.1:8001/query` 时，系统出现以下两类错误：
1. **401 Unauthorized**: 认证失败。
2. **Expecting value: line 1 column 1 (char 0)**: 解析响应数据失败。

### 根本原因分析

1. **Token 格式错误 (401)**:
   - 现象：`.env` 文件中配置的 `KNOWLEDGE_BASE_TOKEN` 已经包含了 `Bearer ` 前缀。
   - 原因：`infrastructure/tools/local/knowledge_base.py` 代码中又手动拼接了 `f"Bearer {settings.KNOWLEDGE_BASE_TOKEN}"`，导致发送的请求头变为 `Authorization: Bearer Bearer <Token>`。
   - 影响：服务器校验失败，返回 401。

2. **响应格式不匹配 (Expecting value)**:
   - 现象：修复 401 后，由于知识库服务返回的是 `text/event-stream` (SSE) 格式，而客户端代码直接使用 `response.json()` 进行解析。
   - 原因：`httpx` 客户端在面对非 JSON 格式的字符串（如以 `data:` 开头的 SSE 数据流）调用 `.json()` 方法时抛出解析异常。
   - 影响：系统无法获取知识库内容，直接报错。

### 解决方案

1. **修正配置**:
   - 更新 `.env` 文件，移除 `KNOWLEDGE_BASE_TOKEN` 值中多余的 `Bearer ` 前缀，确保代码拼接逻辑正确。

2. **代码兼容性增强**:
   - 修改 `infrastructure/tools/local/knowledge_base.py` 中的 `query_knowledge` 函数。
   - 增加对 `Content-Type` 的判断。
   - 如果响应类型为 `text/event-stream`，则按行解析 SSE 协议数据，提取所有以 `data:` 开头的内容并进行字符串拼接，最后封装成字典返回。
   - 保留对普通 JSON 响应的支持，确保向后兼容。

### 验证结果
- 使用 `curl` 模拟请求确认服务端返回正常（包含 Token 校验）。
- 修改代码后，系统能正确接收流式响应并将其合并为完整文本，不再抛出 JSON 解析错误。
