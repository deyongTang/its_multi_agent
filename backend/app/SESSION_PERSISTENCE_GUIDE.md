# ITS 会话持久化部署指南

本文档说明如何部署和使用 ITS 多智能体系统的会话持久化功能。

## 架构概览

根据 `SESSION_PERSISTENCE_DESIGN.md` 设计文档，系统采用**双层存储架构**：

| 层面 | 存储介质 | 职责 | 服务对象 |
|------|---------|------|---------|
| **热存储 (State)** | Redis (Checkpointer) | 维护推理状态 (Slots, Thread) | 机器 (LangGraph) |
| **冷存储 (History)** | 文件系统 (JSON) | 维护对话日志 + seq_id | 人类 (Frontend) |

## 核心特性

✅ **Thread ID 绑定** - `thread_id = f"thread_{user_id}_{session_id}"`
✅ **Redis Checkpointer** - LangGraph 状态自动持久化到 Redis
✅ **分布式锁** - 防止并发写入导致数据乱序
✅ **逻辑序号 (seq_id)** - 确保消息顺序一致性
✅ **优雅降级** - Redis 不可用时自动降级到 MemorySaver

---

## 部署步骤

### 1. 安装依赖

```bash
cd backend/app
pip install -r requirements.txt
```

新增的依赖包括：
- `redis>=5.0.0` - Redis 客户端
- `langgraph-checkpoint-redis>=0.1.0` - LangGraph Redis Checkpointer

### 2. 启动 Redis 服务

**方式 1: Docker 启动**
```bash
docker run -d \
  --name redis-its \
  -p 6379:6379 \
  redis:7-alpine
```

**方式 2: 本地安装**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

**验证 Redis 运行**
```bash
redis-cli ping
# 输出: PONG
```

### 3. 配置环境变量

编辑 `backend/app/.env` 文件，添加 Redis 配置：

```env
# Redis 配置（用于会话持久化和分布式锁）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_DECODE_RESPONSES=true
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### 4. 运行测试脚本

```bash
cd backend/app
python test_session_persistence.py
```

**预期输出**：
```
============================================================
ITS 会话持久化功能测试
============================================================

==================================================
测试 1: Redis 连接测试
==================================================
✅ Redis 连接成功: True

==================================================
测试 2: 分布式锁测试
==================================================
尝试获取锁: test:lock:demo
✅ 成功获取锁
执行临界区代码...
临界区代码执行完成
✅ 锁已释放

==================================================
测试 3: seq_id 机制测试
==================================================
准备测试数据: user_id=test_user, session_id=test_session_seq
✅ 第一次保存完成
✅ 第二次保存完成

最终历史记录 (共 5 条):
  seq_id=0, role=system, content=你是一个有记忆的智能体助手，请基于上下文...
  seq_id=1, role=user, content=你好...
  seq_id=2, role=assistant, content=您好，有什么可以帮助您的？...
  seq_id=3, role=user, content=今天天气怎么样...
  seq_id=4, role=assistant, content=今天天气晴朗...

✅ seq_id 顺序正确

==================================================
测试 4: 并发写入测试
==================================================
  线程 0 写入完成
  线程 1 写入完成
  线程 2 写入完成
  线程 3 写入完成
  线程 4 写入完成

并发写入后的历史记录 (共 5 条):
✅ 并发写入测试通过，seq_id 唯一且有序

============================================================
测试结果汇总
============================================================
Redis 连接: ✅ 通过
分布式锁: ✅ 通过
seq_id 机制: ✅ 通过
并发写入: ✅ 通过

总计: 4/4 项测试通过

🎉 所有测试通过！会话持久化功能正常工作。
```

### 5. 启动应用

```bash
cd backend/app
python api/main.py
```

---

## 工作原理

### 1. State 持久化（热存储）

**位置**: [multi_agent/workflow/graph.py](multi_agent/workflow/graph.py#L134-L144)

```python
# 根据 Redis 可用性选择 Checkpointer
if REDIS_AVAILABLE:
    checkpointer = RedisSaver(redis_client)
    logger.info("使用 RedisSaver 作为 Checkpointer (Phase 2)")
else:
    checkpointer = MemorySaver()
    logger.info("使用 MemorySaver (Phase 1)")
