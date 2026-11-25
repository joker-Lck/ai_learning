# -*- coding: utf-8 -*-
"""入口可达性分析：从 backend/main.py 等入口出发，找出不可达模块"""
import ast
import os
from collections import defaultdict, deque

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"
SCAN = ["backend", "core", "data", "services"]
SKIP = {"__pycache__", "node_modules", ".git", ".pytest_cache"}

py_files = []
for d in SCAN:
    base = os.path.join(ROOT, d)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP]
        for fn in filenames:
            if fn.endswith(".py"):
                py_files.append(os.path.join(dirpath, fn))

def dotted(path):
    rel = os.path.relpath(path, ROOT)
    parts = rel.split(os.sep)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)

module_of = {dotted(f): f for f in py_files}
tops = ("backend", "core", "data", "services")

# 解析每个文件的项目内 import
edges = defaultdict(set)   # file -> set(file)
for f in py_files:
    try:
        src = open(f, encoding="utf-8", errors="replace").read()
        if src.startswith("\ufeff"):
            src = src[1:]
        tree = ast.parse(src)
    except SyntaxError as e:
        print("SYNTAX ERROR", os.path.relpath(f, ROOT), e)
        continue
    targets = set()
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.module:
                # 相对导入
                base = dotted(f).split(".")
                pkg = base[:-1] if not f.endswith("__init__.py") else base
                up = node.level - 1
                prefix = ".".join(pkg[: len(pkg) - up]) if up else ".".join(pkg)
                mods = [prefix + "." + node.module if prefix else node.module]
            elif node.level and not node.module:
                base = dotted(f).split(".")
                pkg = base[:-1] if not f.endswith("__init__.py") else base
                up = node.level - 1
                mods = [".".join(pkg[: len(pkg) - up])] if up else []
            elif node.module:
                mods = [node.module]
        # from X import Y → X.Y 也可能是模块
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                mods.append(node.module + "." + a.name)
        for m in mods:
            if not m.split(".")[0] in tops:
                continue
            # 匹配到最长已知模块
            cand = m
            while cand and cand not in module_of:
                cand = cand.rsplit(".", 1)[0] if "." in cand else ""
            if cand:
                edges[f].add(module_of[cand])

# 入口
entries = [os.path.join(ROOT, "backend", "main.py")]
for extra in ("init_admin.py", "init_db.py", "init_qa_db.py", "init_rag_db.py"):
    p = os.path.join(ROOT, extra)
    if os.path.exists(p):
        entries.append(p)
for sub in ("01_运行启动", "scripts"):
    b = os.path.join(ROOT, sub)
    for dirpath, _, filenames in os.walk(b):
        for fn in filenames:
            if fn.endswith(".py"):
                entries.append(os.path.join(dirpath, fn))

reachable = set()
q = deque()
for e in entries:
    if os.path.exists(e):
        q.append(e)
        reachable.add(e)
while q:
    cur = q.popleft()
    for nxt in edges.get(cur, ()):
        if nxt not in reachable:
            reachable.add(nxt)
            q.append(nxt)

print(f"总 py 文件(主代码): {len(py_files)}, 入口: {len(entries)}, 可达: {len(reachable)}")
print("\n=== 不可达模块（入口链路上没人用）===")
unreach = []
for f in py_files:
    if f in reachable:
        continue
    if f.endswith("__init__.py") and not defs_count_ok if False else False:
        pass
    rel = os.path.relpath(f, ROOT)
    try:
        src = open(f, encoding="utf-8", errors="replace").read()
        n = src.count("\ndef ") + src.count("\nclass ")
    except Exception:
        n = -1
    unreach.append((rel, n, len(src) if src else 0))
for rel, n, size in sorted(unreach):
    print(f"  {rel}  (defs~{n}, {size}B)")

print("\n=== backend/api 路由 → 依赖的 services/data ===")
api_dir = os.path.join(ROOT, "backend", "api")
for fn in sorted(os.listdir(api_dir)):
    if not fn.endswith(".py"):
        continue
    f = os.path.join(api_dir, fn)
    deps = sorted({dotted(x) for x in edges.get(f, set()) if dotted(x).startswith(("services", "data"))})
    print(f"  {fn}: {', '.join(deps) if deps else '-'}")
