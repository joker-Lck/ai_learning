# -*- coding: utf-8 -*-
"""风险分解界核验：总漏检 = c·ε_片段内 + (1−c)·ε_解析失败 ≤ c·ε_片段内 + (1−c)

逐样本标注：公式是否可解析（claim 提取到公式 且 证据含公式）× 是否被门控检出。
"""
import sys, os, re
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
spec = u.spec_from_file_location("ev", r"F:\项目\ai教学辅助系统\experiments\eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

from services.faithfulness_verifier import FaithfulnessVerifier, _FORMULA_RE

golds = ev.extract_gold(ev.load_corpus())
ch = ev.build_challenge(golds)
v = FaithfulnessVerifier()

def is_parsed(claim, evidence):
    ev_all = "\n".join(e.get("content_text", "") for e in evidence)
    has_c = bool(_FORMULA_RE.search(claim))
    has_e = bool(_FORMULA_RE.search(ev_all))
    return has_c and has_e

def flagged(claim, evidence):
    rep = v.verify(claim, evidence)
    return any(c.missing_numbers or c.status == "unsupported" for c in rep.claims)

def decompose(items, name):
    n = len(items)
    parse_hit = miss_parse = hit_parse = miss_gap = 0
    n_parsed = 0
    for it in items:
        parsed = is_parsed(it["claim"], it["evidence"])
        det = flagged(it["claim"], it["evidence"])
        if parsed:
            n_parsed += 1
            if det:
                hit_parse += 1
            else:
                miss_parse += 1
        else:
            if det:
                pass  # gap 组检出（少见）
            else:
                miss_gap += 1
    c = n_parsed / n if n else 0.0
    eps_frag = miss_parse / n_parsed if n_parsed else 0.0
    eps_gap = miss_gap / (n - n_parsed) if (n - n_parsed) else 0.0
    eps_total = (miss_parse + miss_gap) / n if n else 0.0
    bound = c * eps_frag + (1 - c) * 1.0
    print(f"RESULT[{name}] n={n} parsed={n_parsed} c={c:.4f} "
          f"eps_frag={eps_frag:.4f} eps_gap={eps_gap:.4f} eps_total={eps_total:.4f} "
          f"bound(=c*eps_frag+(1-c))={bound:.4f} holds={eps_total <= bound + 1e-9} "
          f"parse_improvement_headroom={1 - c:.4f}")

decompose(ch["公式改写"], "公式改写")
decompose(ch["数值篡改(数字集保持)"], "数值篡改")
decompose(ch["绑定值篡改(数字集保持)"], "绑定值篡改")
decompose(ch["无支撑"], "无支撑")
