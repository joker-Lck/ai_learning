# -*- coding: utf-8 -*-
"""精确验证 db_operations 领域方法的真实调用方"""
import re
import os
import collections

os.chdir(r"C:\Users\Administrator\Downloads\ai_learning_repo")
methods = ["add_user", "get_user", "add_class", "get_class_by_name", "add_student",
           "get_students_by_class", "add_question", "get_questions_by_user",
           "add_analysis", "get_analysis_by_student"]
hits = collections.defaultdict(list)
for dp, dn, fn in os.walk("."):
    dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__", "corpus_textbook", "_zip_tmp", "experiments")]
    for f in fn:
        if not f.endswith(".py"):
            continue
        p = os.path.join(dp, f)
        for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            s = line.strip()
            if s.startswith("def ") or s.startswith("#") or s.startswith("class ") or '"""' in s:
                continue
            for m in methods:
                if re.search(r"\." + m + r"\s*\(", s):
                    hits[m].append(f"{p}:{i}: {s[:80]}")
for m in methods:
    print(m, "->")
    if hits[m]:
        for h in hits[m][:6]:
            print("   ", h)
    else:
        print("    NO CALLS")
