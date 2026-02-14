# LangSmith 追踪问题完整复盘

## 问题概述

**问题描述**: LangSmith 平台上显示 "Agent workflow" 记录，但 Input 和 Output 列完全为空，无法查看详细的执行信息。

**影响范围**:
- 无法追踪智能体执行过程
- 无法调试 LLM 调用
- 无法分析工具使用情况
- 严重影响系统可观测性

**问题持续时间**: 约 2-3 小时
**消耗资源**: 大量 Token、多次代码修改、多次重启测试

---

## 问题根因分析

### 最终根因（Root Cause）

**位置**: `backend/app/multi_agent/service_agent.py` 第 1-3 行

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)  # ← 这行代码是罪魁祸首！
from agents import Agent, ModelSettings
```

**影响机制**:
- `set_tracing_disabled(True)` 是一个**全局设置**
- 它会禁用整个应用的 OpenAI Agents SDK 追踪功能
- 即使 LangSmith 客户端正确初始化，`OpenAIAgentsTracingProcessor` 也无法捕获任何数据
- 导致 LangSmith 平台上创建了空的追踪记录（有记录但无内容）

---

## 问题排查过程（时间线）

### 第一阶段：初始诊断（误判方向）

**现象**: LangSmith 平台完全没有日志

**错误假设**: 认为是 LangSmith 配置问题

**采取的行动**:
1. 检查 `.env` 文件中的 LangSmith 配置
2. 检查 `langsmith_client.py` 的初始化逻辑
3. 发现模型名称格式问题 `Qwen/Qwen3-32B`（实际上这不是主要问题）

**结果**: 浪费时间在非关键路径上

---

### 第二阶段：Settings 加载问题（真实问题但非根因）

**现象**: 出现 `'Settings' object has no attribute 'LANGCHAIN_TRACING_V2'` 错误

**真实原因**: Python 模块路径冲突
- `sys.path` 中包含 `backend/knowledge` 路径
- Python 导入了错误的 Settings 类（知识库项目的 Settings）
- 知识库的 Settings 没有 `LANGCHAIN_TRACING_V2` 等字段

**解决方案**: 在 `api/main.py` 中添加路径管理代码
```python
# 移除 backend/knowledge 路径
knowledge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../knowledge'))
if knowledge_path in sys.path:
    sys.path.remove(knowledge_path)

