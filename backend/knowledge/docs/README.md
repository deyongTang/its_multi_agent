# ITS 知识库系统文档

欢迎查阅。本目录包含 ITS 多智能体知识库系统的权威技术文档。
我们坚持极简主义：**只提供真正有价值的干货。**

## 💡 核心设计哲学 (必读)

*   **[RAG_Design_Philosophy.md](./RAG_Design_Philosophy.md)**
    > **系统的灵魂。**
    > 阐述了为什么我们坚持将任务拆分为“算法（腿）”和“大模型（脑）”。
    > 详细解释了“黄金分工法则”以及在 AI 系统构建中必须避免的反模式。

## 🏗️ 架构与演进路线

*   **[System_Architecture.md](./System_Architecture.md)**
    > **工业级架构白皮书 (单一事实来源)。**
    > 深度剖析：OSS+ES 存算分离设计、N+1 冗余存储策略、混合检索 (Hybrid Retrieval) 核心逻辑、以及事务级的数据入库流水线。
    > **核心关注：业务数据闭环与流程可控性。**

*   **[Roadmap.md](./Roadmap.md)**
    > **系统演进路线图。**
    > 规划了未来的技术方向：包括引入 Cross-Encoder 重排序以提升精度、多模态 RAG (图片理解)、以及基于智能体的相关性筛选机制。

## 📖 操作与运维指南

*   **[ES_Upload_Guide.md](./ES_Upload_Guide.md)**
    > **文档上传指南**：如何手动将文档上传至向量数据库。

*   **[Logging_Guide.md](./Logging_Guide.md)**
    > **开发日志指南**：如何在 Python 代码中正确使用 `logger` (包含 TraceId 注入、JSON 结构化日志)。

*   **[ES_Logging_Guide.md](./ES_Logging_Guide.md)**
    > **日志查询指南**：如何在 Kibana/Elasticsearch 中进行可视化的日志查询与链路追踪。
