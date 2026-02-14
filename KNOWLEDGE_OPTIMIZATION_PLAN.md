# ITS 知识库高并发高可用专项优化方案 (v1.0)

## 1. 背景与目标
当前知识库系统 (`backend/knowledge`) 虽然在数据闭环（ETL）设计上较为完善，但在 **高并发 (High Concurrency)** 和 **高可用 (High Availability)** 方面仍存在显著的架构瓶颈。本方案旨在识别这些痛点，并提出具体的工程化解决方案，以支撑 **千万级数据量** 和 **千级 QPS** 的生产环境要求。

## 2. 核心痛点分析 (Pain Points)

### 2.1 痛点一：同步阻塞 I/O (Blocking I/O)
*   **现状**: `ESRetrievalService` 和 `CrawlerService` 中大量使用了同步的 HTTP 客户端 (`requests`/`elasticsearch`)。
*   **影响**: Python 的 GIL 锁限制了 CPU 利用率。在 I/O 密集型场景（如爬虫、大批量写入 ES）下，线程会被阻塞，导致服务吞吐量（Throughput）极低。一旦并发请求增加，Web 容器（Uvicorn）的线程池瞬间耗尽，后续请求全部超时。

### 2.2 痛点二：Elasticsearch 性能瓶颈 (Scalability)
*   **现状**: 混合检索中的向量匹配使用了 `script_score` + `cosineSimilarity`。
*   **原理**: 这是一个 **O(N)** 的全表扫描操作。ES 必须遍历所有文档计算余弦相似度。
*   **影响**:
    *   **数据量 < 10万**: 响应 < 100ms (当前现状)。
    *   **数据量 > 100万**: 响应 > 1s。
    *   **数据量 > 1000万**: 响应超时或 OOM (内存溢出)。

### 2.3 痛点三：Worker 单点与竞态 (Single Point & Race Condition)
*   **现状**: `worker_cli.py` 设计为单机运行，虽然文件存储已使用 MinIO，但任务调度依赖 MySQL 轮询。
*   **影响**:
    *   **无法横向扩展**: 单纯启动多个 Worker 进程会导致严重的任务冲突。
    *   **竞态风险**: 如果强行启动两个 Worker 进程，它们可能会同时查询到同一批状态为 `NEW` 的记录，导致重复处理、重复 Embedding 计算和 ES 写入冲突。

### 2.4 痛点四：技术迁移遗留债 (Legacy Migration Debt)
*   **现状**: 项目早期使用 Chroma 作为向量数据库，后期升级为 Elasticsearch 实现混合检索。但早期的 `VectorStoreRepository` (基于 Chroma) 代码仍保留在仓库中，且相关的依赖库 (`langchain_chroma`) 仍在 `requirements.txt` 中。
*   **影响**:
    *   **认知干扰**: 新加入的开发者（或自动化工具）难以判断当前生效的存储方案，容易在废弃的代码上浪费时间。
    *   **镜像臃肿**: 包含不再使用的第三方库依赖，增加了 Docker 镜像的体积和构建时间。
    *   **误用风险**: 如果未清理的配置被错误激活，可能导致双写或数据不一致。

### 2.5 痛点五：缺乏熔断与降级 (No Circuit Breaker)
*   **现状**: API 直接调用 ES 和 MinIO。
*   **影响**:
    *   如果 ES 负载过高或宕机，API 会一直重试直到超时。这会引起 **雪崩效应 (Avalanche)**，把原本就脆弱的 ES 彻底打死。
    *   用户端体验极差，直接看到 500 错误。

## 3. 优化解决方案 (Optimization Strategy)

### 3.1 清理历史遗留代码 (Clean up Legacy Debt)
*   **方案**: **彻底移除 Chroma 相关代码与依赖**。
*   **理由**: 既然项目已成功升级为 ES 混合检索，保留旧的 Chroma 实现已无价值，反而成为维护负担。
*   **具体动作**:
    1.  删除 `backend/knowledge/repositories/vector_store_repository.py`。
    2.  清理 `requirements.txt` 中与 Chroma 相关的依赖 (`langchain_chroma`)。
    3.  更新项目文档，明确标记 Elasticsearch 为唯一向量存储后端。

### 3.2 异步化改造 (Async Upgrade)
*   **方案**: 全面引入 `asyncio`。
*   **具体动作**:
    1.  **Web 层**: 将 FastAPI 的 Router 全部改为 `async def`。
    2.  **ES 客户端**: 迁移至 `AsyncElasticsearch`。
    3.  **爬虫**: 使用 `aiohttp` 或 `httpx` (Async) 替代 `requests`。
*   **预期收益**: 单机并发能力提升 10-50 倍。

### 3.3 向量检索加速 (Vector Acceleration)
*   **方案**: 弃用 `script_score`，采用 **HNSW (Hierarchical Navigable Small World)** 索引。
*   **具体动作**:
    *   **选项 A (ES 8.x 原生)**: 使用 ES 的 `dense_vector` 类型并开启 `index: true` (基于 HNSW)。这将检索复杂度降低到 **O(log N)**。
    *   **选项 B (专用向量库)**: 引入 **Milvus** 或 **Qdrant** 专门处理向量检索，ES 只负责倒排索引，最后在应用层做 ID 融合。
*   **预期收益**: 千万级数据量下，检索延迟稳定在 50ms 以内。

### 3.4 分布式 Worker 改造 (Distributed Worker)
*   **方案**: 引入 **Redis 分布式锁** 或 **消息队列** 解决任务竞争。
*   **具体动作**:
    1.  **任务分发**: 爬取任务不再直接查 MySQL，而是推送到 Redis List 或 RabbitMQ（生产者-消费者模型）。
    2.  **抢占锁**: 或者保持 MySQL 轮询，但 Worker 在处理任务前，必须先获取 `lock:knowledge:{id}` 的 Redis 锁，确保同一任务同一时间只有一个 Worker 在处理。
    3.  **幂等性增强**: 在 `DocumentSyncService` 中增加更严格的数据库唯一键约束或状态检查 (CAS)。
*   **预期收益**: 支持动态扩缩容，Worker 数量可随任务量自动增减，且互不冲突。

### 3.5 熔断与降级策略 (Resilience Patterns)
*   **方案**: 引入 **Circuit Breaker (熔断器)** 模式。
*   **具体动作**:
    *   使用 `pybreaker` 或类似库包裹外部调用。
    *   **策略**:
        *   当 ES 错误率 > 50% 时，自动熔断 30秒。
        *   **降级 (Fallback)**: 熔断期间，返回“系统繁忙，请稍后”或只查询本地缓存 (Local Cache)。
*   **预期收益**: 保证在核心组件故障时，系统依然存活（Fail Fast），保护下游服务。

## 4. 实施排期建议

| 优先级 | 优化项 | 实施阶段 | 理由 |
| :--- | :--- | :--- | :--- |
| **P0** | **架构统一 (移除 Chroma)** | Phase 1 | 清理技术债务，防止后续开发路径分裂。 |
| **P0** | **ES 索引 HNSW 改造** | Phase 1 | 成本最低，收益最高，直接解决量级瓶颈。 |
| **P1** | **Web 层异步化** | Phase 1 | 解决高并发下的 Web 容器阻塞问题。 |
| **P2** | **分布式 Worker** | Phase 2 | 仅在数据量巨大需要多机爬取时才紧迫。 |
| **P3** | **熔断降级** | Phase 3 | 属于系统稳定性的“最后一道防线”。 |