```

**工作流程**：
1. 用户发送请求 → `WorkflowRunner.stream_run()`
2. LangGraph 根据 `thread_id` 从 Redis 加载 Checkpoint
3. 每经过一个 Node，自动执行 `checkpoint.put()`
4. 如果进入 `node_ask_user`，流程挂起，状态持久化到 Redis

### 2. History 持久化（冷存储）

**位置**: [services/agent_service_v2.py](services/agent_service_v2.py#L77-L86)

```python
# 流式响应结束后保存历史
if full_ai_response:
    format_result = re.sub(r'\n+', '\n', full_ai_response)
    chat_history.append({"role": "assistant", "content": format_result})
    session_service.save_history(user_id, session_id, chat_history)
```

**工作流程**：
1. 流式响应完成 → 累积完整的 AI 回复
2. 调用 `session_service.save_history()`
3. 使用 Redis 分布式锁保护写入
4. 为新消息分配递增的 `seq_id`
5. 保存到文件系统

### 3. 分布式锁机制

**位置**: [infrastructure/redis_lock.py](infrastructure/redis_lock.py)

```python
with redis_lock(f"lock:session:{user_id}:{session_id}:write", timeout=5):
    # 临界区：Read-Modify-Write
    max_seq_id = repo.get_max_seq_id(user_id, session_id)
    for msg in chat_history:
        if "seq_id" not in msg:
            msg["seq_id"] = max_seq_id + 1
            max_seq_id += 1
    repo.save_session(user_id, session_id, chat_history)
```

**保护机制**：
- 使用 Redis `SET NX EX` 原子操作获取锁
- 锁超时时间 5 秒（防止死锁）
- 使用 Lua 脚本释放锁（防止误删）

---

## 故障恢复

### Q1: Redis 不可用怎么办？

**系统行为**：
- LangGraph 自动降级到 `MemorySaver`（内存模式）
- 分布式锁失效，使用无锁模式
- **适用场景**：单实例部署

**日志输出**：
```
WARNING: RedisSaver 初始化失败，降级到 MemorySaver
WARNING: Redis 分布式锁不可用，将使用无锁模式（仅适用于单实例部署）
```

### Q2: 服务重启后会话丢失吗？

**不会丢失**：
- **State**: 如果使用 RedisSaver，重启后从 Redis 恢复
- **History**: 持久化到文件系统，永久保存

### Q3: 并发写入会导致数据乱序吗？

**不会乱序**：
- 分布式锁保证同一时刻只有一个进程写入
- `seq_id` 机制作为最后防线
- 读取时自动按 `seq_id` 排序

---

## 监控与调试

### 查看 Redis 中的 Checkpoint

```bash
redis-cli
> KEYS thread_*
> GET thread_user123_session456
```

### 查看会话文件

```bash
ls -la backend/app/user_memories/user123/
cat backend/app/user_memories/user123/session456.json
```

### 日志关键字

```bash
# 查看 Checkpointer 类型
grep "Checkpointer" logs/app.log

# 查看分布式锁操作
grep "获取锁\|释放锁" logs/app.log

# 查看 seq_id 分配
grep "seq_id" logs/app.log
```

---

## 性能优化建议

### 1. Redis 连接池配置

[infrastructure/redis_client.py](infrastructure/redis_client.py#L26-L28)
```python
max_connections=10,          # 根据并发量调整
health_check_interval=30,    # 健康检查间隔
```

### 2. 锁超时时间调整

```python
# 如果业务逻辑复杂，可以增加超时时间
with redis_lock(lock_key, timeout=10):  # 默认 5 秒
    # 临界区代码
```

### 3. History 存储优化

**当前方案**: 文件系统 (JSON)
**未来升级**: MySQL + 异步写入 (Phase 3)

---

## 常见问题

### 1. 如何清理测试数据？

```bash
# 清理 Redis
redis-cli FLUSHDB

# 清理会话文件
rm -rf backend/app/user_memories/test_*
```

### 2. 如何迁移到 MySQL？

参考设计文档 Phase 3，需要：
1. 创建 `chat_history` 表（包含 `seq_id` 字段）
2. 修改 `SessionRepository` 使用 MySQL
3. 引入 MQ 异步写入（可选）

### 3. 多实例部署注意事项

✅ **必须启用 Redis**
✅ **必须启用分布式锁**
❌ **不能使用 MemorySaver**

---

## 参考文档

- [SESSION_PERSISTENCE_DESIGN.md](SESSION_PERSISTENCE_DESIGN.md) - 架构设计文档
- [LangGraph Checkpointer 文档](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [Redis 分布式锁最佳实践](https://redis.io/docs/manual/patterns/distributed-locks/)
