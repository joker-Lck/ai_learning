# -*- coding: utf-8 -*-
"""T2.3 Part A: 质量检查模块共用逻辑合并到 core.text_utils"""
import io
import os

ROOT = r"F:\项目\ai教学辅助系统"

def edit_file(path, pairs):
    p = os.path.join(ROOT, path.replace("/", os.sep))
    raw = io.open(p, "r", encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    for old, new in pairs:
        assert old in text, f"NOT FOUND in {path}:\n{old[:120]}"
        text = text.replace(old, new, 1)
    if crlf:
        text = text.replace("\n", "\r\n")
    io.open(p, "w", encoding="utf-8", newline="").write(text)
    print(f"edited: {path}")

# ── 1. core/text_utils.py 已直接重写（含 split_paragraphs/extract_numbers/jaccard/containment/split_sentences）──
print("core/text_utils.py: ready (rewritten)")

# ── 2. citation_annotator._jaccard 委托共享实现 ──
edit_file("services/citation_annotator.py", [
    ('''    def _jaccard(self, set_a: set, set_b: set) -> float:
        """Jaccard 相似度"""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0''',
     '''    def _jaccard(self, set_a: set, set_b: set) -> float:
        """Jaccard 相似度（共享实现）"""
        from core.text_utils import jaccard

        return jaccard(set_a, set_b)'''),
    # 两处切句改用共享 split_sentences（参数保持原行为）
    ("            sentences = re.split(r'[。！？\\n]', content)",
     "            from core.text_utils import split_sentences\n            sentences = split_sentences(content, seps='。！？\\n')"),
    ("        answer_sentences = re.split(r'(?<=[。！？\\n])', answer)",
     "        from core.text_utils import split_sentences\n        answer_sentences = split_sentences(answer, seps='。！？\\n', keep_seps=True)"),
])

# ── 3. faithfulness_verifier：_support_score 数学与 _extract_numbers 走共享实现（公式不变）──
edit_file("services/faithfulness_verifier.py", [
    ('''        jac = len(sent_words & ev_words) / max(len(sent_words | ev_words), 1)
        # 包含度：答案词被证据覆盖的比例（答案短句常是证据子集）
        contain = len(sent_words & ev_words) / max(len(sent_words), 1)''',
     '''        from core.text_utils import containment, jaccard

        jac = jaccard(sent_words, ev_words)
        # 包含度：答案词被证据覆盖的比例（答案短句常是证据子集）
        contain = containment(sent_words, ev_words)'''),
    ('''    @staticmethod
    def _extract_numbers(text: str) -> list[str]:
        return [m.group(0).replace(" ", "") for m in _NUM_RE.finditer(text)]''',
     '''    @staticmethod
    def _extract_numbers(text: str) -> list[str]:
        from core.text_utils import extract_numbers

        return extract_numbers(text)'''),
    # _NUM_RE 改为从 core.text_utils 导入（同名别名，detect_contradictions 仍用 match 位置）
    ('''_NUM_RE = re.compile(r"\\d+\\.\\d+|\\d{2,}|\\d+/\\d+|\\d+%|\\d+\\s*[×x*]\\s*10")
''', '''from core.text_utils import NUM_RE as _NUM_RE
'''),
])

# ── 4. content_safety_service._calculate_text_similarity 走共享 jaccard ──
edit_file("services/content_safety_service.py", [
    ('''    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度(简化版Jaccard相似度)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)''',
     '''    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度(简化版Jaccard相似度，共享实现)"""
        from core.text_utils import jaccard

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        return jaccard(words1, words2)'''),
])

# ── 5. answer_quality_scorer：overlap 走共享 containment，切句走共享 split_sentences ──
edit_file("services/answer_quality_scorer.py", [
    ('''        overlap = len(q_words & a_words) / len(q_words)
        return min(overlap * 1.8, 1.0)''',
     '''        from core.text_utils import containment

        overlap = containment(q_words, a_words)
        return min(overlap * 1.8, 1.0)'''),
    ('''        overlap = len(c_words & a_words) / len(c_words)
        return min(overlap * 2.5, 1.0)''',
     '''        from core.text_utils import containment

        overlap = containment(c_words, a_words)
        return min(overlap * 2.5, 1.0)'''),
    ('''        sentences = [s.strip() for s in answer.split("。") if len(s.strip()) > 10]''',
     '''        from core.text_utils import split_sentences

        sentences = split_sentences(answer, seps="。", min_len=11)'''),
])

print("Part A done")
