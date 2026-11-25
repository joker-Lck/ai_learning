# -*- coding: utf-8 -*-
"""
E2-a 查询生成：为每个语义单元生成学生风格提问（本地 qwen3:14b，think=False）
输出 experiments/eval2_queries.json
"""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
OUT = os.path.join(ROOT, "experiments", "eval2_queries.json")

UNIT_START = re.compile(
    r"(?:^\*\*(定义|定理|引理|推论|性质|公式|例)\s*(\d+)?\*\*)|(?:^(证|证明|解)\s*[：:])|(?:^(注意)\s*[：:])",
    re.M,
)
KIND_MAP = {"定义": "definition", "定理": "theorem", "引理": "theorem", "推论": "theorem",
            "性质": "theorem", "公式": "theorem", "例": "example",
            "证": "proof", "证明": "proof", "解": "proof", "注意": "note"}


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
            t = re.sub(r"^#{1,4}\s*", "", open(os.path.join(cdir, f), encoding="utf-8").read(), flags=re.M)
            parts.append(t)
        docs.append({"doc": chapter, "text": "\n\n".join(parts)})
    return docs


def gt_units(text):
    units = []
    for m in UNIT_START.finditer(text):
        label = m.group(1) or m.group(3) or m.group(4)
        units.append({"start": m.start(), "label": label, "kind": KIND_MAP[label]})
    for i, u in enumerate(units):
        u["end"] = units[i + 1]["start"] if i + 1 < len(units) else len(text)
    return units


def ask_llm(prompt, num_predict=80):
    payload = {
        "model": "qwen3:14b", "prompt": prompt, "stream": False, "think": False,
        "options": {"temperature": 0.3, "num_predict": num_predict},
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return (r.get("response") or "").strip()


def template_query(u, text):
    head = re.sub(r"\s+", " ", text[u["start"]:u["start"] + 60]).strip()
    head = re.sub(r"\*\*|^\*+|\*+$", "", head)
    return f"{head[:24]}的相关内容是什么？"


def main():
    docs = load_docs()
    items = []
    for d in docs:
        for u in gt_units(d["text"]):
            if u["kind"] in ("theorem", "example") and 60 <= u["end"] - u["start"] <= 4000:
                items.append({**u, "doc": d["doc"], "text": d["text"]})
    print(f"candidate units: {len(items)}")

    queries = []
    for i, it in enumerate(items):
        snippet = re.sub(r"\s+", " ", it["text"][it["start"]:it["start"] + 260]).strip()
        snippet = re.sub(r"\$\$.*?\$\$", "[公式]", snippet)
        prompt = (
            "以下是教材中的一段内容。请模拟学生口吻，提出一个能从这段内容得到答案的问题。"
            "只输出问题本身，不超过 30 字，不要任何解释。\n内容：" + snippet
        )
        q = ""
        try:
            q = ask_llm(prompt)
            q = re.sub(r"^(问题|问)[:：]?\s*", "", q).strip().strip("。？?！!")
            if not (4 <= len(q) <= 60) or "内容" in q[:6]:
                q = ""
        except Exception as e:
            print(f"  [{i}] llm fail: {str(e)[:60]}")
        if not q:
            q = template_query(it, it["text"])
        queries.append({
            "query": q,
            "doc": it["doc"],
            "unit_start": it["start"],
            "unit_end": it["end"],
            "kind": it["kind"],
        })
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(items)}] last: {q}")
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(queries, f, ensure_ascii=False, indent=1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=1)
    print(f"saved {len(queries)} queries -> {OUT}")


if __name__ == "__main__":
    main()
