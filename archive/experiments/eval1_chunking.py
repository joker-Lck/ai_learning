# -*- coding: utf-8 -*-
"""
E1 分块质量实验 v2：结构感知分块 vs 固定长度分块
对照论文主张：
  A 单元对齐率  —— 教学语义标记处硬边界（单元起点=块起点）
  B 单元纯度    —— 一块只含一种教学语义类型（固定切分会混切）
  C 句边界完整  —— 块不从句子中间截断
  D 上下文完整率 —— 同节邻域组装后覆盖完整语义单元（证明链主张）
  E 跨节噪声    —— 组装上下文混入其他小节内容
"""
import json
import os
import re
import sys

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from data.structure_chunker import StructureChunker, expand_context  # noqa: E402

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
OUT = os.path.join(ROOT, "experiments", "eval1_chunking_results.json")

UNIT_START = re.compile(
    r"(?:^\*\*(定义|定理|引理|推论|性质|公式|例)\s*(\d+)?\*\*)"
    r"|(?:^(证|证明|解)\s*[：:])"
    r"|(?:^(注意)\s*[：:])",
    re.M,
)
KIND_MAP = {"定义": "definition", "定理": "theorem", "引理": "theorem", "推论": "theorem",
            "性质": "theorem", "公式": "theorem", "例": "example",
            "证": "proof", "证明": "proof", "解": "proof", "注意": "note"}
SENT_END = re.compile(r"[。！？；!?;]")


def load_docs():
    docs = []
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
            t = open(os.path.join(cdir, f), encoding="utf-8").read()
            t = re.sub(r"^#{1,4}\s*", "", t, flags=re.M)
            parts.append(t)
        docs.append({"title": chapter, "text": "\n\n".join(parts)})
    return docs


def gt_units(text):
    units = []
    for m in UNIT_START.finditer(text):
        label = m.group(1) or m.group(3) or m.group(4)
        units.append({"start": m.start(), "label": label, "kind": KIND_MAP[label]})
    for i, u in enumerate(units):
        u["end"] = units[i + 1]["start"] if i + 1 < len(units) else len(text)
    return units


def fixed_chunks(text, size=700):
    return [{"char_start": i, "char_end": min(i + size, len(text)), "text": text[i:i + size],
             "section_path": "", "kind": "body"}
            for i in range(0, len(text), size)]


