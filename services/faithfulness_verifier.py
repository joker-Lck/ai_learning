"""忠实度验证器（Faithfulness Verifier）

解决教育 RAG 的核心风险：「归因正确 ≠ 生成忠实」（Wallat et al., SIGIR ICTIR 2025）
——答案可以结论对但引用错证据；知识库投毒（PoisonedRAG）可系统性篡改答案。
教育场景学生无法分辨伪忠实，必须给出句级可核查的接地信号与拒答保护。

创新点:
1. 句级归因核查（claim → evidence support scoring）
   - Jaccard 词面 + 包含度 + 数字/公式锚点三通道判定
   - 数字锚点对教育尤其关键：数学/理科答案的数值必须能在证据中找到
2. 证据矛盾检测（numeric conflict detection）
   - 同关键词下不同数值 → 矛盾信号（教材版本冲突/投毒信号）
3. 证据不足拒答/降级（refuse-or-qualify）
   - 无支撑句比例超阈值 → 保留有支撑部分 + 显式「证据不足」声明
4. 投毒/注入信号（outlier + directive 检测）
   - 离群低分块 + 指令性文本（"忽略之前"类）→ 标记可疑证据

纯规则+词面（无模型依赖），可与 CitationAnnotator/RAGAS 互补。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.logger import debug, info, warning

# 中文停用词（与 citation_annotator 保持一致的最小集）
_STOP = set("的了和是在有我他这就不都一个上们来到时为地大以中说出行会可你生对也子得里后自那要下过么然没看天去过小么起多都还")


@dataclass
class ClaimCheck:
    """单句核查结果"""
    sentence: str
    status: str  # supported / partial / unsupported
    support_score: float
    best_evidence_idx: int
    missing_numbers: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class FaithfulnessReport:
    """完整核查报告"""
    claims: list[ClaimCheck]
    supported_ratio: float
    numeric_consistency: float
    contradictions: list[dict]
    suspicious_evidence: list[dict]
    verdict: str  # faithful / partial / unfaithful / insufficient_evidence
    qualified_answer: str

    def to_dict(self) -> dict:
        return {
            "claims": [
                {
                    "sentence": c.sentence,
                    "status": c.status,
                    "support_score": round(c.support_score, 3),
                    "best_evidence_idx": c.best_evidence_idx,
                    "missing_numbers": c.missing_numbers,
                    "reason": c.reason,
                }
                for c in self.claims
            ],
            "supported_ratio": round(self.supported_ratio, 3),
            "numeric_consistency": round(self.numeric_consistency, 3),
            "contradictions": self.contradictions,
            "suspicious_evidence": self.suspicious_evidence,
            "verdict": self.verdict,
            "qualified_answer": self.qualified_answer,
        }


# 数字/公式锚点：整数、小数、分数、百分数（过滤纯序号<10 的单数字，噪声太大）
_NUM_RE = re.compile(r"\d+\.\d+|\d{2,}|\d+/\d+|\d+%|\d+\s*[×x*]\s*10")
# 指令注入/投毒信号
_DIRECTIVE_RE = re.compile(
    r"(忽略(此前|之前|以上)?(的)?(指令|问题|内容)|ignore\s+(previous|above)|"
    r"必须(遵照|按照|遵循)|系统提示|扮演(一个)?|你是(一个)?[^。]{0,10}(助手|教师)$)"
)
# 矛盾指示词（同关键词附近数值冲突时提示）
_CONFLICT_WINDOW = 6


class FaithfulnessVerifier:
    """忠实度验证器"""

    def __init__(self, support_threshold: float = 0.35,
                 unsupported_refuse_ratio: float = 0.5):
        self.support_threshold = support_threshold
        self.unsupported_refuse_ratio = unsupported_refuse_ratio

    # ── 主入口 ─────────────────────────────────────────────
    def verify(self, answer: str, evidence: list[dict]) -> FaithfulnessReport:
        """核查答案相对证据的忠实度

        参数:
            answer: 生成的答案文本
            evidence: 检索证据（[{content_text|content, title, section_path?, similarity?}]）
        """
        claims = self.verify_claims(answer, evidence)
        contradictions = self.detect_contradictions(evidence)
        suspicious = self.detect_suspicious_evidence(evidence)

        n = max(len(claims), 1)
        supported = sum(1 for c in claims if c.status == "supported")
        partial = sum(1 for c in claims if c.status == "partial")
        unsupported = sum(1 for c in claims if c.status == "unsupported")
        supported_ratio = supported / n
        numeric_ok = sum(1 for c in claims if not c.missing_numbers) / n

        # 判定
        if not evidence:
            verdict = "insufficient_evidence"
        elif unsupported / n > self.unsupported_refuse_ratio:
            verdict = "unfaithful"
        elif unsupported > 0 or partial > 0:
            verdict = "partial"
        else:
            verdict = "faithful"
        if contradictions and verdict == "faithful":
            verdict = "partial"

        qualified = self.qualify_answer(answer, claims, verdict, contradictions)

        report = FaithfulnessReport(
            claims=claims,
            supported_ratio=supported_ratio,
            numeric_consistency=numeric_ok,
            contradictions=contradictions,
            suspicious_evidence=suspicious,
            verdict=verdict,
            qualified_answer=qualified,
        )
        info(f"忠实度核查: verdict={verdict} supported={supported}/{n} "
             f"contradictions={len(contradictions)} suspicious={len(suspicious)}")
        return report

    # ── 1. 句级归因核查 ────────────────────────────────────
    def verify_claims(self, answer: str, evidence: list[dict]) -> list[ClaimCheck]:
        """逐句核查：每个断言是否有证据支撑（词面+数字锚点）"""
        sentences = self._split_claims(answer)
        ev_sents = self._evidence_sentences(evidence)

        claims = []
        for sent in sentences:
            if len(sent) < 5:
                continue
            best_idx, best_score, best_ev = -1, 0.0, ""
            sent_words = self._tokenize(sent)
            for ev_sent, doc_idx in ev_sents:
                score = self._support_score(sent, sent_words, ev_sent)
                if score > best_score:
                    best_score, best_idx, best_ev = score, doc_idx, ev_sent

            missing = self._missing_numbers(sent, best_ev) if best_ev else self._extract_numbers(sent)

            # 状态判定：分数 + 数字锚点
            if best_score >= self.support_threshold and not missing:
                status = "supported"
            elif best_score >= self.support_threshold * 0.6:
                status = "partial"
            else:
                status = "unsupported"

            claims.append(ClaimCheck(
                sentence=sent,
                status=status,
                support_score=best_score,
                best_evidence_idx=best_idx,
                missing_numbers=missing,
                reason=f"score={best_score:.2f}"
                       + (f", missing_nums={missing}" if missing else ""),
            ))
        return claims

    def _support_score(self, sent: str, sent_words: set, ev_sent: str) -> float:
        """三通道支撑分：Jaccard + 包含度 + 数字锚点加成"""
        ev_words = self._tokenize(ev_sent)
        if not sent_words or not ev_words:
            return 0.0
        jac = len(sent_words & ev_words) / max(len(sent_words | ev_words), 1)
        # 包含度：答案词被证据覆盖的比例（答案短句常是证据子集）
        contain = len(sent_words & ev_words) / max(len(sent_words), 1)
        score = max(jac, contain * 0.9)
        # 数字锚点加成：句中数字出现在证据中
        nums = self._extract_numbers(sent)
        if nums and all(n in ev_sent for n in nums):
            score = min(1.0, score + 0.2)
        return score

    # ── 2. 证据矛盾检测 ────────────────────────────────────
    def detect_contradictions(self, evidence: list[dict]) -> list[dict]:
        """同关键词窗口内数值不一致 → 矛盾信号（教材冲突/投毒提示）"""
        # 收集 (keyword, number, doc_idx) 三元组
        triples: list[tuple[str, str, int]] = []
        for i, doc in enumerate(evidence):
            text = doc.get("content_text") or doc.get("content") or ""
            for m in _NUM_RE.finditer(text):
                num = m.group(0).replace(" ", "")
                lo = max(0, m.start() - _CONFLICT_WINDOW * 3)
                hi = min(len(text), m.end() + _CONFLICT_WINDOW * 3)
                window = text[lo:hi]
                # 窗口内取最长中文词块作关键词锚
                for kw in re.findall(r"[\u4e00-\u9fff]{2,6}", window):
                    triples.append((kw, num, i))

        conflicts = []
        seen = set()
        by_kw: dict[str, list[tuple[str, int]]] = {}
        for kw, num, idx in triples:
            by_kw.setdefault(kw, []).append((num, idx))
        for kw, pairs in by_kw.items():
            nums = {n for n, _ in pairs}
            if len(nums) > 1 and len(pairs) >= 2:
                key = (kw, tuple(sorted(nums)))
                if key in seen:
                    continue
                seen.add(key)
                doc_ids = sorted({idx for _, idx in pairs})
                if len(doc_ids) >= 2:  # 跨文档数值冲突才有意义
                    conflicts.append({
                        "keyword": kw,
                        "numbers": sorted(nums),
                        "doc_indexes": doc_ids,
                        "hint": "同一概念在不同证据中数值不一致，请人工核对（可能是教材版本差异或错误内容）",
                    })
        return conflicts[:10]  # 上限防爆

    # ── 3. 投毒/注入信号 ───────────────────────────────────
    def detect_suspicious_evidence(self, evidence: list[dict]) -> list[dict]:
        """离群低分块 + 指令性文本 → 可疑证据标记"""
        suspicious = []
        scores = [d.get("similarity", d.get("score", d.get("probability", 0))) for d in evidence]
        max_score = max(scores) if scores else 0

        for i, doc in enumerate(evidence):
            text = doc.get("content_text") or doc.get("content") or ""
            reasons = []
            if _DIRECTIVE_RE.search(text):
                reasons.append("含指令性/注入样文本")
            s = scores[i] if i < len(scores) else 0
            if max_score > 0 and s < max_score * 0.5 and s < 0.3:
                reasons.append(f"相似度离群低（{s:.2f} vs max {max_score:.2f}）")
            if reasons:
                suspicious.append({
                    "doc_index": i,
                    "title": (doc.get("title") or "")[:50],
                    "reasons": reasons,
                    "hint": "该证据可信度存疑，建议忽略或人工复核",
                })
        return suspicious

    # ── 4. 拒答/降级答案 ────────────────────────────────────
    def qualify_answer(self, answer: str, claims: list[ClaimCheck],
                       verdict: str, contradictions: list[dict]) -> str:
        """证据不足时生成降级答案：保留有支撑内容 + 显式不确定性声明"""
        if verdict == "faithful" and not contradictions:
            return answer

        parts = []
        kept, flagged = [], []
        for c in claims:
            if c.status == "supported":
                kept.append(c.sentence)
            else:
                flagged.append(c)

        if verdict == "insufficient_evidence":
            return ("【知识库中没有找到足够依据，以下为推测性回答，仅供参考】\n"
                    f"{answer}\n"
                    "【建议】请查阅教材原文或咨询老师确认。")

        if verdict == "unfaithful":
            header = "【警告】回答中大部分内容缺乏知识库依据，请谨慎参考：\n"
        else:
            header = "【提示】部分内容缺乏依据，已标注：\n"

        body_parts = []
        for c in claims:
            if c.status == "supported":
                body_parts.append(c.sentence)
            else:
                body_parts.append(f"{c.sentence}（〔待核实：{c.reason}〕）")
        body = "".join(body_parts) if body_parts else answer

        tail = []
        if contradictions:
            kw_list = "、".join(c["keyword"] for c in contradictions[:3])
            tail.append(f"⚠ 证据间数值存在冲突（{kw_list}），请注意甄别。")
        if tail:
            body += "\n" + "\n".join(tail)
        return header + body

    # ── 工具 ───────────────────────────────────────────────
    @staticmethod
    def _split_claims(answer: str) -> list[str]:
        """断言切分：按句读+换行，保留完整句"""
        parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", answer)
        return [p.strip() for p in parts if p and p.strip()]

    @staticmethod
    def _evidence_sentences(evidence: list[dict]) -> list[tuple[str, int]]:
        out = []
        for i, doc in enumerate(evidence):
            text = doc.get("content_text") or doc.get("content") or ""
            path = doc.get("section_path") or ""
            for s in re.split(r"[。！？\n；;]", f"{path}\n{text}"):
                s = s.strip()
                if len(s) >= 8:
                    out.append((s, i))
        return out

    @staticmethod
    def _tokenize(text: str) -> set:
        words = set()
        for seg in re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text):
            if re.fullmatch(r"[\u4e00-\u9fff]+", seg):
                if len(seg) <= 2:
                    if seg not in _STOP:
                        words.add(seg)
                else:
                    for j in range(len(seg) - 1):
                        bigram = seg[j:j + 2]
                        if bigram not in _STOP:
                            words.add(bigram)
            else:
                words.add(seg.lower())
        return words

    @staticmethod
    def _extract_numbers(text: str) -> list[str]:
        return [m.group(0).replace(" ", "") for m in _NUM_RE.finditer(text)]

    def _missing_numbers(self, claim: str, evidence_sent: str) -> list[str]:
        nums = self._extract_numbers(claim)
        if not evidence_sent:
            return nums
        ev_nums = set(self._extract_numbers(evidence_sent)) | set(re.findall(r"\d+", evidence_sent))
        missing = []
        for n in nums:
            # 允许 3/5 在证据中以"3/5"或"0.6"以外的分解出现：只要数字组成都在证据里
            parts = re.findall(r"\d+", n)
            if n in evidence_sent or all(p in ev_nums for p in parts):
                continue
            missing.append(n)
        return missing


# 全局单例
faithfulness_verifier = FaithfulnessVerifier()
