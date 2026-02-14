# 工业级 ITS 智能运维编排引擎详细设计文档 (Detailed Design Document)

| 文档版本 | 修改日期 | 修改人 | 备注 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-01-28 | 架构师 | 初始化状态机与动态检索策略设计 |
| v2.0 | 2026-01-28 | 架构师 | 升级为工业级架构，增加数据闭环、安全合规、人机协同等模块 |

---

## 1. 业务背景与技术挑战 (Background & Challenges)

### 1.1 核心痛点
当前的 ITS 智能体初步具备了对话能力，但在面对企业级真实场景时，显得“脆弱”且“不可控”：
1.  **不可控性 (Uncontrollability)**：完全依赖 LLM 的概率性输出，导致在收集关键故障信息（如“型号”、“错误码”）时经常遗漏，且容易产生幻觉。
2.  **数据割裂 (Open Loop)**：Agent 的每一次交互都是孤立的，缺乏“负反馈机制”。线上发生的 Bad Case 无法自动转化为知识库的更新或 Prompt 的优化。
3.  **安全隐患 (Security Risks)**：缺乏对敏感数据（PII）的过滤，且对 Prompt Injection 攻击缺乏防御。
4.  **运维盲区 (Observability Gap)**：缺乏端到端的全链路追踪，无法量化 Agent 的“思考过程”和“耗时瓶颈”。

### 1.2 设计目标
构建一个 **"可信、可控、可进化"** 的工业级智能编排引擎。

*   **业务合规率**：100%（通过 FSM 强制状态流转，杜绝核心步骤跳过）。
*   **检索准确率 (Recall@5)**：提升 40%（通过动态权重策略 + 语义重排）。
*   **数据闭环**：实现 "Feedback -> Evaluation -> Finetune/KB Update" 的自动化流程。
*   **系统延迟 (P99)**：< 500ms (首字生成)，< 2s (完整回复，复杂任务除外)。

---

## 2. 系统总体架构 (System Architecture)

系统采用 **分层治理架构 (Layered Governance Architecture)**，将“概率性的 AI” 关进 “确定性的工程笼子”里。

```mermaid
graph TD
    User[用户终端] --> WAF[WAF/API Gateway]
    WAF --> Auth[认证鉴权 & 限流]
    Auth --> Guard_In[输入安全围栏]

    subgraph Core["Core Orchestration Engine (Python)"]
        Guard_In --> Router{意图路由 Agent}

        Router -->|简单问答| Chat[通用 Chat Agent]
        Router -->|故障诊断/复杂任务| FSM[有限状态机]

        subgraph FSMContext["FSM Context (Shared Memory)"]
            State1[SlotFilling] --> State2[StrategyGen]
            State2 --> State3[ActionExec]
            State3 --> State4[ResponseGen]
        end

        FSM --> State1
        State4 --> HITL[Human In The Loop]
    end

    subgraph Knowledge["Knowledge & Service Layer"]
        SearchAPI[增强检索服务]
        ES[Elasticsearch]
        Rerank[RRF 重排模型]
        Tools[外部工具]

        SearchAPI --> ES
        SearchAPI --> Rerank
    end

    State3 -->|Active RAG| SearchAPI
    State3 -->|Tool Call| Tools

    subgraph DataLoop["Data Closed Loop System"]
        Log[全链路日志] --> ETL[数据清洗]
        Feedback[用户反馈] --> Label[自动/人工标注]
        Label --> Eval[效果评估]
        Eval -->|Bad Cases| KB_Update[知识库修正]
        Eval -->|Bad Cases| Prompt_Opt[Prompt 优化]
    end

    State4 --> Response[响应生成]
    Response --> Guard_Out[输出安全围栏]
    Guard_Out --> User
```

---

## 3. 核心模块详细设计 (Module Design)

### 3.1 确定性编排引擎 (FSM Orchestrator)

放弃纯 Prompt 驱动的 ReAct 模式，采用 **FSM (有限状态机)** 管理核心业务流，确保流程的**确定性**。

#### 3.1.1 状态定义
*   **INIT**: 初始化上下文，加载用户画像 (User Profile) 和历史 Session。
*   **INTENT_CHECK**: 意图识别与分类（故障诊断 vs 技术咨询 vs 闲聊）。
*   **SLOT_FILLING**: **(核心)** 强制信息收集。基于 Pydantic 校验器，检查关键槽位（如 `device_id`, `error_code`）是否完备。若缺失，强制进入 `ASK_USER` 状态。
*   **STRATEGY_GEN**: 生成检索或工具调用策略（Json 格式）。
*   **RETRIEVAL / TOOL_EXEC**: 执行具体的检索或工具调用。
*   **VERIFY**: 结果校验。检查检索结果是否为空，置信度是否达标。
*   **HITL (Human-in-the-Loop)**: **(新增)** 若多次检索失败或置信度低于阈值，自动升级为人工客服工单，并生成摘要给人工坐席。
*   **RESPONSE_GEN**: 生成最终回复。

#### 3.1.2 异常熔断机制
*   **死循环检测**：FSM 内部维护 Step Counter，超过 10 步强制结束并转人工。
*   **LLM 超时重试**：关键节点配置 Exponential Backoff 重试策略。

