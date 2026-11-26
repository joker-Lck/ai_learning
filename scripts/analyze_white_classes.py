# -*- coding: utf-8 -*-
"""扫描前端剩余黑白硬编码模式。"""
import re, os, collections, sys

sys.stdout.reconfigure(encoding="utf-8")

pats = {
    "bg_black": r"bg-black[^\s\"']*",
    "text_black": r"text-black[^\s\"']*",
    "grad_white": r"(?:from|via|to)-white[^\s\"']*",
    "svg_white": r"(?:fill|stroke)=\"#[0-9a-fA-F]{3,6}\"",
    "hex_fff": r"#fff\b|#ffffff",
    "hex_0a": r"#0a0a0a",
    "hex_1a": r"#1a1a2[0-9a-f]",
    "hex_e2": r"#e2e8f0|#e0e0e0|#f5f5f5",
    "purple_cls": r"purple-[0-9]+",
    "cyan_cls": r"cyan-[0-9]+",
    "gray_hexes": r"#888888|#0f172a|#0d1117|#111111",
}

counts = {k: collections.Counter() for k in pats}
files_hit = collections.defaultdict(set)

for root, dirs, files in os.walk("frontend"):
    dirs[:] = [d for d in dirs if d not in ("node_modules", ".next")]
    for f in files:
        if f.endswith((".tsx", ".ts", ".css")):
            p = os.path.join(root, f)
            text = open(p, encoding="utf-8", errors="replace").read()
            for k, pat in pats.items():
                found = re.findall(pat, text)
                if found:
                    counts[k].update(found)
                    files_hit[k].add(f)

for k, c in counts.items():
    total = sum(c.values())
    print(f"=== {k}: {total}  ({len(files_hit[k])} files)")
    for name, n in c.most_common(10):
        print(f"   {n:4d}  {name}")
