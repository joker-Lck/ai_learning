# -*- coding: utf-8 -*-
"""
品牌改名 灵犀→启智 / LINGXI→QIZHI + 残余绿色十六进制收敛。
用法：
  python scripts/rename_qizhi.py          # 干跑
  python scripts/rename_qizhi.py --apply  # 写入
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

APPLY = "--apply" in sys.argv

TARGETS = [
    "frontend/app",
    "frontend/components",
    "frontend/lib",
    "frontend/stores",
    "frontend/styles",
    "docs",
]
SKIP_DIRS = {"node_modules", ".next", "archive"}

# 二进制 "LINGXI" -> "QIZHI"
BIN_OLD = "[01001100 01001001 01001110 01000111 01011000 01001001]"
BIN_NEW = "[01010001 01001001 01011010 01001000 01001001]"

RENAMES = [
    (BIN_OLD, BIN_NEW),
    ("LINGXI", "QIZHI"),
    ("lingxi", "qizhi"),
    ("灵犀", "启智"),
]

# 残余绿色 hex → 主题变量（上下文无关的安全值）
GREEN_HEX = {
    r"#10[bB]981": "var(--accent)",
    r"#34[dD]399": "var(--accent)",
    r"#22[Cc]55[Ee]": "var(--accent)",
    r"#00[Cc]853": "var(--accent-2)",
    r"#00[Aa]63[Ee]": "var(--accent)",
}


def transform(text):
    notes = []
    for old, new in RENAMES:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            notes.append(f"rename {old!r} -> {new!r}  x{n}")
    for pat, repl in GREEN_HEX.items():
        new_text, n = re.subn(pat, repl, text)
        if n:
            text = new_text
            notes.append(f"hex {pat} -> {repl}  x{n}")
    return text, notes


def main():
    changed = 0
    for root in TARGETS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith((".tsx", ".ts", ".css", ".js", ".jsx", ".md", ".json", ".html")):
                    continue
                path = os.path.join(dirpath, fname)
                raw = open(path, "rb").read()
                bom = b""
                if raw.startswith(b"\xef\xbb\xbf"):
                    bom, raw = raw[:3], raw[3:]
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                newline = "\r\n" if "\r\n" in text else "\n"
                # LessonPPTView 的 PPT 主题预设色板是内容数据，不做 hex 替换
                if fname == "LessonPPTView.tsx":
                    new_text, notes = text, []
                    for old, new in RENAMES:
                        n = new_text.count(old)
                        if n:
                            new_text = new_text.replace(old, new)
                            notes.append(f"rename {old!r} -> {new!r}  x{n}")
                else:
                    new_text, notes = transform(text)
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
