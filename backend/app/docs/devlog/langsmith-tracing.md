# LangSmith 追踪：问题复盘与标识优化

> 本文合并自 `LANGSMITH_TRACING_问题复盘.md` 和 `LangSmith_追踪标识优化.md`

---

## 第一部分：追踪数据为空 — 问题复盘

### 问题概述

LangSmith 平台上显示 "Agent workflow" 记录，但 Input 和 Output 列完全为空，无法查看详细的执行信息。

**影响范围**: 无法追踪智能体执行过程、无法调试 LLM 调用、严重影响系统可观测性。

### 最终根因

**位置**: `backend/app/multi_agent/service_agent.py` 第 1-3 行

```python
from agents import set_tracing_disabled
set_tracing_disabled(True)  # ← 罪魁祸首！
```

`set_tracing_disabled(True)` 是一个**全局设置**，会禁用整个应用的 OpenAI Agents SDK 追踪功能。即使 LangSmith 客户端正确初始化，也无法捕获任何数据。

### 排查过程（时间线）

**第一阶段：初始诊断（误判方向）**
- 现象：LangSmith 平台完全没有日志
- 错误假设：认为是 LangSmith 配置问题
- 结果：浪费时间在非关键路径上

**第二阶段：Settings 加载问题（真实问题但非根因）**
- 现象：`'Settings' object has no attribute 'LANGCHAIN_TRACING_V2'`
- 真实原因：`sys.path` 中包含 `backend/knowledge` 路径，导入了错误的 Settings 类
- 解决：在 `api/main.py` 中添加路径管理代码
- 结果：LangSmith 初始化成功，但 Input/Output 仍然为空

**第三阶段：追踪配置问题（接近真相）**
- 删除了 `agent_factory.py` 中的 `RunConfig(tracing_disabled=True)`
- 结果：问题依然存在

**第四阶段：发现真凶**
- 使用 `grep -r "tracing_disabled" backend/app/` 搜索
- 发现 `service_agent.py` 文件开头的全局调用
- 删除后问题彻底解决

### 为什么这个问题难以发现？

1. **隐蔽性强**: 代码位于文件开头，看起来像"临时调试代码"
2. **误导性现象**: LangSmith 有记录但没有内容（"半工作"状态让人误以为是配置问题）
3. **全局副作用**: 一票否决机制，覆盖所有其他正确配置
4. **排查路径干扰**: Settings 加载问题是真实存在的，修复后给人"快要解决"的错觉

### 关键教训

1. **全局状态是魔鬼**: 避免使用全局状态修改函数，优先使用局部配置 `RunConfig(tracing_disabled=True)`
2. **排查问题要系统化**: 先 `grep -r "tracing" backend/app/` 搜索所有可能影响追踪的代码
3. **测试代码与生产代码隔离**: 使用环境变量控制或独立测试文件
4. **"半工作"状态要警惕全局开关**: 有记录但无内容时，特别注意拦截器的存在

### 修复的文件

1. `multi_agent/service_agent.py` — 删除 `set_tracing_disabled(True)`
2. `multi_agent/agent_factory.py` — 删除 `RunConfig(tracing_disabled=True)` 参数
3. `services/agent_service.py` — 删除错误的 `@traceable` 装饰器
4. `api/main.py` — 添加路径管理代码（修复 Settings 加载问题）

### 预防措施

```bash
# 添加到 CI/CD 流程
if grep -r "set_tracing_disabled(True)" backend/app/multi_agent/ backend/app/services/; then
    echo "错误：发现禁用追踪的代码！"
    exit 1
fi
```

---

## 第二部分：追踪标识优化方案

### 问题描述

LangSmith 平台上所有追踪记录的 Name 都显示为 "Agent workflow"，没有任何区分标识。无法区分不同用户的请求，无法追踪特定会话。

### 解决方案

#### 1. 添加唯一请求标识（Request ID）

```python
import uuid
request_id = str(uuid.uuid4())[:8]  # 例如: "a3f2b1c4"
```

#### 2. 在日志中包含请求标识

```python
logger.info(f"[{request_id}] 用户 {user_id} 发送的待处理任务: {user_query}")
```

#### 3. 添加 LangSmith 追踪元数据

```python
from langsmith.run_helpers import get_current_run_tree

run_tree = get_current_run_tree()
if run_tree:
    run_tree.extra = {
        "user_id": user_id,
        "session_id": session_id,
        "request_id": request_id,
        "query": user_query[:100]
    }
    run_tree.tags = [
        f"user:{user_id}",
        f"session:{session_id}",
        f"req:{request_id}"
    ]
```

### 使用方法

```bash
# 通过日志追踪请求
grep "a3f2b1c4" logs/app.log

# 实时监控特定用户
tail -f logs/app.log | grep "root1"
```

在 LangSmith 平台上使用标签过滤：`user:root1`、`session:session_xxx`、`req:a3f2b1c4`

### 注意事项

- OpenAI Agents SDK 0.7.0 可能不支持自定义元数据和标签，但日志中的 request_id 仍然有效
- 性能影响几乎可以忽略（UUID 生成 < 0.1ms）
- 元数据中只记录查询前 100 个字符，避免记录敏感信息

---

**问题状态**: 已解决 | **复盘完成时间**: 2026-01-28
