# ITS Knowledge System - 架构演进路线图 (Roadmap)

> **文档说明**: 本文档基于现有 V3.2 工业级架构，规划了系统未来的演进方向。重点解决“检索精度天花板”、“多模态盲区”与“被动采集瓶颈”三大挑战。

---

## 阶段一：检索精度突破 (Precision Breakthrough)
**背景**: 当前使用的 Bi-Encoder (向量) + RRF 虽然解决了召回问题，但缺乏对 Query 与 Document 之间细粒度交互的理解能力。

### 1.1 引入 Cross-Encoder 重排序 (Reranking)
*   **痛点**: 向量模型认为 "K900" 和 "K910" 很相似，但用户只想找 "K900"。Bi-Encoder 无法通过简单的点积捕捉这种细微差异。
*   **方案**: 在 RRF 融合后的 Top 50 结果基础上，引入 **Cross-Encoder 模型** (如 `bge-reranker-large`)。
    *   *机制*: 将 (Query, Doc) 拼接输入模型，输出 0-1 的相关性得分。
*   **流程**: `Hybrid Retrieval (Top 50)` -> `Reranker Scoring` -> `Truncate (Top 5)` -> `LLM`。
*   **预期收益**: MRR@10 指标提升 15% 以上，显著减少 LLM 的幻觉。

### 1.2 动态阈值截断 (Dynamic Thresholding)
*   **痛点**: 当前硬编码返回 Top 5。若仅有 1 条相关，会引入 4 条噪音；若有 10 条相关，会漏掉 5 条。
*   **方案**: 实现 **Elbow Method (肘部法则)**。
    *   *算法*: 计算重排分数的导数（斜率）。当分数出现断崖式下跌（Slope > Threshold）时，立即截断结果列表。

---

## 阶段二：多模态内容理解 (Multimodal RAG)
**背景**: 知识库中包含大量蓝屏截图、BIOS 设置图、架构图。当前系统只能处理文本，图片如同“黑洞”。

### 2.1 图片 ETL 流水线
*   **现状**: Markdown 中仅保留原始图片链接，存在防盗链失效风险。
*   **方案**: 
    1.  **Extract**: 爬虫阶段提取所有 `![]()` 链接。
    2.  **Transform**: 下载图片二进制流，转换为标准格式 (WebP/PNG)。
    3.  **Load**: 转存至 MinIO (`knowledge/images/...`) 并重写 Markdown 链接。

### 2.2 视觉语义增强 (Visual Captioning)
*   **方案**: 在 Worker 处理图片时，调用 **VLM (Vision Language Model)**。
    *   *Prompt*: "请详细描述这张图片。如果是报错截图，提取错误代码；如果是架构图，列出关键组件。"
*   **索引增强**: 
    *   将生成的 Caption 插入到 Markdown 图片下方（作为 Hidden Text）。
    *   Caption 参与 Embedding 和 BM25 索引。
*   **效果**: 用户搜索 "蓝屏 0x000000D1"，即可直接命中包含该截图的文档。

---

## 阶段三：主动智能采集 (Agentic Crawling)
**背景**: 当前 Worker 仅被动处理已有的 Markdown 文件，缺乏对外部数据源的主动感知和策略调整。

### 3.1 列表驱动的智能爬虫
*   **现状**: 依赖 `Range(ID)` 暴力枚举，效率低且包含大量无效页面。
*   **方案**: 重构为 **"Monitor (列表页监听) -> Filter (规则过滤) -> Fetch (详情抓取)"** 模式。
    *   *配置化*: 支持 JSON 定义采集源 (`CrawlSource`)。
    *   *增量*: 记录 Last-Modified 时间，仅抓取更新的页面。

### 3.2 智能体筛选 (Agentic Selection)
*   **场景**: 对于高价值、高复杂度的查询（如“对比 Windows 10 和 11 的网络配置差异”）。
*   **方案**: 在检索 Top 20 后，不立即生成答案，而是启动一个 **Agent**。
    *   *Step 1*: Agent 快速浏览 20 篇摘要。
    *   *Step 2*: 剔除过时或无关文档。
    *   *Step 3*: 若信息不足，Agent 主动发起二次搜索 (Query Expansion)。
*   **权衡**: 响应延迟增加 (3-5s)，换取极高的回答质量。

---

## 演进时间表 (Timeline)

| 阶段 | 重点特性 | 关键技术 | 状态 |
| :--- | :--- | :--- | :--- |
| **V3.2 (Current)** | 工业级基座 | N+1 Storage, Atomic Write, RRF Fusion | ✅ 已上线 |
| **V3.3** | 精度优化 | Cross-Encoder Rerank, Dynamic Threshold | 📅 待排期 |
| **V3.4** | 多模态基础 | Image ETL (MinIO), Visual Captioning | 📅 规划中 |
| **V4.0** | 智能体化 | Smart Crawler, Agentic Retrieval | 📅 远期规划 |