# 确保当前项目路径在最前面
current_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, current_app_path)
```

**结果**:
- ✅ 解决了 Settings 加载问题
- ✅ LangSmith 客户端成功初始化
- ❌ 但 Input/Output 仍然为空（说明这不是根因）

---

### 第三阶段：追踪配置问题（接近真相）

**现象**: LangSmith 有记录但 Input/Output 为空

**排查路径**:
1. 检查 `agent_factory.py` - 发现并删除了 `RunConfig(tracing_disabled=True)`
2. 尝试添加 `@traceable` 装饰器到 `agent_service.py`（错误方向）
3. 检查 `technical_agent.py` - 发现测试代码中有 `tracing_disabled=True`（但这只是测试代码）

**结果**:
- ✅ 删除了一些不必要的 `tracing_disabled` 配置
- ❌ 但问题依然存在

---

### 第四阶段：发现真凶（最终解决）

**关键发现**: 使用 `grep` 搜索 `tracing_disabled` 时发现：

```bash
multi_agent/service_agent.py:1:from agents import set_tracing_disabled
multi_agent/service_agent.py:3:set_tracing_disabled(True)
```

**恍然大悟**:
- 这是一个**全局函数调用**，不是局部配置
- 它在模块导入时就执行了
- 影响整个应用的所有 Agent 执行

**解决方案**: 直接删除这三行代码

**结果**: ✅ 问题彻底解决，LangSmith 显示完整的追踪信息

---

## 为什么这个问题如此难以发现？

### 1. 隐蔽性强
- 代码位于文件开头，容易被忽略
- 看起来像是"测试代码"或"临时调试代码"
- 没有明显的注释说明其影响范围

### 2. 误导性现象
- LangSmith 平台**有记录**（说明追踪系统在工作）
- 但**没有内容**（说明数据被拦截了）
- 这种"半工作"状态让人误以为是配置问题而非代码问题

### 3. 全局副作用
- `set_tracing_disabled(True)` 是全局设置，影响所有后续代码
- 即使其他地方配置正确，这个全局开关也会覆盖一切
- 类似于"一票否决"机制

### 4. 排查路径干扰
- Settings 加载问题是真实存在的，但不是根因
- 修复 Settings 问题后，LangSmith 初始化成功，给人"快要解决"的错觉
- 实际上根因还没有触及

---

## 关键教训与反思

### 教训 1: 全局状态是魔鬼

**问题**:
```python
set_tracing_disabled(True)  # 全局设置，影响整个应用
```

**正确做法**:
```python
# 如果需要禁用追踪，应该在局部使用
result = await Runner.run(
    agent,
    input=query,
    run_config=RunConfig(tracing_disabled=True)  # 局部配置
)
```

**原则**:
- 避免使用全局状态修改函数
- 优先使用局部配置参数
- 如果必须使用全局设置，必须有明确的注释和文档

---

### 教训 2: 排查问题要系统化

**错误的排查方式**:
1. 看到现象 → 猜测原因
2. 尝试修复 → 测试
3. 失败 → 换一个猜测
4. 循环往复

**正确的排查方式**:
1. **收集完整信息**: 日志、配置、代码路径
2. **建立假设树**: 列出所有可能的原因
3. **优先级排序**: 从最可能到最不可能
4. **系统性验证**: 逐一排除，记录结果
5. **根因分析**: 找到根本原因，而非表面现象

**本次应该做的**:
```bash
# 第一步：搜索所有可能影响追踪的代码
grep -r "tracing" backend/app/
grep -r "set_tracing" backend/app/
grep -r "RunConfig" backend/app/

# 第二步：检查全局初始化代码
# 重点关注模块级别的代码（不在函数内的代码）

# 第三步：验证假设
# 逐个注释掉可疑代码，观察效果
```

---

### 教训 3: 代码审查的重要性

**问题代码的特征**:
```python
from agents import set_tracing_disabled

set_tracing_disabled(True)  # ← 没有注释，没有说明
from agents import Agent, ModelSettings
```

**应该有的样子**:
```python
from agents import Agent, ModelSettings

# 注意：以下代码仅用于本地测试，生产环境必须删除或注释掉
# from agents import set_tracing_disabled
# set_tracing_disabled(True)  # 禁用追踪以加快本地测试速度
```

**代码审查检查清单**:
- [ ] 是否有全局状态修改？
- [ ] 是否有副作用？
- [ ] 是否有充分的注释？
- [ ] 是否会影响生产环境？
- [ ] 是否有更好的替代方案？

---

### 教训 4: 测试代码与生产代码的隔离

**问题**: 测试代码混入生产代码路径

**解决方案**:
1. **使用环境变量控制**:
```python
import os

if os.getenv("ENVIRONMENT") == "development":
    set_tracing_disabled(True)
```

2. **使用独立的测试文件**:
```
backend/app/
├── multi_agent/
│   ├── service_agent.py          # 生产代码
│   └── test_service_agent.py     # 测试代码（独立文件）
```

3. **使用配置文件**:
```python
# config/settings.py
class Settings(BaseSettings):
    ENABLE_TRACING: bool = True  # 通过配置控制
```

---

### 教训 5: 文档的重要性

**缺失的文档**:
- `set_tracing_disabled()` 函数的影响范围
- 为什么要禁用追踪
- 何时应该启用/禁用追踪

**应该有的文档**:
```markdown
## LangSmith 追踪配置