### 3.2 主动检索协议 (Active Retrieval Protocol)

Agent 不再是被动的“查询者”，而是拥有“元认知”的**策略制定者**。它负责告诉知识库服务“我要找什么类型的资料”，而不是“怎么找”。

#### 3.2.1 动态策略矩阵
在 `STRATEGY_GEN` 阶段，Agent 根据意图类型输出业务层检索配置：

| 场景类型 | 意图标签 (Query Tags) | 业务目标 | 适用案例 |
| :--- | :--- | :--- | :--- |
| **精确报错** | `["ErrorCode", "ExactMatch"]` | 精确命中特定错误码解决方案 | "错误码 0x8004005" |
| **模糊咨询** | `["SemanticSearch", "Broad"]` | 召回语义相关的故障现象 | "电脑运行很慢，卡顿" |
| **组合查询** | `["Hybrid", "HowTo"]` | 综合检索操作指南 | "Win10 如何配置静态IP" |
| **已知实体** | `["EntityFilter", "Product"]` | 限定在特定产品线下检索 | "ThinkPad X1 无法充电" |

#### 3.2.2 接口 Schema (Business Layer)
```python
class RetrievalStrategy(BaseModel):
    intent_type: str = Field(..., description="业务意图类型，如 tech_issue")
    query_tags: List[str] = Field(default=[], description="业务检索标签，指导知识库内部策略")
    filters: Dict[str, Any] = {} # e.g. {"product_line": "server"}
    top_k: int = 5
```

### 3.3 数据闭环系统 (Data Closed Loop)

这是区别于 Demo 的关键，实现了系统的**自我进化**。

1.  **数据埋点**：
    *   **Trace ID**: 贯穿 API -> FSM -> LLM -> DB 全链路。
    *   **Feedback Endpoint**: 允许前端传入 `thumbs_up`, `thumbs_down` 及 `correction_text`。
2.  **Bad Case 挖掘**：
    *   **规则挖掘**: 检索结果为空、多轮交互未解决、用户负反馈。
    *   **模型挖掘**: 使用更强的模型 (e.g. GPT-4/Qwen-Max) 定期审计历史对话，评分 < 3 分的标记为 Bad Case。
3.  **闭环动作**：
    *   **知识库补缺**: 将 Bad Case 及其正确解法（人工或高阶模型生成）自动提炼为 Q&A 对，存入知识库“待审核区”。
    *   **Prompt 优化**: 分析 Slot Filling 失败的高频场景，优化提取 Prompt 的 Few-Shot 示例。

---

## 4. 安全与合规设计 (Security & Compliance)

### 4.1 输入/输出围栏 (Guardrails)
*   **PII 过滤**: 在发送给 LLM 前，使用正则或专门模型将 手机号、身份证、IP地址 等替换为 `<PHONE>`, `<ID_CARD>` 等占位符。
*   **Prompt 注入防御**: 检测输入中是否包含 "Ignore previous instructions" 等特征词。
*   **输出审计**: 检测 LLM 输出是否包含敏感词、竞争对手名称或不合规建议。

### 4.2 权限控制
*   **API 鉴权**: 基于 OAuth2 / JWT 的身份验证。
*   **RBAC**: 限制普通用户只能查询公开知识库，内部技术人员可查询机密文档。

---

## 5. 可观测性设计 (Observability)

### 5.1 结构化日志 (Structured Logging)
```json
{
  "trace_id": "tx_123456",
  "span_id": "span_789",
  "level": "INFO",
  "component": "Orchestrator",
  "event": "state_transition",
  "attributes": {
    "from": "SLOT_FILLING",
    "to": "STRATEGY_GEN",
    "slots_collected": {"device": "Server A", "error": "Disk Full"},
    "latency_ms": 450
  }
}
```

### 5.2 核心监控指标 (Metrics)
*   **Business Success Rate**: 最终诊断成功（无转人工）的比例。
*   **Slot Filling Efficiency**: 平均多少轮对话能填满槽位。
*   **Retrieval Zero Rate**: 检索结果为空的比例（反映知识库缺口）。
*   **Token Usage / Cost**: 按用户/租户维度的成本监控。

---

## 6. 接口协议规范 (API Specifications)

### 6.1 核心对话接口
`POST /api/query`
支持 **SSE (Server-Sent Events)** 流式输出，以降低用户感知的延迟。

**Response Stream Events:**
1.  `event: thought` -> 返回 Agent 的思考过程（状态机流转、使用的工具）。
2.  `event: message` -> 返回具体的对话文本。
3.  `event: diagnosis_report` -> 返回结构化的 JSON 报告（卡片展示）。
4.  `event: error` -> 系统异常信息。

---

## 7. 部署与运维 (Deployment & Ops)

*   **容器化**: Docker + K8s 部署，支持水平扩展。
*   **配置管理**: 通过 ConfigMap/Secret 管理 API Key 和 数据库连接串。
*   **CI/CD**: 代码提交触发 Unit Test -> Integration Test (Mock LLM) -> Deploy to Staging。