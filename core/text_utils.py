# -*- coding: utf-8 -*-
"""共享文本处理工具 —— 各模块统一使用，避免重复实现"""

import re

NUM_RE = re.compile(r"\d+\.\d+|\d{2,}|\d+/\d+|\d+%|\d+\s*[×x*]\s*10")


def split_paragraphs(text: str, max_length: int = 500, max_count: int = 100) -> list[str]:
    """将文本分割为段落（过长段落按句读二次切分，无句读则强切）"""
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    result = []
    for para in paragraphs:
        if len(para) <= max_length:
            result.append(para)
        else:
            for sep in ["。", "；", "!", "？", ".", ";", "!", "?"]:
                if sep in para:
                    sentences = para.split(sep)
                    current = ""
                    for sentence in sentences:
                        if len(current + sentence) <= max_length:
                            current += sentence + sep
                        else:
                            if current:
                                result.append(current.strip())
                            current = sentence + sep
                    if current:
                        result.append(current.strip())
                    break
            else:
                for i in range(0, len(para), max_length):
                    result.append(para[i : i + max_length])

    return result[:max_count]


def extract_numbers(text: str) -> list[str]:
    """提取数值锚点：小数/两位以上整数/分数/百分数/科学计数"""
    return [m.group(0).replace(" ", "") for m in NUM_RE.finditer(text)]


def jaccard(set_a: set, set_b: set) -> float:
    """Jaccard 相似度（空集返回 0）"""
    if not set_a or not set_b:
        return 0.0
    union = len(set_a | set_b)
    return len(set_a & set_b) / union if union > 0 else 0.0


def containment(small: set, big: set) -> float:
    """包含度：small 被 big 覆盖的比例（空 small 返回 0）"""
    if not small:
        return 0.0
    return len(small & big) / len(small)


def split_sentences(text: str, seps: str = "。！？\n", min_len: int = 0, keep_seps: bool = False) -> list[str]:
    """按句读切句；keep_seps=True 时保留分隔符在句尾"""
    if not text:
        return []
    if keep_seps:
        parts = re.split(f"(?<=[{seps}])", text)
    else:
        parts = re.split(f"[{seps}]", text)
    out = []
    for s in parts:
        s = s.strip()
        if s and len(s) >= min_len:
            out.append(s)
    return out


# ── 符号锚点工具：数值归一化 / 容差匹配 / 公式等价 ─────────────

def normalize_number(s: str) -> float | None:
    """数值归一化：'3/5'→0.6，'60%'→0.6，'3.14'→3.14，'1.2×10^3'→1200"""
    if not s:
        return None
    t = s.strip().replace(" ", "").replace("％", "%")
    try:
        if t.endswith("%"):
            return float(t[:-1]) / 100.0
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / float(b)
        m = re.fullmatch(r"(\d+\.?\d*)[×x*]10\^?(-?\d+)", t)
        if m:
            return float(m.group(1)) * (10.0 ** int(m.group(2)))
        return float(t)
    except (ValueError, ZeroDivisionError):
        return None


def numbers_equivalent(a: str, b: str, rel_tol: float = 1e-6,
                       near_tol: float | None = None) -> bool | None:
    """比较两个数值表达式是否等价。

    返回 True=精确等价（含分数/百分数归一化）、False=不等价、
    None=无法解析。near_tol 给定时：差值在 near_tol 内返回 'near'
    （由调用方决定语义，这里用 None 表示不等价但近似——为保持返回类型
    简洁，近似判定用 numbers_near()）。
    """
    va, vb = normalize_number(a), normalize_number(b)
    if va is None or vb is None:
        return None
    if va == vb:
        return True
    return abs(va - vb) <= max(rel_tol * max(abs(va), abs(vb)), 1e-12)


def numbers_near(a: str, b: str, rel_tol: float = 0.01, abs_tol: float = 0.01) -> bool:
    """容差匹配：π≈3.14 与 3.16 判为近似（教材四舍五入差异）"""
    va, vb = normalize_number(a), normalize_number(b)
    if va is None or vb is None:
        return False
    return abs(va - vb) <= max(rel_tol * max(abs(va), abs(vb)), abs_tol)


