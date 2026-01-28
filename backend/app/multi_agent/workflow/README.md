# LangGraph 工作流引擎 - Phase 1

## 概述

基于 LangGraph 的状态机编排引擎，实现意图识别、槽位填充、多轮对话等核心功能。

## 架构设计

### 核心组件

```
workflow/
├── __init__.py           # 模块入口
├── state.py              # 状态定义（AgentState, RetrievalStrategy, DiagnosisStep）
├── graph.py              # 工作流图定义
├── runner.py             # 运行器（集成 LangSmith）
├── test_workflow.py      # 测试用例
├── nodes/                # 节点实现
│   ├── intent_node.py           # 意图识别
│   ├── slot_filling_node.py     # 槽位填充
│   ├── ask_user_node.py         # 追问生成
│   └── general_chat_node.py     # 闲聊处理
└── edges/                # 路由函数
    ├── route_intent.py          # 意图路由
    └── route_slot_check.py      # 槽位检查路由
```

### Phase 1 流程图

```
START
  ↓
node_intent (意图识别)
  ↓
route_intent (意图路由)
  ├─→ chitchat → node_general_chat → END
  └─→ business → node_slot_filling (槽位填充)
                   ↓
                 route_slot_check (槽位检查)
                   ├─→ missing → node_ask_user → END (interrupt)
                   └─→ complete → END
```

## 安装依赖

```bash
cd backend/app
pip install -r requirements.txt
```

新增依赖：
- `langgraph>=0.2.0` - 状态机编排框架
- `langchain-core>=0.3.0` - LangChain 核心库
- `langchain-openai>=0.2.0` - OpenAI 集成

## 运行测试

```bash
cd backend/app
python -m multi_agent.workflow.test_workflow
```

测试用例：
- **T01**: 闲聊场景（直接回复）
- **T02**: 技术问题（槽位不完整，触发追问）

## 核心功能

### 1. 意图识别

自动识别用户意图类型：
- `tech`: 技术问题（故障诊断、操作指南、实时资讯）
- `service`: 服务站查询（维修点查找）
- `poi`: POI 导航（地点查询、路线规划）
- `chitchat`: 闲聊（非业务对话）

### 2. 槽位填充

根据意图类型提取必要信息：
- **tech**: `problem_description`, `device_model`, `os_version`
- **service**: `location`, `brand`
- **poi**: `destination`, `origin`

### 3. 多轮对话

- 自动检测缺失槽位
- 生成友好的追问话术
- 支持最多 3 次追问（防止死循环）
- 使用 `interrupt_before` 实现人机交互

### 4. 持久化

- **开发环境**: `MemorySaver`（内存存储）
- **生产环境**: `RedisCheckpointer`（Phase 3 实现）
- 支持会话恢复（通过 `thread_id`）

## LangSmith 集成

### 自动追踪

工作流自动集成 LangSmith 追踪，无需额外配置。

### 追踪信息

- **trace_id**: 从 `trace_id_var` 上下文变量获取
- **业务属性**:
  - `biz.intent`: 意图类型
  - `biz.confidence`: 置信度
  - `biz.extracted_slots`: 已提取槽位
  - `biz.missing_slots`: 缺失槽位
  - `biz.ask_count`: 追问次数

### 查看追踪

1. 确保 `.env` 中配置了 LangSmith：
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=ITS-MultiAgent
```

2. 运行测试后，访问 [LangSmith](https://smith.langchain.com/)

3. 在项目中查看追踪记录，可以看到：
   - 完整的状态流转路径
   - 每个节点的输入输出
   - 业务级别的追踪属性

## 使用示例

### 基本使用

```python
from multi_agent.workflow.runner import WorkflowRunner
from infrastructure.logging.logger import trace_id_var
import uuid

# 设置 trace_id
trace_id_var.set(str(uuid.uuid4())[:8])

# 创建运行器
runner = WorkflowRunner()

# 运行工作流
result = await runner.run(
    user_query="电脑蓝屏了",
    user_id="user_001",
    session_id="session_001",
)

# 获取结果
print(f"意图: {result['current_intent']}")
print(f"槽位: {result['slots']}")
print(f"回复: {result['messages'][-1].content}")
```

### 会话恢复

```python
# 第一轮对话
result1 = await runner.run(
    user_query="电脑蓝屏了",
    user_id="user_001",
    session_id="session_001",
    thread_id="thread_001",  # 指定 thread_id
)

# 第二轮对话（恢复上下文）
result2 = await runner.run(
    user_query="是 Windows 10 系统",
    user_id="user_001",
    session_id="session_001",
    thread_id="thread_001",  # 使用相同的 thread_id
)
```

## 错误处理

### 节点级别

每个节点都有 try-catch 包装：
- 捕获异常并记录到 `error_log`
- 提供降级策略（默认值）
- 不会中断整个流程

### 追问限制

- 最多追问 3 次
- 超限后自动转人工（`need_human_help = True`）

### 日志追踪

所有日志自动包含 `trace_id`：
```
[a3f2b1c4] 开始意图识别: 电脑蓝屏了...
[a3f2b1c4] 意图识别完成: tech (置信度: 0.95)
[a3f2b1c4] 槽位填充完成: 已提取 1 个，缺失 0 个
```

## 下一步计划

### Phase 2: 核心功能节点迁移

- [ ] 实现 `node_strategy_gen`（检索策略生成）
- [ ] 实现并行搜索节点（ES、Baidu、Tools）
- [ ] 实现 `node_merge_rerank`（结果融合）
- [ ] 实现 `node_verify`（结果校验）
- [ ] 实现 `node_expand_query`（扩搜）
- [ ] 实现 `node_escalate`（转人工）
- [ ] 实现 `node_generate_report`（生成报告）

### Phase 3: 多轮会话与持久化

- [ ] 接入 `RedisCheckpointer`
- [ ] 实现会话历史管理
- [ ] 调试 `thread_id` 机制
- [ ] 跑通 M01-M03 用例

## 常见问题

### Q: 如何查看工作流的可视化图？

A: LangGraph 会自动在 LangSmith 中生成可视化图。也可以使用：
```python
from multi_agent.workflow.graph import create_workflow_graph
graph = create_workflow_graph()
graph.get_graph().print_ascii()
```

### Q: 如何调试某个节点？

A: 可以单独测试节点：
```python
from multi_agent.workflow.nodes import node_intent
from multi_agent.workflow.state import AgentState
from langchain_core.messages import HumanMessage

state = {
    "messages": [HumanMessage(content="你好")],
    "trace_id": "test",
    # ... 其他必需字段
}

result = await node_intent(state)
print(result)
```

### Q: 如何修改槽位定义？

A: 编辑 `nodes/slot_filling_node.py` 中的 `REQUIRED_SLOTS` 字典。

## 参考文档

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangSmith 追踪指南](https://docs.smith.langchain.com/)
- [WORKFLOW_ENGINE_DESIGN.md](../WORKFLOW_ENGINE_DESIGN.md) - 完整设计文档
