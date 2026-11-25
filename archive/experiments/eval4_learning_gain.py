# -*- coding: utf-8 -*-
"""
E4 学习增益评估实验：
  A. 模拟 200 学生 × 10 知识点：Hake 归一化增益分布、分档比例、误解纠正率、配对完整性
  B. 真实覆盖率：E2 查询 + LEAR 同节组装上下文，按知识点关键词测 Coverage
输出 experiments/eval4_learning_gain_results.json
"""
import json
import math
import os
import random
import re
import sys

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
QFILE = os.path.join(ROOT, "experiments", "eval2_queries.json")
OUT = os.path.join(ROOT, "experiments", "eval4_learning_gain_results.json")
random.seed(42)

GAIN_BINS = {"low": 0.3, "medium": 0.7}


def part_a():
    """BKT/Hake 模拟（种子固定，可复现）"""
    n_students, n_kp = 200, 10
    g_all, corr_rates, pairing = [], [], {"paired": 0, "total": 0}
    for _ in range(n_students):
        pre = [random.betavariate(2, 5) for _ in range(n_kp)]
        eff = [random.betavariate(5, 2) for _ in range(n_kp)]
        post = [p + (1 - p) * e for p, e in zip(pre, eff)]
        for p, q in zip(pre, post):
            pairing["total"] += 1
            if 0 <= p <= 1 and 0 <= q <= 1:
                pairing["paired"] += 1
            g = (q - p) / (1 - p) if p < 1 else 0.0
            g_all.append(g)
        # 误解纠正率：3 个易错知识点 × 2 次作答（P(对)=掌握度递增）
        errored, corrected = 0, 0
        for kp in range(3):
            m1, m2 = pre[kp], post[kp]
            first = random.random() < m1          # 第一次作答
            if not first:
                errored += 1
                if random.random() < m2:          # 会话后第二次作答
                    corrected += 1
        if errored:
            corr_rates.append(corrected / errored)
    def pct(x):
        return round(100 * x / len(g_all), 1)
    bins = {
        "low(<0.3)": pct(sum(1 for g in g_all if g < 0.3)),
        "medium(0.3-0.7)": pct(sum(1 for g in g_all if 0.3 <= g <= 0.7)),
        "high(>0.7)": pct(sum(1 for g in g_all if g > 0.7)),
    }
    mean = sum(g_all) / len(g_all)
    std = (sum((g - mean) ** 2 for g in g_all) / len(g_all)) ** 0.5
    corr_mean = sum(corr_rates) / len(corr_rates) if corr_rates else None
    return {
        "n_students": n_students, "n_kp": n_kp, "n_pairs": len(g_all),
        "hake_g": {"mean": round(mean, 4), "std": round(std, 4),
                   "min": round(min(g_all), 4), "max": round(max(g_all), 4), "bins_pct": bins},
        "correction_rate": {"mean": round(corr_mean, 4) if corr_mean is not None else None,
                            "n_students_with_errors": len(corr_rates)},
        "pairing_completeness": round(pairing["paired"] / pairing["total"], 4),
    }


def part_b():
    """真实覆盖率：LEAR 组装上下文对单元关键词的覆盖"""
    from data.structure_chunker import StructureChunker, expand_context
    from data.bm25_softmax import BM25Index
    from data.embedding_service import embedding_service as es

    docs = {}
    for chapter in sorted(os.listdir(CORPUS)):
        cdir = os.path.join(CORPUS, chapter)
        if not os.path.isdir(cdir) or not re.match(r"第[一二三四五六七]章", chapter):
            continue
        files = [f for f in os.listdir(cdir) if re.match(r"^\d+\.\d+\s.*\.md$", f)]
        if not files:
            continue
        files.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s.split(" ")[0])])
        parts = [chapter]
        for f in files:
            parts.append(re.sub(r"^#{1,4}\s*", "", open(os.path.join(cdir, f), encoding="utf-8").read(), flags=re.M))
        docs[chapter] = "\n\n".join(parts)

    queries = json.load(open(QFILE, encoding="utf-8"))
    chunker = StructureChunker(max_length=900, min_length=60)
    chunks, by_doc = [], {}
    for doc, text in docs.items():
        tree = chunker.chunk(text, doc_id=doc)
        base = len(chunks)
        for c in tree.chunks:
            d = c.to_dict()
            d["doc_id"] = doc
            chunks.append(d)
        by_doc[doc] = chunks[base:]

    texts = [c["text"] for c in chunks] + [q["query"] for q in queries]
    vecs = []
    for i in range(0, len(texts), 32):
        vecs.extend(es._encode_batch(texts[i:i + 32]))
    c_vecs, q_vecs = vecs[:len(chunks)], vecs[len(chunks):]

    import numpy as np
    mat = np.asarray(c_vecs, dtype="float32")
    mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
    bm25 = BM25Index()
    bm25.build([{"id": i, "text": c["text"]} for i, c in enumerate(chunks)])

    def kp_terms(unit_text):
        """从单元文本抽 3 个关键词作为问题所需知识点"""
        words = re.findall(r"[\u4e00-\u9fff]{3,6}", unit_text)
        seen, out = set(), []
        for w in words:
            if w not in seen:
                seen.add(w)
                out.append(w)
            if len(out) >= 3:
                break
        return out

    covs = []
    for qi, q in enumerate(queries):
        text = docs[q["doc"]]
        unit = text[q["unit_start"]:q["unit_end"]]
        kps = kp_terms(unit)
        if not kps:
            continue
        qv = np.asarray(q_vecs[qi], dtype="float32")
        sims = mat @ qv
        top = np.argsort(-sims)[:5]
        scores = {}
        for rank, cid in enumerate(top):
            scores[int(cid)] = scores.get(int(cid), 0) + 1.0 / (60 + rank + 1)
        for rank, (cid, _) in enumerate(bm25.search(q["query"], 5)):
            scores[cid] = scores.get(cid, 0) + 1.0 / (60 + rank + 1)
        fused = sorted(scores.items(), key=lambda x: -x[1])[:3]
        ctx = ""
        for cid, _ in fused:
            hit = chunks[cid]
            got = expand_context([hit], by_doc.get(hit["doc_id"], []), max_chars=4800, neighbor_window=2)
            for g in got:
                ctx += g.get("context_text", "")
        covered = sum(1 for kp in kps if kp in ctx)
        covs.append(covered / len(kps))
    return {
        "n_queries": len(covs),
        "coverage_mean": round(sum(covs) / len(covs), 4) if covs else None,
        "coverage_full": round(sum(1 for c in covs if c >= 1.0) / len(covs), 4) if covs else None,
    }


def main():
    a = part_a()
    print("part A:", json.dumps(a, ensure_ascii=False))
    b = part_b()
    print("part B:", json.dumps(b, ensure_ascii=False))
    results = {"simulation": a, "real_coverage": b}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