_BOUND_RE = re.compile(
    r"([A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9_]*|P\s*\([^)]{1,12}\)|[A-Za-z][A-Za-z0-9_]*\s*\([^)]{1,12}\))"
    r"\s*[=＝]\s*"
    r"(\d+\.?\d*\s*/\s*\d+\.?\d*|\d+\.?\d*\s*%|\d+\.\d+|\d+)"
)


def extract_bound_values(text: str) -> list[tuple[str, str]]:
    """提取（符号=数值）绑定值对，如 'P(A)=3/5' → [('P(A)', '3/5')]"""
    out = []
    for m in _BOUND_RE.finditer(text or ""):
        sym = re.sub(r"\s+", "", m.group(1))
        out.append((sym, m.group(2).replace(" ", "")))
    return out


def normalize_formula(s: str) -> str:
    """公式归一化：去 LaTeX 记号/统一运算符与括号/去空白、编号与末尾句读"""
    t = (s or "").strip().rstrip("。．.；;！!？?")
    t = t.replace("（", "(").replace("）", ")")
    t = t.replace("×", "*").replace("·", "*").replace("÷", "/").replace("−", "-")
    # LaTeX 收敛：\tag{...} 编号剥离；\frac2{10} / \frac{2}{10} → 2/10；\times → *；去 \left\right $ _{}
    t = re.sub(r"\\tag\{[^}]*\}", "", t)
    t = re.sub(r"\\d?frac\s*\{?\s*([-\d]+)\s*\}?\s*\{\s*([-\d]+)\s*\}", r"\1/\2", t)
    t = re.sub(r"\\d?frac\s*([-\d])\s*([-\d])", r"\1/\2", t)
    t = t.replace("\\times", "*").replace("\\cdot", "*").replace("\\div", "/")
    t = t.replace("\\left", "").replace("\\right", "").replace("\\", "")
    t = t.replace("$", "").replace("{", "").replace("}", "")
    t = re.sub(r"\s+", "", t)
    return t


def _formula_terms(expr: str) -> list[str]:
    """把表达式拆成带符号的项多重集（处理加法交换律，不展开乘积）"""
    expr = expr.replace("-", "+-")
    terms = [t for t in expr.split("+") if t and t != "-"]
    return sorted(terms)


def formulas_equivalent(f1: str, f2: str) -> bool | None:
    """公式等价判定（纯确定性，零模型）。

    依次尝试：归一化全等 → 等式两侧项多重集相等（加法交换律）→
    分式交叉相乘（a/b = c/d ⇔ a·d = b·c）。无法解析返回 None。
    """
    a, b = normalize_formula(f1), normalize_formula(f2)
    if not a or not b:
        return None
    if a == b:
        return True
    if "=" not in a or "=" not in b:
        return None
    la, ra = a.split("=", 1)
    lb, rb = b.split("=", 1)
    # 项多重集比较（同侧交换律：a+b=b+a）
    if _formula_terms(la) == _formula_terms(lb) and _formula_terms(ra) == _formula_terms(rb):
        return True
    if _formula_terms(la) == _formula_terms(rb) and _formula_terms(ra) == _formula_terms(lb):
        return True
    # 分式交叉相乘：a/b = c/d ⇔ a*d == b*c（系数为纯数值时）
    def _frac(s: str):
        if "/" in s:
            a1, b1 = s.split("/", 1)
            return a1.strip(), b1.strip()
        return s.strip(), "1"

    a1, b1 = _frac(la)
    a2, b2 = _frac(lb)
    na1, nb1 = normalize_number(a1), normalize_number(b1)
    na2, nb2 = normalize_number(a2), normalize_number(b2)
    if None not in (na1, nb1, na2, nb2) and nb1 and nb2:
        cross1, cross2 = na1 * nb2, na2 * nb1
        if abs(cross1 - cross2) <= 1e-9 * max(abs(cross1), abs(cross2), 1.0):
            return True
    return None
