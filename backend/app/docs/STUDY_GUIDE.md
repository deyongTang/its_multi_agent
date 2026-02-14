# ITS 多智能体系统 (its_app)

## 项目概览
本项目是一个工业级的**智能交通系统 (ITS) 多智能体**后端应用。旨在通过精密的多智能体架构，实现“业务数据闭环”和“业务流程可控”，满足商业化交通服务场景下的严谨性和科学性要求。

## 项目背景
在复杂的交通服务场景中，用户需求往往具有多跳性和跨域性（如：从技术咨询转到线下服务站导航）。本项目通过核心的**协调者智能体 (Orchestrator Agent)** 统一调度，利用 **MCP (Model Context Protocol)** 协议连接外部专业能力，确保复杂业务流程的自动化与可控化。

## 核心功能
*   **多智能体协同调度**：自动识别用户意图，在技术专家、服务站查询、POI 导航等子智能体间进行任务拆解与分发。
*   **标准 MCP 协议集成**：标准化接入百度地图、联网搜索等外部工具，提升系统的扩展性。
*   **复杂多跳任务处理**：支持“查询->判断->决策->执行”的完整闭环逻辑。
*   **工业级基础架构**：包含异步连接池、详尽的日志追踪、基于 Pydantic 的配置管理以及流式响应（SSE）机制。

---

# ITS Multi-Agent System 学习与调试指南

这份文档旨在指导你如何从源代码层面理解当前的多智能体系统，并通过实际运行来观察其行为。

## 第一阶段：静态代码分析 (核心逻辑)

请按以下顺序阅读核心源代码，理解系统的"大脑"（调度）和"手脚"（工具）是如何配合的。

### 1. 核心大脑：调度器 (Orchestrator)
*   **目标文件**: `multi_agent/orchestrator_agent.py`
*   **关注点**:
    *   **Agent 初始化**: 查看 `orchestrator_agent` 变量是如何被创建的。注意它使用了哪个 Prompt (`orchestrator_v1`) 和哪些 Tools (`AGENT_TOOLS`)。
    *   **运行逻辑**: 观察 `run_single_test` 函数。
        *   `stack.enter_async_context`: 它是如何同时建立 搜索MCP 和 地图MCP 连接的。
        *   `Runner.run_streamed`: 这是 Agent 启动的核心。
        *   `event.type == "run_item_stream_event"`: 这里是打印"思考过程"和"工具调用"日志的地方。

### 2. 指令中心：Prompt 设计
*   **目标文件**: `prompts/orchestrator_v1.md`
*   **关注点**:
    *   这是调度器的"灵魂"。阅读它如何定义 **意图识别** 规则。
    *   注意它如何区分 `consult_technical_expert` (技术/资讯) 和 `query_service_station_and_navigate` (服务/导航)。
    *   **核心原则**: 阅读 "任务完整性原则"，理解它如何处理组合任务（如：先查问题，再找维修站）。

### 3. 执行工具：Agent Tools 定义
*   **目标文件**: `multi_agent/agent_factory.py`
*   **关注点**:
    *   这里定义了暴露给调度器的 Python 函数：`consult_technical_expert` 和 `query_service_station_and_navigate`。
    *   注意这些函数内部：它们不是直接写死逻辑，而是再次调用了子 Agent (`technical_agent` 和 `comprehensive_service_agent`)。这就是 **分层 Agent 架构**。

### 4. 外部连接：MCP 协议实现
*   **目标文件**: `infrastructure/tools/mcp/mcp_servers.py`
*   **关注点**:
    *   `MCPServerSse`: 这是如何连接到外部 SSE 服务（百度地图、搜索服务）的客户端实现。
    *   配置参数 (`params`): 这里读取了 `.env` 中的 API Key。

---

## 第二阶段：动态调试 (运行与观察)

在运行之前，请确保你的项目根目录包含 `.env` 文件，并且配置了有效的 `SF_API_KEY` (或阿里百炼 Key) 和 `BAIDUMAP_AK`。

### 任务 1：CLI 模式运行 (观察思考链路)

这是最直接的观察方式，可以清楚看到 Agent 的"思考 -> 调用工具 -> 获取结果 -> 最终回复"的全过程。

1.  **修改测试用例**:
    打开 `multi_agent/orchestrator_agent.py`，找到底部的 `test_cases` 列表。
    取消注释其中一个简单的测试用例，例如：
    ```python
    # 找到这一行并取消注释，或添加新的一行
    ("单个任务（实时问题）", "今天AI圈发生了些什么事儿"),
    ```

2.  **运行脚本**:
    在终端执行：
    ```bash
    python multi_agent/orchestrator_agent.py
    ```

3.  **观察输出**:
    *   **Tool Call**: 看它是否正确识别了意图并调用了 `consult_technical_expert`。
    *   **Arguments**: 传递的参数是什么？
    *   **Result**: 最终返回的自然语言回答。

### 任务 2：Web 服务模式运行 (模拟真实请求)

启动 FastAPI 服务，模拟前端发起的 SSE 流式请求。

1.  **启动服务**:
    在终端执行：
    ```bash
    python api/main.py
    ```
    *等待出现 `Application startup complete` 和 MCP 连接成功的日志。*

2.  **发送请求 (另开一个终端)**:
    使用 `curl` 发送一个 POST 请求：
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/query" \
         -H "Content-Type: application/json" \
         -d '{
               "query": "最近的小米之家在哪里？",
               "context": {"user_id": "test_user_001", "session_id": "session_abc"}
             }'
    ```

3.  **观察日志**:
    回到运行 `api/main.py` 的终端，观察实时的日志滚动。
    *   看 `[Route] 转交业务专家...` 这样的日志，证明请求被正确路由了。

---

## 思考题 (为升级做准备)

在阅读和运行时，请思考以下问题，这将是我们下一步"工业级改造"的重点：

1.  **异常处理**: 如果你关掉 Wi-Fi 或者断开网络，运行 CLI 测试会发生什么？程序是优雅报错还是直接崩溃打印 traceback？
2.  **延迟感知**: 现在的日志能看出每一步花费了多少时间吗？
3.  **配置安全**: 如果 `.env` 里的 Key 是错的，系统会在启动时就报错，还是等到调用时才报错？
