# Elasticsearch 向量存储与检索原理

> **定位**：学习文档，帮助理解 ES 向量检索的底层机制，以及本项目为何从 `script_score` 迁移到原生 `knn`。

---

## 一、向量存储

ES 用 `dense_vector` 字段类型存储向量：

```json
"content_vector": {
    "type": "dense_vector",
    "dims": 1024,           // 向量维度，必须固定，与 Embedding 模型输出一致
    "index": true,          // 开启后才能用 knn 查询，同时会构建 HNSW 图索引
    "similarity": "cosine"  // 相似度算法：cosine / dot_product / l2_norm
}
```

**`index: true` 做了什么？**

开启后 ES 在**写入**文档时会额外构建一个 **HNSW 图索引**，类似数据库的 B-Tree 索引，专门加速向量近邻查找。关闭则只是原始存储，查询时必须全量扫描。

---

## 二、两种向量检索方式对比

### 方式一：`script_score`（暴力枚举）

```python
{
    "query": {
        "bool": {
            "must": [{
                "script_score": {
                    "query": {"match_all": {}},   # 取出全部文档
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0"
                    }
                }
            }]
        }
    }
}
```

**执行流程：**
```
查询进来
  ↓
取出索引中【全部】文档
  ↓
对每一条文档：计算 cosine(query_vec, doc_vec)
  ↓
按分数排序，取 Top-K
```

- 复杂度：**O(n)**，10万条文档算10万次余弦计算
- 优点：结果精确，无近似误差
- 缺点：数据量越大越慢，并发时 CPU 压力极大

---

### 方式二：`knn` 原生查询（HNSW 索引）

```python
{
    "knn": {
        "field": "content_vector",
        "query_vector": query_vector,
        "k": 15,                          # 最终返回数量
        "num_candidates": 150,            # HNSW 探索的候选节点数
        "filter": {"term": {"doc_type": "chunk"}}  # 前置过滤
    },
    "size": 15
}
```

**执行流程：**
```
查询进来
  ↓
在 HNSW 图中"导航"，贪心地找近邻
  ↓
只访问少量节点
  ↓
返回 Top-K
```

- 复杂度：**O(log n)**
- 优点：速度极快，数据量越大优势越明显
- 缺点：近似结果（ANN），存在极小概率漏掉最优解

---

## 三、HNSW 算法详解

**Hierarchical Navigable Small World（分层可导航小世界图）**

### 3.1 核心思想类比：找人问路

```
第 0 层（最稀疏）：全国高速公路网 → 快速定位大区域
第 1 层：省道网                   → 缩小到城市
第 2 层（最密集）：街道网          → 精确定位目标
```

层数越高，节点越少，每一跳跨度越大；层数越低，节点越多，精度越高。

### 3.2 写入过程（建图）

每个新向量写入时：
1. 随机分配到某一最高层（层数越高概率越低）
2. 从顶层开始，找到当前层中最近的 `M` 个邻居，建立双向边
3. 逐层下降，直到第 0 层
4. 整个图在所有写入完成后形成"小世界"结构

```
写入向量 v
  ↓
随机决定插入到第 L 层
  ↓
从顶层到第 L+1 层：贪心找最近节点（不建边，只导航）
  ↓
从第 L 层到第 0 层：找最近的 M 个节点，建立双向边
```

### 3.3 查询过程（导航）

```
从顶层固定入口节点出发
  ↓
贪心移动：每次跳到当前邻居中离 query 最近的节点
  ↓
到达当前层局部最优点后，下降到下一层
  ↓
在第 0 层（最密集）扩大探索范围（由 num_candidates 控制）
  ↓
收集候选集，按真实距离排序，返回 Top-K
```

### 3.4 关键参数

| 参数 | 含义 | 影响 |
|------|------|------|
| `k` | 最终返回的近邻数量 | 直接影响召回数量 |
| `num_candidates` | 底层探索的候选节点数 | 越大越准，越大越慢（建议 `k * 10`） |
| `M`（建图参数） | 每个节点的最大邻居数 | 越大图越密，查询越准，内存越大 |
| `ef_construction`（建图参数） | 建图时的探索宽度 | 越大建图越慢，但图质量越高 |

---

## 四、为什么是"近似"最近邻（ANN）

HNSW 的贪心导航策略可能陷入**局部最优**，错过真正最近的点：

```
真正最近邻 A ──────────── 距离 0.95
                           ↑ 可能因导航路径问题被跳过
当前找到的 B ──────────── 距离 0.93
```

但实际工程表现：
- 召回率通常在 **95%~99%** 以上
- 速度比精确搜索快 **100 倍以上**
- RAG 场景：5% 的近似误差对最终答案质量影响可忽略不计

---

## 五、`knn` 与 BM25 混合检索（Hybrid Search）

ES 8.x 支持 `knn` 和 `query` 并排，实现原生混合检索：

```python
{
    "knn": {
        "field": "content_vector",
        "query_vector": query_vector,
        "k": 50,
        "num_candidates": 500,
        "boost": 0.5           # 向量检索权重
    },
    "query": {
        "multi_match": {
            "query": query_text,
            "fields": ["title^2", "content"],
            "boost": 0.5        # BM25 权重
        }
    }
}
```

本项目采用的是**代码层 RRF 融合**（分别执行 BM25 和 KNN，Python 层合并排名），效果等价，控制更灵活。

---

## 六、对应到本项目

```
入库（es_ingestion_processor.py）
  chunk 文本
    → Embedding API (阿里百炼)
    → 1024 维向量
    → 写入 ES content_vector 字段
    → ES 自动更新 HNSW 图索引

检索（es_retrieval_service.py）
  query 文本
    → Embedding API (阿里百炼)
    → 1024 维向量
    → knn 查询，HNSW 图中导航
    → 返回语义最相近的 Top-K chunks
    → 与 BM25 结果做 RRF 融合
    → Reranker 精排（V3.3 新增）
    → 获取父文档完整内容
    → LLM 生成回答
```

### 升级前后对比

| 维度 | 升级前（script_score） | 升级后（knn） |
|------|----------------------|--------------|
| 算法复杂度 | O(n) 全量扫描 | O(log n) HNSW 导航 |
| 1万条文档延迟 | ~50ms | ~5ms |
| 10万条文档延迟 | ~500ms | ~8ms |
| 并发压力 | 高（每请求全量计算） | 低（索引加速） |
| 结果精度 | 100% 精确 | ~98% 近似（实际无感知） |
| 索引占用 | 无额外开销 | 多占约 10~20% 内存 |

---

## 七、参考资料

- [Elasticsearch 官方文档 - dense_vector](https://www.elastic.co/guide/en/elasticsearch/reference/current/dense-vector.html)
- [Elasticsearch 官方文档 - knn search](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)
- [HNSW 原始论文](https://arxiv.org/abs/1603.09320) - Malkov & Yashunin, 2016
