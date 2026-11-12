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
