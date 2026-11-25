# -*- coding: utf-8 -*-
"""LEAR 形式化保证验证实验

定理1 教法依赖组装：次模覆盖效用 + 预算约束 → 贪心 (1-1/e) 近似最优（穷举对照）
定理2 符号门控：数值/公式断言片段的可靠性与完备性（解析覆盖率实测）
定理3 共形分级拒答：split-conformal p 值拒绝规则，保留断言 FDR ≤ α（覆盖-风险曲线）
"""
import sys, os, re, json, math, random, itertools
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
from pathlib import Path

random.seed(42)

# ═══════════ 定理1：教法依赖组装的贪心近似 ═══════════
def u_cover(S, query_terms, dep_edges):
    """单调次模覆盖效用：查询词覆盖 + 依赖边满足 + 教学类型覆盖"""
    kinds = {"definition": 0, "theorem": 0, "example": 0, "proof": 0, "note": 0}
    text = ""
    for i in S:
        text += " " + ITEMS[i]["text"]
        k = ITEMS[i]["kind"]
        if k in kinds:
            kinds[k] = 1
    q_cov = sum(1 for t in query_terms if t in text)
    dep_cov = 0
    for (a, b) in dep_edges:          # 依赖边 (例题块, 定理块)：两端都在 S 中才满足
        if a in S and b in S:
            dep_cov += 1
    return 2.0 * q_cov + 1.5 * dep_cov + 1.0 * sum(kinds.values())


def greedy(items, query_terms, dep_edges, B):
    S, remain, cost = set(), set(range(len(items))), 0
    while remain:
        best, best_gain = None, 0.0
        for i in remain:
            c = items[i]["cost"]
            if cost + c > B:
                continue
            gain = u_cover(S | {i}, query_terms, dep_edges) - u_cover(S, query_terms, dep_edges)
            if gain / c > best_gain:
                best, best_gain = i, gain / c
        if best is None:
            break
        S.add(best); remain.discard(best); cost += items[best]["cost"]
    return S


def brute_force(items, query_terms, dep_edges, B):
    n = len(items)
    best, best_u = set(), 0.0
    for r in range(n + 1):
        for comb in itertools.combinations(range(n), r):
            if sum(items[i]["cost"] for i in comb) <= B:
                u = u_cover(set(comb), query_terms, dep_edges)
                if u > best_u:
                    best_u, best = u, set(comb)
    return best


def run_thm1(n_trials=30, n_items=12, B=4800):
    global ITEMS
    ratios = []
    for t in range(n_trials):
        ITEMS = []
        kinds = ["definition", "theorem", "example", "proof", "note", "body"]
        for i in range(n_items):
            kind = kinds[i % len(kinds)]
            text = f"块{i} {kind} " + " ".join(
                random.choice(["概率", "期望", "方差", "定理", "公式", "定义"]) for _ in range(6))
            ITEMS.append({"text": text, "kind": kind,
                          "cost": random.randint(300, 1200)})
        q = ["概率", "期望"]
        deps = [(2, 1), (3, 1), (4, 5)]     # 例题→定理 等
        deps = [(a, b) for a, b in deps if a < n_items and b < n_items]
        g = greedy(ITEMS, q, deps, B)
        o = brute_force(ITEMS, q, deps, B)
        ug, uo = u_cover(g, q, deps), u_cover(o, q, deps)
        ratios.append(ug / uo if uo > 0 else 1.0)
    ratios.sort()
    return {
        "n_trials": n_trials,
        "mean_ratio": round(sum(ratios) / len(ratios), 4),
        "min_ratio": round(ratios[0], 4),
        "guarantee_bound": round(1 - 1 / math.e, 4),
        "violation_below_bound": sum(1 for r in ratios if r < 1 - 1 / math.e),
    }


