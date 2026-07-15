# 检索算法详解

## 混合检索架构

系统采用 **KNN + ANN + RRF** 三路混合检索，兼顾语义相似度和关键词精确匹配。

```
用户查询
   │
   ├── KNN 关键词路径 ──→ SQLite FTS5 ──→ Top-K 结果
   │                       (专业术语精确匹配)
   │
   ├── ANN 向量路径 ──→ Embedding(768维) ──→ FAISS ANN ──→ Top-K 结果
   │                                          │
   │                                   三级回退策略
   │                                   ┌──────────────┐
   │                                   │ L1: FAISS 搜索 │
   │                                   │ L2: 惰性构建   │
   │                                   │ L3: 暴力余弦   │
   │                                   └──────────────┘
   │
   └───────────────────────┬───────────────────────────────┐
                           │                               │
                           ▼                               │
              ┌───── RRF 融合排序 ─────────────────────┐   │
              │ RRF(d)=Σ1/(k+rank)                     │   │
              │ 去重 + Top-K 截断                       │   │
              └───────────────────────────────────────┘   │
                           │                               │
                           ▼                               │
                 混合检索结果（基座）                       │
                           │                               │
              ┌────────────┼────────────┐                 │
              ▼            ▼            ▼                 │
           HyDE       RAG-Fusion   Graph-Enhanced         │
           Multi-Query Contextual  策略路由(smart_search)  │
```

## 1. KNN 关键词检索

**技术**：SQLite FTS5 全文索引

- 精确匹配专业术语、公式、代码
- 使用 `CREATE VIRTUAL TABLE ... USING fts5(tokenize='unicode61')` 创建
- 配合同步触发器维护索引

## 2. ANN 向量检索

**技术**：FAISS IndexFlatIP

| 参数 | 值 | 说明 |
|------|------|------|
| 索引类型 | `faiss.IndexFlatIP` | Flat Inner Product |
| 相似度原理 | L2 归一化后内积 | 等价于余弦相似度 |
| 搜索复杂度 | O(n·d) | 精确线性扫描 |
| 向量维度 | 768 | Kimi Moonshot Embedding |
| 并发安全 | `threading.Lock` | 保护所有索引读写 |

### 三级回退策略

| 级别 | 触发条件 | 检索方式 | 响应时间 |
|------|---------|---------|---------|
| L1 | FAISS 就绪 | IndexFlatIP 搜索 | ~5ms |
| L2 | FAISS 可用但索引为空 | 惰性构建后搜索 | ~500ms（首次） |
| L3 | FAISS 不可用 | 暴力余弦 KNN | ~100ms |

## 3. RRF 融合排序

**公式**：

```
RRF_score(d) = Σ 1/(k + rank_i(d))    # k=60
```

KNN 结果 + ANN 结果 → RRF 统一排序 → Top-N 返回。

## 4. 高级检索方法（2023-2026）

系统实现了 **11 种前沿检索策略**，通过 `smart_search()` 统一入口按策略路由。

### 策略列表

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `auto` | 自动选择（短查询用 HyDE，长查询用 RAG-Fusion） | 默认 |
| `knn` | KNN 关键词检索（FTS5 精确匹配） | 专业术语、公式 |
| `ann` | ANN 向量检索（FAISS 语义匹配） | 模糊语义查询 |
| `hybrid` | KNN + ANN + RRF 混合（基座策略） | 通用推荐 |
| `hyde` | 假设性文档嵌入（Gao et al., 2023） | 短查询、概念性问题 |
| `multi_query` | 多查询检索（LangChain, 2023） | 提高召回率 |
| `rag_fusion` | RAG-Fusion + RRF（Raudaschl, 2023） | 通用推荐 |
| `contextual` | 上下文精排（Anthropic, 2024） | 高精度场景 |
| `graph` | 图谱增强检索（Microsoft GraphRAG, 2024） | 有图谱数据时 |
| `hybrid_advl` | 基座 + HyDE + RAG-Fusion 三路 RRF | 平衡速度与精度 |
| `ensemble` | 全部 6 种方法取并集，RRF 融合 | 最全面 |

### HyDE — 假设性文档嵌入

```
用户问题 → LLM 生成假设答案(200-400字) → 向量化 → FAISS 检索
```

- 零侵入，仅改变查询端
- 适合短查询、概念性问题

### Multi-Query — 多查询检索

```
"梯度下降原理" → LLM 改写为 3-5 个变体 → 分别检索 → 合并去重
```

- 提高召回率，捕捉单一查询遗漏的文档

### RAG-Fusion + RRF

多查询 + Reciprocal Rank Fusion 加权融合，当前 RAG 社区最佳实践。

### Contextual Retrieval

为每个 chunk 生成上下文前缀后再嵌入，检索失败率降低 35%。

```
原始: "反向传播通过链式法则计算梯度"
添加上下文后: "[来自《机器学习》第5章·神经网络训练] 反向传播通过链式法则计算梯度"
```

### Graph-Enhanced RAG

```
"梯度下降" → 图谱查找 → [学习率, 损失函数, 梯度爆炸]
→ 扩展查询检索 → 结合图谱关系给出结构化答案
```

## 5. 防幻觉 RAG 交叉验证

| 验证方式 | 说明 |
|---------|------|
| 关键实体提取 + RAG 验证 | 提取声明中的关键实体，在知识库中逐一查找 |
| 交叉验证 + 文本相似度 | 将主回答与多个替代来源比较，Jaccard 相似度 |
| 可信度阈值 | 0.7（置信度 < 0.7 标记为"可能存在幻觉"） |
| 一致性阈值 | 0.6（一致性 < 0.6 标记为不一致） |

## 源文件

| 文件 | 核心类/函数 | 说明 |
|------|-----------|------|
| `data/rag_knowledge_base.py` | `VectorIndexManager`, `RAGKnowledgeBase` | FAISS 向量索引 + 混合检索 |
| `data/embedding_service.py` | `EmbeddingService` | Kimi Moonshot Embedding API（768 维） |
| `services/advanced_retrieval_service.py` | `AdvancedRetrievalService` | 11 种高级检索策略 |
| `services/content_safety_service.py` | `AntiHallucinationService` | 防幻觉验证 |