def main():
    docs = load_docs()
    chunker = StructureChunker(max_length=900, min_length=60)
    tot = {
        "units": 0, "align": {"struct": 0, "fixed": 0},
        "purity": {"struct": [0, 0], "fixed": [0, 0]},          # [纯块数, 总块数]
        "sent_boundary": {"struct": [0, 0], "fixed": [0, 0]},   # [句边界结尾块, 总块数]
        "ctx_full": {"struct": [0, 0], "fixed": [0, 0], "nofilter": [0, 0]},  # [完整单元, 总单元]
        "noise": {"struct": 0, "fixed": 0, "nofilter": 0},                     # 组装上下文含异节块的次数
        "chunks": {"struct": 0, "fixed": 0},
        "oversized": 0,
    }
    unit_n = {"definition": 0, "theorem": 0, "example": 0, "proof": 0, "note": 0}

    for d in docs:
        text = d["text"]
        units = gt_units(text)
        for u in units:
            unit_n[u["kind"]] += 1
        tot["units"] += len(units)

        tree = chunker.chunk(text, doc_id=d["title"])
        s_chunks = [c.to_dict() for c in tree.chunks]
        for c in s_chunks:
            c.setdefault("section_path", c.get("section_path", ""))
        f_chunks = fixed_chunks(text, 700)
        tot["chunks"]["struct"] += len(s_chunks)
        tot["chunks"]["fixed"] += len(f_chunks)

        def section_of(pos):
            # 位置 → 所属小节标题（用原文中的 1.x 标题行划分）
            return None

        for label, chunks in (("struct", s_chunks), ("fixed", f_chunks)):
            starts = {c["char_start"] for c in chunks}
            # A 单元对齐
            for u in units:
                if u["start"] in starts or (label == "fixed" and u["start"] % 700 == 0):
                    tot["align"][label] += 1
            # B 单元纯度：块内单元种类 <=1（不含任何单元起点穿过块内部的两侧）
            for c in chunks:
                inside = [u for u in units if u["start"] < c["char_end"] and u["end"] > c["char_start"]]
                tot["purity"][label][1] += 1
                if len({u["kind"] for u in inside}) <= 1:
                    tot["purity"][label][0] += 1
            # C 句边界完整：块末尾是句读/空白/文末，或下一块以语义标记硬边界开头
            starts_with_marker = [
                bool(UNIT_START.match(text[c["char_start"]:c["char_start"] + 20])) for c in chunks
            ]
            for ci, c in enumerate(chunks):
                tot["sent_boundary"][label][1] += 1
                tail = text[c["char_end"] - 1] if 0 < c["char_end"] <= len(text) else ""
                nxt = text[c["char_end"]] if c["char_end"] < len(text) else ""
                next_is_marker = ci + 1 < len(chunks) and starts_with_marker[ci + 1]
                if tail in "。！？；!?;\n" or nxt == "" or nxt in "\n" or c["char_end"] >= len(text) or next_is_marker:
                    tot["sent_boundary"][label][0] += 1

        # D/E 上下文组装：等预算 4800 字对比
        #   struct：expand_context 大邻域 + 预算截断（同节约束生效）
        #   fixed：命中块向外扩到同预算（无同节约束 = Cross-Section 消融）
        BUDGET = 4800
        for u in units:
            span = u["end"] - u["start"]
            if span < 30:
                continue
            if span > BUDGET:
                tot["oversized"] += 1  # 超预算单元任何方法都无法全覆盖，单独计数
                continue
            # 结构：命中块 = 覆盖单元起点的块
            hit = next((c for c in s_chunks if c["char_start"] <= u["start"] < c["char_end"]), None)
            if hit:
                by_id = {c["chunk_id"]: c for c in s_chunks}
                # w 按平均块长反推，使邻域≈预算（论文：预算 B 驱动的对称邻域）
                avg_len = max(1, sum(len(c["text"]) for c in s_chunks) / max(len(s_chunks), 1))
                w = max(1, int(BUDGET / avg_len / 2))
                got = expand_context([hit], s_chunks, max_chars=BUDGET, neighbor_window=w)
                covered = 0
                used_paths = set()
                for g in got:
                    used_paths.add(g.get("section_path") or "")
                    for cid in g.get("chunk_ids") or []:
                        cc = by_id.get(cid)
                        if not cc:
                            continue
                        s0, s1 = cc["char_start"], cc["char_end"]
                        covered += max(0, min(s1, u["end"]) - max(s0, u["start"]))
                tot["ctx_full"]["struct"][1] += 1
                if covered / span >= 0.95:
                    tot["ctx_full"]["struct"][0] += 1
                # 跨节噪声：组装结果里出现与命中块不同的小节
                hit_path = hit.get("section_path") or ""
                if any(p != hit_path for p in used_paths):
                    tot["noise"]["struct"] += 1

            # 消融臂：结构分块 + 去除同节约束（Cross-Section）
            if hit:
                order_sorted = sorted(s_chunks, key=lambda x: x.get("order", 0))
                center_idx = next((i for i, c in enumerate(order_sorted) if c is hit), 0)
                picked = []
                total = 0
                for delta in range(len(order_sorted)):
                    for idx in ([center_idx + delta, center_idx - delta] if delta else [center_idx]):
                        if not 0 <= idx < len(order_sorted):
                            continue
                        c = order_sorted[idx]
                        if any(p is c for p in picked):
                            continue
                        seg = c["text"]
                        if total + len(seg) > BUDGET and picked:
                            continue
                        picked.append(c)
                        total += len(seg)
                covered = 0
                paths = set()
                for cc in picked:
                    paths.add(cc.get("section_path") or "")
                    covered += max(0, min(cc["char_end"], u["end"]) - max(cc["char_start"], u["start"]))
                tot["ctx_full"]["nofilter"][1] += 1
                if covered / span >= 0.95:
                    tot["ctx_full"]["nofilter"][0] += 1
                if any(p != (hit.get("section_path") or "") for p in paths):
                    tot["noise"]["nofilter"] += 1

            # 固定基线：以固定块为单位做无同节约束的邻域拼接
            hit_f = next((c for c in f_chunks if c["char_start"] <= u["start"] < c["char_end"]), None)
            if hit_f:
                idx = f_chunks.index(hit_f)
                # 以命中块为中心向外扩到 ~BUDGET 字符（无同节约束）
                window = [f_chunks[idx]]
                total = len(f_chunks[idx]["text"])
                lo, hi = idx - 1, idx + 1
                while total < BUDGET and (lo >= 0 or hi < len(f_chunks)):
                    if hi < len(f_chunks):
                        window.append(f_chunks[hi])
                        total += len(f_chunks[hi]["text"])
                        hi += 1
                    if total >= BUDGET:
                        break
                    if lo >= 0:
                        window.append(f_chunks[lo])
                        total += len(f_chunks[lo]["text"])
                        lo -= 1
                joined = "".join(x["text"] for x in sorted(window, key=lambda x: x["char_start"]))
                # 覆盖近似：单元文本是否 95% 出现在拼接中（子串级，按 40 字滑窗采样）
                sample = [u_ for k in range(0, span - 40, 40) for u_ in [text[u["start"] + k: u["start"] + k + 40]]]
                hit_rate = sum(1 for s in sample if s in joined) / max(len(sample), 1)
                tot["ctx_full"]["fixed"][1] += 1
                if hit_rate >= 0.95:
                    tot["ctx_full"]["fixed"][0] += 1
                # 固定基线无小节概念：窗口跨过小节标题 → 记噪声
                joined_span_lo = min(x["char_start"] for x in window)
                joined_span_hi = max(x["char_end"] for x in window)
                # 单元起点两侧 400 字内若出现“1.x”标题线且窗口跨越它 → 噪声
                for m in re.finditer(r"^\d+\.\d+\s+\S", text[joined_span_lo:joined_span_hi], re.M):
                    if not (u["start"] <= joined_span_lo + m.start() < u["end"]):
                        tot["noise"]["fixed"] += 1
                        break

    def pct(a, b):
        return round(a / b, 4) if b else None

    results = {
        "corpus": {"docs": len(docs), "chars": sum(len(d["text"]) for d in docs), "units": tot["units"],
                   "unit_kinds": unit_n},
        "A_unit_alignment": {k: pct(v, tot["units"]) for k, v in tot["align"].items()},
        "B_unit_purity": {k: pct(v[0], v[1]) for k, v in tot["purity"].items()},
        "C_sentence_boundary": {k: pct(v[0], v[1]) for k, v in tot["sent_boundary"].items()},
        "D_context_coverage": {k: pct(v[0], v[1]) for k, v in tot["ctx_full"].items()},
        "D_oversized_units_excluded": tot["oversized"],
        "E_cross_section_noise": {k: tot["noise"][k] for k in ("struct", "nofilter", "fixed")},
        "chunk_counts": tot["chunks"],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
