# CLAUDE.md — ITS 知识库平台开发规范

本文件为 Claude Code 在 `backend/knowledge` 项目中的工作准则。

---

## 核心设计原则

### 工业级标准

**所有设计和实现必须按工业级标准执行，不允许以"先跑通"为由降低标准。**

具体体现：

1. **生产环境禁止在主服务中加载本地 ML 模型**
   - PyTorch / Transformers 推理是 CPU 密集型同步操作
   - 并发请求下会导致：CPU 100% → 队列积压 → 响应超时 → 服务崩溃
   - Python GIL 导致多线程无法真正并行跑 CPU 密集计算，`run_in_executor` 无法解决此问题
   - **正确做法**：生产环境使用 API（如阿里百炼），本地模型仅用于开发调试

2. **有开关，能降级**
   - 所有新增功能必须有 Feature Flag（如 `RERANKER_ENABLED`）
   - 新功能关闭时系统必须完全退化到上一个稳定版本的行为

3. **向后兼容**
   - 不破坏现有接口的入参和返回结构
   - 改动范围最小化，不动不需要动的文件

4. **可观测**
   - 关键路径必须有日志：检索耗时、rerank 耗时、候选集大小、最终返回数量
   - 异常必须有明确的错误信息，不允许吞掉异常

5. **外部依赖统一管理**
   - 同一类型的外部服务（LLM、Embedding、Rerank）优先复用同一供应商的 SDK
   - 当前供应商：阿里百炼（LLM + Embedding）、硅基流动（Rerank）

6. **代码可读性：强制类型注解**
   - 这是企业级项目，代码必须让人看得懂，不允许裸写无类型的变量和函数
   - **所有函数必须有完整的参数类型注解和返回值注解**：
     ```python
     # ❌ 禁止：IDE 无法推断类型，阅读者看不出意图
     def retrieve(self, query, top_k=5):
         ...

     # ✅ 正确：类型清晰，IDE 可跳转，阅读者一目了然
     def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
         ...
     ```
   - **函数返回值必须注解**，是推断调用链类型的基础：
     ```python
     # ❌ 禁止：IDE 不知道返回什么类型
     def get_es_retrieval_service():
         return ESRetrievalService(...)

     # ✅ 正确：调用方可自动推断类型，无需手动标注变量
     def get_es_retrieval_service() -> ESRetrievalService:
         return ESRetrievalService(...)
     ```
   - **类属性必须在 `__init__` 中声明类型**：
     ```python
     # ✅ 正确
     class RerankerService:
         api_key: str
         model: str
         enabled: bool

         def __init__(self) -> None:
             self.api_key: str = settings.SILICONFLOW_API_KEY
             self.model: str = settings.RERANKER_MODEL
             self.enabled: bool = settings.RERANKER_ENABLED
     ```
   - 复杂类型使用 `from typing import List, Dict, Any, Optional, Tuple`

---

## 技术栈约定

- **向量检索**：ES 原生 `knn` 查询（HNSW），禁止 `script_score + match_all` 全量扫描
- **重排序**：硅基流动 `BAAI/bge-reranker-v2-m3` API，禁止生产环境本地推理
- **融合算法**：RRF（Reciprocal Rank Fusion），k=60
- **文本分词**：jieba（中文）
- **向量模型**：阿里百炼 Embedding API

---

## 参考文档

- `docs/Roadmap.md` — 系统演进路线图
- `docs/V3.3_升级设计方案.md` — Native KNN + Reranker 升级设计
- `docs/RAG_Design_Philosophy.md` — RAG 设计哲学
