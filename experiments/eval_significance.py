# -*- coding: utf-8 -*-
"""关键指标对比的统计显著性：bootstrap 95% CI + McNemar 配对检验

对比：
- 检索（N=200）：意图路由系统 vs 标题前缀（全查询）；视图B vs 上下文化前缀（术语型）；
  A+标记重排 vs 段落分块（标签型）
- 忠实度（N=401）：符号锚点 vs 词面数字锚点（整体F1方向=检出率R）；公式类召回对比
"""
import sys, os, re, math, random
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
import numpy as np
spec = u.spec_from_file_location("ev", r"F:\项目\ai教学辅助系统\experiments\eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

random.seed(7)
np.random.seed(7)

def mcnemar(b, c):
    """b=系统1命中&系统2未命中，c=系统1未命中&系统2命中；精确二项p值"""
    n = b + c
    if n == 0:
        return 1.0
    k = max(b, c)
    # 双侧精确二项检验
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * p)

def boot_ci(diff_samples, level=0.95):
    lo = np.percentile(diff_samples, (1 - level) / 2 * 100)
    hi = np.percentile(diff_samples, (1 + level) / 2 * 100)
    return float(lo), float(hi)

def paired_bootstrap(y1, y2, n_boot=10000):
    """y1/y2: 每样本 0/1 命中；返回 (diff, CI, mcnemar_p)"""
    y1, y2 = np.asarray(y1, float), np.asarray(y2, float)
    n = len(y1)
    diff = float(y1.mean() - y2.mean())
    idx = np.random.randint(0, n, size=(n_boot, n))
    diffs = y1[idx].mean(1) - y2[idx].mean(1)
    lo, hi = boot_ci(diffs)
    b = int(((y1 == 1) & (y2 == 0)).sum())
    c = int(((y1 == 0) & (y2 == 1)).sum())
    return diff, lo, hi, mcnemar(b, c)

# ── 检索：构造各系统每查询命中向量 ──
docs = ev.load_corpus()
golds = ev.extract_gold(docs)
queries = ev.build_queries(golds)

viewA, viewB, fixed, para_, titlep, ctxp = [], [], [], [], [], []
for di, d in enumerate(docs):
    viewA += ev.chunks_lear(d["text"], d["section"], di)
    clus = ev.chunks_lear_clustered(d["text"], d["section"], di)
    head = re.sub(r"\s+", " ", d["text"])[:80]
    viewB += [{**c, "text": f"{c['section_path']} >> {head} >> {c['raw']}"} for c in clus]
    fixed += ev.chunks_fixed(d["text"], d["section"])
    para_ += ev.chunks_para(d["text"], d["section"])
    titlep += ev.chunks_title_prefix(d["text"], d["section"])
    ctxp += ev.chunks_ctx_prefix(d["text"], d["section"])

def hit_vectors(view):
    cmat = ev.embed_batch([c["text"] for c in view])
    qmat = ev.embed_batch([it["q"] for it in queries])
    cnorm = cmat / (np.linalg.norm(cmat, axis=1, keepdims=True) + 1e-9)
    out = []
    ranks_all = []
    for qi in range(len(queries)):
        q = qmat[qi] / (np.linalg.norm(qmat[qi]) + 1e-9)
        ranked = list(np.argsort(-(cnorm @ q))[:20])
        ranks_all.append(ranked)
        rels = [1 if ev.hit_any(queries[qi]["gold_texts"], view[ci]["raw"]) else 0 for ci in ranked[:5]]
        out.append(1 if any(rels) else 0)
    return out, ranks_all

print("编码各视图...")
hA, rA = hit_vectors(viewA)
hB, _ = hit_vectors(viewB)
hT, _ = hit_vectors(titlep)
hC, _ = hit_vectors(ctxp)
hP, _ = hit_vectors(para_)

# A+标记重排：label 查询在 A 候选上标记重排
hAb = []
for qi, it in enumerate(queries):
    ranked = list(rA[qi])
    if it["qtype"] == "标签型":
        m = re.search(r"(定义|定理|引理|例题|例|公式)\s*(\d+)", it["q"])
        if m:
            pat = re.compile(rf"\*{{0,2}}\s*{m.group(1)}\s*{m.group(2)}\b")
            front = [ci for ci in ranked if pat.search(viewA[ci]["raw"][:30])]
            rest = [ci for ci in ranked if ci not in set(front)]
            ranked = front + rest
    rels = [1 if ev.hit_any(it["gold_texts"], viewA[ci]["raw"]) else 0 for ci in ranked[:5]]
    hAb.append(1 if any(rels) else 0)

# 意图路由 = label→A_boost, term→B
hRoute = [(hAb[i] if queries[i]["qtype"] == "标签型" else hB[i]) for i in range(len(queries))]

types = [q["qtype"] for q in queries]
term_ix = [i for i, t in enumerate(types) if t == "术语型"]
label_ix = [i for i, t in enumerate(types) if t == "标签型"]

print("\n== 检索显著性（全查询，N=%d）==" % len(queries))
d, lo, hi, p = paired_bootstrap(hRoute, hT)
print(f"RESULT 意图路由 vs 标题前缀: diff={d:.4f} CI95=[{lo:.4f},{hi:.4f}] mcnemar_p={p:.2e}")
print("== 术语型（N=%d）==" % len(term_ix))
d, lo, hi, p = paired_bootstrap([hB[i] for i in term_ix], [hC[i] for i in term_ix])
print(f"RESULT 视图B vs 上下文化前缀: diff={d:.4f} CI95=[{lo:.4f},{hi:.4f}] mcnemar_p={p:.2e}")
print("== 标签型（N=%d）==" % len(label_ix))
d, lo, hi, p = paired_bootstrap([hAb[i] for i in label_ix], [hP[i] for i in label_ix])
print(f"RESULT A+标记重排 vs 段落分块: diff={d:.4f} CI95=[{lo:.4f},{hi:.4f}] mcnemar_p={p:.2e}")

# ── 忠实度显著性 ──
ch = ev.build_challenge(golds)
items = sum(ch.values(), [])
sym = ev.make_flag(True, True, True)
lex = ev.flag_lexical_num
ys = [1 if sym(it["claim"], it["evidence"]) else 0 for it in items]
yl = [1 if lex(it["claim"], it["evidence"]) else 0 for it in items]
labels = [it["label"] for it in items]
# 检出率（=召回方向）在负例子集上比较
neg = [i for i, lb in enumerate(labels) if lb == 1]
d, lo, hi, p = paired_bootstrap([ys[i] for i in neg], [yl[i] for i in neg])
print(f"\n== 忠实度（负例检出率，N={len(neg)}）==")
print(f"RESULT 符号锚点 vs 词面数字: diff={d:.4f} CI95=[{lo:.4f},{hi:.4f}] mcnemar_p={p:.2e}")
fn = [i for i in neg if "公式" in str(items[i].get("_cat", "")) or True]
# 公式类单独
fitems = ch["公式改写"]
yf_s = [1 if sym(it["claim"], it["evidence"]) else 0 for it in fitems]
yf_l = [1 if lex(it["claim"], it["evidence"]) else 0 for it in fitems]
d, lo, hi, p = paired_bootstrap(yf_s, yf_l)
print(f"== 公式改写类检出（N={len(fitems)}）==")
print(f"RESULT 符号锚点 vs 词面数字: diff={d:.4f} CI95=[{lo:.4f},{hi:.4f}] mcnemar_p={p:.2e}")
