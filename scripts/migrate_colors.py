# -*- coding: utf-8 -*-
"""
前端色彩令牌迁移脚本：
将硬编码色值替换为 CSS 变量，使全部组件适配 昼夜双主题。
用法：
  python scripts/migrate_colors.py          # 干跑（只报告）
  python scripts/migrate_colors.py --apply  # 实际写入
"""
import re
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

APPLY = "--apply" in sys.argv
ROOTS = ["frontend/app", "frontend/components", "frontend/lib", "frontend/stores", "frontend/styles"]
SKIP_DIRS = {"node_modules", ".next", "archive"}
# 主题定义文件 / 数据文件不做机械替换
SKIP_FILES = {"globals.css", "api.ts"}

# 精确十六进制 → CSS 变量
HEX_MAP = {
    r"#6643[Ff][Ff]": "var(--accent)",
    r"#8[Bb]7[Aa][Ff][Ff]": "var(--accent-2)",
    r"#[Aa]78[Bb][Ff][Aa]": "var(--accent-2)",
    r"#64[Ff][Ff][Dd][Aa]": "var(--accent)",
    r"#00[Dd]4[Ff][Ff]": "var(--accent)",
    r"#0[Aa]0[Aa]0[Aa]": "var(--bg)",
    r"#1[Aa]1[Aa]2[Ee]": "var(--panel)",
    r"#1[Aa]1[Aa]27": "var(--panel)",
    r"#0[Ff]0[Ff]0[Ff]": "var(--panel)",
    r"#111111": "var(--panel)",
    r"#0[Dd]1117": "var(--panel-2)",
    r"#0[Ff]172[Aa]": "var(--panel-2)",
    r"#0[Aa]0[Ff]1[Ee]": "var(--panel)",
    r"#0[Aa]192[Ff]": "var(--panel)",
    r"#0[Dd]1[Bb]2[Aa]": "var(--panel)",
    r"#020508": "var(--panel)",
    r"#040[Aa]11": "var(--panel)",
    r"#060[Ff]1[Bb]": "var(--panel)",
    r"#081425": "var(--panel)",
    r"#[Ee]2[Ee]8[Ff]0": "var(--ink-2)",
    r"#[Ee]0[Ee]0[Ee]0": "var(--ink-2)",
    r"#[Ff]5[Ff]5[Ff]5": "var(--ink-2)",
    r"#888888": "var(--ink-3)",
}

# 单独处理（含边界判断）
HEX_FFF = re.compile(r"#ffffff\b|#fff\b", re.IGNORECASE)

# rgba(102, 67, 255, a) → rgb(var(--accent-rgb) / a)
RGBA_ACCENT = re.compile(
    r"rgba\(\s*102\s*,\s*67\s*,\s*255\s*,\s*([0-9.]+)\s*\)", re.IGNORECASE
)
RGBA_ACCENT2 = re.compile(
    r"rgba\(\s*139\s*,\s*122\s*,\s*255\s*,\s*([0-9.]+)\s*\)", re.IGNORECASE
)
# rgba(255, 255, 255, a) → rgb(var(--white-rgb) / a)
RGBA_WHITE = re.compile(
    r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\s*\)", re.IGNORECASE
)
# rgba(167, 139, 250, a) (#a78bfa)
RGBA_ACCENT3 = re.compile(
    r"rgba\(\s*167\s*,\s*139\s*,\s*250\s*,\s*([0-9.]+)\s*\)", re.IGNORECASE
)


def transform(text: str) -> tuple[str, list[str]]:
    notes = []
    for pat, repl in HEX_MAP.items():
        new_text, n = re.subn(pat, repl, text)
        if n:
            notes.append(f"{pat} -> {repl}  x{n}")
            text = new_text

    # #fff / #ffffff（避免替换已生成的 var 无影响；注意不要碰到 #fffabc 之类的 6 位色）
    def _fff_sub(m):
        return "var(--ink)"

    new_text, n = HEX_FFF.subn(_fff_sub, text)
    if n:
        notes.append(f"#fff/#ffffff -> var(--ink)  x{n}")
        text = new_text

    for pat, repl, label in [
        (RGBA_ACCENT, r"rgb(var(--accent-rgb) / \1)", "rgba(accent)"),
        (RGBA_ACCENT2, r"rgb(var(--accent-2-rgb) / \1)", "rgba(accent-2)"),
        (RGBA_ACCENT3, r"rgb(var(--accent-2-rgb) / \1)", "rgba(accent-2b)"),
        (RGBA_WHITE, r"rgb(var(--white-rgb) / \1)", "rgba(white)"),
    ]:
        new_text, n = pat.subn(repl, text)
        if n:
            notes.append(f"{label} -> rgb(var...)  x{n}")
            text = new_text

    return text, notes


def main():
    changed_files = 0
    total_notes: list[str] = []
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith((".tsx", ".ts", ".css", ".js", ".jsx")):
                    continue
                if fname in SKIP_FILES:
                    continue
                path = os.path.join(dirpath, fname)
                raw = open(path, "rb").read()
                # 保留 BOM / 换行风格
                bom = b""
                if raw.startswith(b"\xef\xbb\xbf"):
                    bom = raw[:3]
                    raw = raw[3:]
                text = raw.decode("utf-8")
                newline = "\r\n" if "\r\n" in text else "\n"

                new_text, notes = transform(text)
                if not notes:
                    continue

                changed_files += 1
                total_notes.append(f"--- {path}")
                total_notes.extend("    " + n for n in notes)

                if APPLY:
                    out = new_text
                    if newline == "\r\n":
                        out = out.replace("\r\n", "\n").replace("\n", "\r\n")
                    data = bom + out.encode("utf-8")
                    open(path, "wb").write(data)

    mode = "已写入" if APPLY else "干跑预览（未修改）"
    print(f"[{mode}] 变更文件数: {changed_files}")
    for line in total_notes:
        print(line)


if __name__ == "__main__":
    main()