### 全局开关
- `set_tracing_disabled(True)`: 禁用整个应用的追踪（慎用！）
- `set_tracing_disabled(False)`: 启用追踪（默认）

### 局部配置
- `RunConfig(tracing_disabled=True)`: 仅禁用单次执行的追踪

### 注意事项
⚠️ 不要在生产代码中使用 `set_tracing_disabled(True)`
⚠️ 如果需要禁用追踪，使用局部配置
⚠️ 追踪对性能影响很小，不建议禁用
```

---

## 问题修复总结

### 修复的文件

1. **backend/app/multi_agent/service_agent.py**
   - 删除: `from agents import set_tracing_disabled`
   - 删除: `set_tracing_disabled(True)`

2. **backend/app/multi_agent/agent_factory.py**
   - 删除: `run_config=RunConfig(tracing_disabled=True)` 参数

3. **backend/app/services/agent_service.py**
   - 删除: 错误的 `@traceable` 装饰器
   - 删除: 不必要的 `langsmith` 导入

4. **backend/app/api/main.py**
   - 添加: 路径管理代码（修复 Settings 加载问题）

### 验证步骤

1. ✅ 重启应用
2. ✅ 通过前端发送请求
3. ✅ 检查 LangSmith 平台
4. ✅ 确认 Input/Output 列有完整数据
5. ✅ 确认可以查看详细的执行树

---

## 预防措施

### 1. 代码规范
- 禁止在生产代码中使用全局状态修改函数
- 所有全局配置必须通过配置文件管理
- 测试代码必须与生产代码隔离

### 2. 代码审查清单
```markdown
## LangSmith 追踪相关审查

- [ ] 是否使用了 `set_tracing_disabled()`？
- [ ] 是否在全局作用域修改了追踪配置？
- [ ] 是否有充分的注释说明？
- [ ] 测试代码是否与生产代码隔离？
```

### 3. 自动化检测
```bash
# 添加到 CI/CD 流程
#!/bin/bash
# 检查是否有禁用追踪的代码
if grep -r "set_tracing_disabled(True)" backend/app/multi_agent/ backend/app/services/; then
    echo "❌ 错误：发现禁用追踪的代码！"
    exit 1
fi
```

### 4. 文档完善
- 在 README 中添加 LangSmith 配置说明
- 在代码中添加关键注释
- 创建故障排查指南

---

## 成本分析

### 时间成本
- 问题排查: 约 2-3 小时
- 代码修改: 约 30 分钟
- 测试验证: 约 30 分钟
- **总计**: 约 3-4 小时

### Token 成本
- 对话轮次: 约 20+ 轮
- 代码读取: 多次读取大文件
- 估计消耗: 40,000+ tokens

### 机会成本
- 延误了其他功能开发
- 影响了系统调试效率
- 降低了团队信心

---

## 最终建议

### 立即执行
1. ✅ 删除所有 `set_tracing_disabled(True)` 调用
2. ✅ 添加 CI/CD 检测脚本
3. ✅ 更新项目文档

### 短期计划
1. 代码审查所有全局状态修改
2. 建立测试代码隔离规范
3. 完善故障排查文档

### 长期计划
1. 建立代码质量门禁
2. 定期进行代码审查培训
3. 完善可观测性基础设施

---

## 结论

这个问题的根本原因是**一行看似无害的全局配置代码**，但它的影响是**全局性和隐蔽性的**。

**核心教训**:
1. 全局状态是危险的，必须谨慎使用
2. 系统化排查比盲目尝试更有效
3. 代码审查和文档是预防问题的关键
4. 测试代码必须与生产代码隔离

**最重要的一点**:
> 当遇到"半工作"状态的问题时（有记录但无内容），要特别警惕全局开关或拦截器的存在。

---

**复盘完成时间**: 2026-01-28
**问题状态**: ✅ 已解决
**文档维护者**: Claude Code