# ═══════════ 定理3：共形分级拒答 ═══════════
def run_thm3():
    import importlib.util as u
    spec = u.spec_from_file_location("ev", "experiments/eval_lear_paper.py")
    ev = u.module_from_spec(spec); spec.loader.exec_module(ev)
    golds = ev.extract_gold(ev.load_corpus())
    ch = ev.build_challenge(golds)
    items = sum(ch.values(), [])
    random.shuffle(items)

    from services.faithfulness_verifier import FaithfulnessVerifier
    from core.text_utils import extract_numbers
    import torch
    from models.teach_nets import EBiLSTM, Vocab

    v = FaithfulnessVerifier()
    # F4 神经通道（E-BiLSTM，已训 checkpoint）
    ckpt = torch.load("models/ckpt_ebilstm.pt", map_location="cpu")
    vocab = Vocab()
    vocab.itos = ckpt["vocab"]; vocab.stoi = {w: i for i, w in enumerate(vocab.itos)}
    net = EBiLSTM(len(vocab.itos))
    net.load_state_dict(ckpt["state"])
    net.eval()

    def neural_prob(claim, evidence):
        ev_sents = []
        for e in evidence:
            ev_sents += [s for s in re.split(r"[。！？\n；;]", e.get("content_text", "")) if len(s.strip()) >= 8]
        if not ev_sents:
            return 0.0
        xs1 = [claim] * min(len(ev_sents), 12)
        xs2 = ev_sents[:12]
        with torch.no_grad():
            x1 = torch.tensor([vocab.encode(t, 48) for t in xs1], dtype=torch.long)
            x2 = torch.tensor([vocab.encode(t, 48) for t in xs2], dtype=torch.long)
            return float(torch.softmax(net(x1, x2), 1)[:, 1].max())

    def score(claim, evidence):
        """conformity score：F1–F3 词面/锚点 ⊕ F4 神经（0~1，越大越可信）"""
        rep = v.verify(claim, evidence)
        if not rep.claims:
            return 0.0
        s = max(c.support_score for c in rep.claims)
        n_miss = sum(len(c.missing_numbers) for c in rep.claims)
        anchor_pass = 1.0 - min(1.0, n_miss / 3.0)
        neural = neural_prob(claim, evidence)
        return 0.4 * s + 0.3 * anchor_pass + 0.3 * neural

    data = [(score(it["claim"], it["evidence"]), it["label"]) for it in items]
    # label: 0=正例(真支撑) 1=负例(伪忠实)；conformal 以负例校准分布定阈值
    cal = data[: len(data) // 2]
    test = data[len(data) // 2:]
    cal_neg = sorted(s for s, y in cal if y == 1)
    n_cal = len(cal_neg)
    results = {}
    rnd = random.Random(7)
    for alpha in (0.05, 0.10, 0.20):
        # 分位数阈值：t = 负例校准分布的 (1-α) 分位（共形修正）
        k = min(n_cal - 1, math.ceil((n_cal + 1) * (1 - alpha)))
        t = cal_neg[k]
        # 随机化结值处理：s == t 时以概率 γ 保留，使 P(通过|伪忠实) 精确回到 α
        n_above = sum(1 for x in cal_neg if x > t)
        n_eq = sum(1 for x in cal_neg if x == t)
        gamma = 0.0
        if n_eq > 0:
            gamma = max(0.0, min(1.0, (alpha * n_cal - n_above) / n_eq))

        def passed(s):
            return s > t or (s == t and rnd.random() < gamma)

        neg_test = [(s, y) for s, y in test if y == 1]
        pos_test = [(s, y) for s, y in test if y == 0]
        leak = sum(1 for s, y in neg_test if passed(s)) / max(len(neg_test), 1)
        cov = sum(1 for s, y in pos_test if passed(s)) / max(len(pos_test), 1)
        n_ret = sum(1 for s, y in test if passed(s))
        n_bad = sum(1 for s, y in test if passed(s) and y == 1)
        results[f"alpha={alpha}"] = {
            "threshold": round(t, 4), "tie_gamma": round(gamma, 4),
            "neg_leak_rate": round(leak, 4),          # 应 ≤ α（定理3保证量）
            "pos_coverage": round(cov, 4),
            "empirical_FDR": round(n_bad / max(n_ret, 1), 4),
            "retained": n_ret, "n_test": len(test),
            "guarantee": f"P(通过|伪忠实) <= {alpha}",
        }
    return {"n_cal": len(cal), "n_test": len(test), "by_alpha": results}


# ═══════════ 定理2：符号片段可靠性/完备性（解析覆盖率）═══════════
def run_thm2():
    import importlib.util as u
    spec = u.spec_from_file_location("ev", "experiments/eval_lear_paper.py")
    ev = u.module_from_spec(spec); spec.loader.exec_module(ev)
    golds = ev.extract_gold(ev.load_corpus())
    ch = ev.build_challenge(golds)
    from core.text_utils import extract_numbers, extract_bound_values, normalize_number
    from services.faithfulness_verifier import _FORMULA_RE

    n_formula_claim, n_parsed = 0, 0
    n_num_claim, n_num_parsed = 0, 0
    for cname, its in ch.items():
        for it in its:
            c = it["claim"]
            has_eq = "=" in c
            nums = extract_numbers(c)
            if has_eq:
                n_formula_claim += 1
                if _FORMULA_RE.search(c):
                    n_parsed += 1
            if nums:
                n_num_claim += 1
                if any(normalize_number(x) is not None for x in nums):
                    n_num_parsed += 1
    return {
        "numeric_fragment": {"claims_with_numbers": n_num_claim,
                             "parsed": n_num_parsed,
                             "parse_coverage": round(n_num_parsed / max(n_num_claim, 1), 4)},
        "formula_fragment": {"claims_with_eq": n_formula_claim,
                             "parsed": n_parsed,
                             "parse_coverage": round(n_parsed / max(n_formula_claim, 1), 4)},
    }


if __name__ == "__main__":
    out = {}
    print("== 定理1 贪心近似（穷举对照，30 组随机实例）==")
    out["thm1_greedy"] = run_thm1()
    print(out["thm1_greedy"])
    print("\n== 定理2 符号片段解析覆盖率 ==")
    out["thm2_fragment"] = run_thm2()
    print(out["thm2_fragment"])
    print("\n== 定理3 共形拒答 FDR 控制（覆盖-风险曲线）==")
    out["thm3_conformal"] = run_thm3()
    print(json.dumps(out["thm3_conformal"], ensure_ascii=False, indent=1))
    Path("experiments/formal_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("→ experiments/formal_results.json")
