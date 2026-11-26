# -*- coding: utf-8 -*-
"""文档版本号升级 v9.1.0 -> v9.2.0（仅文档头/当前版本/APP_VERSION，不碰历史标注）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

APPLY = "--apply" in sys.argv
ROOTS = ["README.md", "docs"]
SKIP_DIRS = {"node_modules", ".next", "archive"}

REPLACES = [
    ("<b>当前版本：v9.1.0</b>", "<b>当前版本：v9.2.0</b>"),
    ("version-v9.1.0-blue", "version-v9.2.0-blue"),
    ("**版本**：v9.1.0", "**版本**：v9.2.0"),
    ("**文档版本**：v9.1.0", "**文档版本**：v9.2.0"),
    ("**版本：v9.1.0**", "**版本：v9.2.0**"),
    ("当前版本 v9.1.0", "当前版本 v9.2.0"),
    ("APP_VERSION=9.1.0", "APP_VERSION=9.2.0"),
    ("| APP_VERSION | 应用版本 | 9.1.0 |", "| APP_VERSION | 应用版本 | 9.2.0 |"),
    ("（对齐系统 v9.1.0）", "（对齐系统 v9.2.0）"),
]


def main():
    changed = 0
    files = []
    for r in ROOTS:
        if os.path.isfile(r):
            files.append(r)
        elif os.path.isdir(r):
            for dirpath, dirs, fs in os.walk(r):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in fs:
                    if f.endswith(".md"):
                        files.append(os.path.join(dirpath, f))

    for path in files:
        raw = open(path, "rb").read()
        bom = b""
        if raw.startswith(b"\xef\xbb\xbf"):
            bom, raw = raw[:3], raw[3:]
        text = raw.decode("utf-8")
        newline = "\r\n" if "\r\n" in text else "\n"
        new_text = text
        notes = []
        for old, new in REPLACES:
            n = new_text.count(old)
            if n:
                new_text = new_text.replace(old, new)
                notes.append(f"{old!r} x{n}")
        if not notes:
            continue
        changed += 1
        print(f"--- {path}")
        for n in notes:
            print("   ", n)
        if APPLY:
            out = new_text
            if newline == "\r\n":
                out = out.replace("\r\n", "\n").replace("\n", "\r\n")
            open(path, "wb").write(bom + out.encode("utf-8"))

    print(f"[{'已写入' if APPLY else '干跑'}] 变更文件数: {changed}")


if __name__ == "__main__":
    main()
