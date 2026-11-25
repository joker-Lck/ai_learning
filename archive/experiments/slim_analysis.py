# -*- coding: utf-8 -*-
"""仓库瘦身分析：死代码、重复模块、无人引用的文件"""
import ast
import os
import re
from collections import defaultdict

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"
SCAN_DIRS = ["backend", "core", "data", "services", "scripts", "tests", "tools", "experiments", "01_运行启动", "02_打包构建"]
SKIP = {"__pycache__", "node_modules", ".git", ".pytest_cache"}

py_files = []
for d in SCAN_DIRS:
    base = os.path.join(ROOT, d)
    if not os.path.isdir(base):
        continue
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP]
        for fn in filenames:
            if fn.endswith(".py"):
                py_files.append(os.path.join(dirpath, fn))

print(f"py files: {len(py_files)}")

# ── 收集每个文件定义的顶层名字 & 它 import 的项目内模块 ──
defs = {}          # file -> set(defined top-level names)
imports = defaultdict(set)   # file -> set(imported module paths like services.faithfulness_verifier)
module_of = {}     # dotted name -> file

def dotted(path):
    rel = os.path.relpath(path, ROOT)
    parts = rel.split(os.sep)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)

for f in py_files:
    module_of[dotted(f)] = f

for f in py_files:
    try:
        src = open(f, encoding="utf-8", errors="replace").read()
        tree = ast.parse(src)
    except SyntaxError as e:
        print("SYNTAX ERROR", f, e)
        continue
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
    defs[f] = defined
    imps = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imps.add(a.name.split(".")[0] if not a.name.startswith(("data", "services", "core", "backend")) else a.name)
                if a.name.split(".")[0] in ("data", "services", "core", "backend"):
                    imps.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top in ("data", "services", "core", "backend"):
                    imps.add(node.module)
                else:
                    imps.add(top)
                # from data.structure_chunker import X -> 也算引用
                if node.level == 0 and node.module:
                    imps.add(node.module)
    imports[f] = imps

# ── 被引用统计（谁 import 了这个模块）──
referenced_by = defaultdict(set)
all_dotted = set(module_of.keys())
for f, imps in imports.items():
    for imp in imps:
        # 找最长匹配的模块
        for mod in all_dotted:
            if imp == mod or imp.startswith(mod + ".") or mod.startswith(imp + "."):
                referenced_by[module_of[mod]].add(dotted(f))

print("\n=== 疑似死代码（没有任何项目内模块 import 它）===")
dead = []
for f in py_files:
    rel = os.path.relpath(f, ROOT)
    d = dotted(f)
    if d.endswith(".__init__") or d.split(".")[-1] == "__init__":
        continue
    users = {u for u in referenced_by.get(f, set()) if u != d}
    # 入口文件不算死代码
    if any(rel.startswith(p) for p in ("scripts", "tests", "01_", "02_", "experiments", "backend/main", "backend/api", "init_")):
        continue
    if not users:
        dead.append((rel, len(defs.get(f, set()))))
for rel, ndef in sorted(dead):
    print(f"  {rel}  (defs={ndef})")

print("\n=== 高扇入模块（被引用最多）===")
fanin = sorted(((dotted(f), len([u for u in users if u != dotted(f)])) for f, users in referenced_by.items()), key=lambda x: -x[1])
for name, n in fanin[:15]:
    print(f"  {n:3d}  {name}")

# ── 内容相似度（同目录/跨目录重复）──
print("\n=== 内容重复/近重复文件（成对相似度）===")
import hashlib
sigs = {}
for f in py_files:
    src = open(f, encoding="utf-8", errors="replace").read()
    # 归一化：去注释、去空行
    lines = [l.strip() for l in src.splitlines() if l.strip() and not l.strip().startswith("#")]
    sigs[f] = set(lines)

fl = list(sigs.keys())
for i in range(len(fl)):
    for j in range(i + 1, len(fl)):
        a, b = sigs[fl[i]], sigs[fl[j]]
        if len(a) < 30 or len(b) < 30:
            continue
        inter = len(a & b)
        ratio = inter / min(len(a), len(b))
        if ratio > 0.55:
            print(f"  {ratio:.0%}  {os.path.relpath(fl[i], ROOT)}  <->  {os.path.relpath(fl[j], ROOT)}")
