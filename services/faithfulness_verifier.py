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
from core.text_utils import (
    extract_bound_values,
    formulas_equivalent,
    normalize_number,
    numbers_equivalent,
    numbers_near,
)

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
    reliance_drop: float = 0.0        # 反事实依赖：移除被引证据后的分数跌幅
    false_dependency: bool = False    # 事后合理化标记（引了但不真依赖）


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
    refusal_level: int = 0  # 0=直接答 1=标注后答 2=部分答+教师复核 3=拒答降级

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
                    "reliance_drop": round(c.reliance_drop, 3),
                    "false_dependency": c.false_dependency,
                }
                for c in self.claims
            ],
            "supported_ratio": round(self.supported_ratio, 3),
            "numeric_consistency": round(self.numeric_consistency, 3),
            "contradictions": self.contradictions,
            "suspicious_evidence": self.suspicious_evidence,
            "verdict": self.verdict,
            "refusal_level": self.refusal_level,
            "qualified_answer": self.qualified_answer,
        }


# 数字/公式锚点：整数、小数、分数、百分数（过滤纯序号<10 的单数字，噪声太大）
from core.text_utils import NUM_RE as _NUM_RE
# 指令注入/投毒信号
_DIRECTIVE_RE = re.compile(
    r"(忽略(此前|之前|以上)?(的)?(指令|问题|内容)|ignore\s+(previous|above)|"
    r"必须(遵照|按照|遵循)|系统提示|扮演(一个)?|你是(一个)?[^。]{0,10}(助手|教师)$)"
)
# 矛盾指示词（同关键词附近数值冲突时提示）
_CONFLICT_WINDOW = 6

# 证据来源权威度（教育场景：教材 > 教师课件 > 教辅/习题 > 网络）
SOURCE_AUTHORITY = {
    "textbook": 4,
    "lecture_notes": 3,
    "slides": 3,
    "study_guide": 2,
    "exercise": 2,
    "homework": 2,
    "web": 1,
    "unknown": 2,
}

# 公式样式：含运算符/等号的数学片段（含 LaTeX；RHS 至数学跨度全长，遇 $ 截止）
_FORMULA_RE = re.compile(
    r"[A-Za-zP\\$][A-Za-z0-9()\\[\]|,_\u03b1-\u03c9\u0391-\u03a9$]{0,16}\s*[=＝]\s*"
    r"[^，。；\n$]{2,80}"
)


class FaithfulnessVerifier:
    """忠实度验证器

    升级点（符号锚点 / 分级拒答 / 权威度消解 / 反事实依赖）：
    - 数值归一化 + 容差匹配：3/5≡0.6、60%≡0.6；π≈3.14 与 3.16 判近似冲突
    - 绑定值锚点：'P(A)=3/5' 按符号绑定核对，捕获改值型伪忠实
    - 公式等价：归一化全等 / 项多重集 / 交叉相乘，捕获改写型伪忠实
    - 分级拒答：0 直接答 → 1 标注后答 → 2 部分答+教师复核 → 3 拒答降级
    - 权威度消解：跨文档数值冲突按 权威度矩阵 + 版本 消解
    - 反事实依赖：移除被引证据后支撑分不降 → 事后合理化标记
    """

    def __init__(self, support_threshold: float = 0.35,
                 unsupported_refuse_ratio: float = 0.5,
                 teacher_review_ratio: float = 0.2,
                 flagged_ratio: float = 0.0,
                 near_tolerance: float = 0.01,
                 reliance_drop_eps: float = 0.05,
                 use_norm: bool = True, use_bound: bool = True,
                 use_formula: bool = True):
        self.support_threshold = support_threshold
        self.unsupported_refuse_ratio = unsupported_refuse_ratio
        self.teacher_review_ratio = teacher_review_ratio
        self.flagged_ratio = flagged_ratio
        self.near_tolerance = near_tolerance
        self.reliance_drop_eps = reliance_drop_eps
        # 符号锚点三通道开关（供消融实验）
        self.use_norm = use_norm
        self.use_bound = use_bound
        self.use_formula = use_formula

    # ── 主入口 ─────────────────────────────────────────────
    def verify(self, answer: str, evidence: list[dict]) -> FaithfulnessReport:
        """核查答案相对证据的忠实度

        参数:
            answer: 生成的答案文本
            evidence: 检索证据（[{content_text|content, title, section_path?,
                    source_type?, version?, similarity?}]）
        """
        claims = self.verify_claims(answer, evidence)
        contradictions = self.detect_contradictions(evidence)
        contradictions = self.resolve_conflicts(contradictions, evidence)
        suspicious = self.detect_suspicious_evidence(evidence)
        self.check_reliance(claims, evidence)

        n = max(len(claims), 1)
        supported = sum(1 for c in claims if c.status == "supported")
        partial = sum(1 for c in claims if c.status == "partial")
        unsupported = sum(1 for c in claims if c.status == "unsupported")
        unsupported_ratio = unsupported / n
        supported_ratio = supported / n
        numeric_ok = sum(1 for c in claims if not c.missing_numbers) / n

        # 判定
        if not evidence:
            verdict = "insufficient_evidence"
        elif unsupported_ratio > self.unsupported_refuse_ratio:
            verdict = "unfaithful"
        elif unsupported > 0 or partial > 0:
            verdict = "partial"
        else:
            verdict = "faithful"
        if contradictions and verdict == "faithful":
            verdict = "partial"

        refusal_level = self._refusal_level(verdict, unsupported_ratio, contradictions, evidence)

        qualified = self.qualify_answer(answer, claims, verdict, contradictions, refusal_level)

        report = FaithfulnessReport(
            claims=claims,
            supported_ratio=supported_ratio,
            numeric_consistency=numeric_ok,
            contradictions=contradictions,
            suspicious_evidence=suspicious,
            verdict=verdict,
            qualified_answer=qualified,
            refusal_level=refusal_level,
        )
        info(f"忠实度核查: verdict={verdict} level={refusal_level} "
             f"supported={supported}/{n} contradictions={len(contradictions)} "
             f"suspicious={len(suspicious)}")
        return report

    def _refusal_level(self, verdict: str, unsupported_ratio: float,
                       contradictions: list, evidence: list) -> int:
        """分级拒答：0 直接答 / 1 标注后答 / 2 部分答+教师复核 / 3 拒答降级"""
        if verdict == "insufficient_evidence" or unsupported_ratio > self.unsupported_refuse_ratio:
            return 3
        if contradictions or unsupported_ratio > self.teacher_review_ratio:
            return 2
        if unsupported_ratio > self.flagged_ratio or verdict == "partial":
            return 1
        return 0

    # ── 1. 句级归因核查 ────────────────────────────────────
    def verify_claims(self, answer: str, evidence: list[dict]) -> list[ClaimCheck]:
        """逐句核查：每个断言是否有证据支撑（词面+符号锚点）"""
        sentences = self._split_claims(answer)
        ev_sents = self._evidence_sentences(evidence)
        # 全证据文本：绑定值与公式锚点对全证据核对（公式常不在最佳句内）
        ev_all = "\n".join(s for s, _ in ev_sents)

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

            missing = self._missing_numbers(sent, best_ev, ev_all) if best_ev \
                else self._extract_numbers(sent)

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
        """三通道支撑分：Jaccard + 包含度 + 符号锚点加成"""
        ev_words = self._tokenize(ev_sent)
        if not sent_words or not ev_words:
            return 0.0
        from core.text_utils import containment, jaccard

        jac = jaccard(sent_words, ev_words)
        # 包含度：答案词被证据覆盖的比例（答案短句常是证据子集）
        contain = containment(sent_words, ev_words)
        score = max(jac, contain * 0.9)
        # 符号锚点加成：句中数值经归一化后在证据中命中（3/5≡0.6）
        nums = self._extract_numbers(sent)
        if nums and not self._missing_numbers(sent, ev_sent):
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

    # ── 4. 分级拒答/降级答案 ────────────────────────────────
    def qualify_answer(self, answer: str, claims: list[ClaimCheck],
                       verdict: str, contradictions: list[dict],
                       refusal_level: int = 0) -> str:
        """分级降级：0 直接答 / 1 标注后答 / 2 部分答+教师复核 / 3 拒答降级"""
        if refusal_level == 0 and not contradictions:
            return answer

        kept, flagged = [], []
        for c in claims:
            (kept if c.status == "supported" else flagged).append(c)

        if refusal_level == 3:
            if verdict == "insufficient_evidence":
                return ("【知识库中没有找到足够依据，以下为推测性回答，仅供参考】\n"
                        f"{answer}\n"
                        "【建议】请查阅教材原文或咨询老师确认。")
            return ("【警告】回答中大部分内容缺乏知识库依据，暂不提供结论，建议：\n"
                    "1. 核对提问是否超出当前知识库范围；\n"
                    "2. 查阅教材原文或咨询老师。\n"
                    + ("可供参考的有支撑片段：\n" + "\n".join(c.sentence for c in kept[:3])
                       if kept else ""))

        body_parts = []
        for c in claims:
            if c.status == "supported":
                body_parts.append(c.sentence)
            else:
                mark = f"〔待核实：{c.reason}〕" if c.reason else "〔待核实〕"
                body_parts.append(f"{c.sentence}（{mark}）")
        body = "".join(body_parts) if body_parts else answer

        tail = []
        if contradictions:
            kw_list = "、".join(c["keyword"] for c in contradictions[:3])
            resolved = [c for c in contradictions if c.get("preferred_doc_index") is not None]
            if resolved:
                tail.append(f"⚠ 证据间数值冲突（{kw_list}），已按来源权威度消解，"
                            f"建议以教材正文为准并人工复核。")
            else:
                tail.append(f"⚠ 证据间数值冲突（{kw_list}），请注意甄别（可能是教材版本差异）。")
        if any(c.false_dependency for c in claims):
            tail.append("⚠ 部分结论与其引用证据的真实依赖性存疑（存在事后合理化风险）。")

        if refusal_level == 2:
            header = "【教师复核提示】以下回答仅部分有知识库依据，不宜直接作为定论：\n"
            tail.append("【建议】请任课教师复核后再向学生发布。")
        else:
            header = "【提示】部分内容缺乏依据，已标注：\n"

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
        from core.text_utils import extract_numbers

        return extract_numbers(text)

    def _missing_numbers(self, claim: str, evidence_sent: str,
                         ev_all: str | None = None) -> list[str]:
        """符号锚点核查：数值归一化/容差（对最佳句）+ 绑定值/公式等价（对全证据）"""
        if not evidence_sent:
            return self._extract_numbers(claim)
        ev_all = ev_all if ev_all is not None else evidence_sent
        missing: list[str] = []

        # 1) 数值锚点：归一化等价（3/5≡0.6）→ 近似（容差）→ 数字组成覆盖
        ev_nums = set(self._extract_numbers(evidence_sent)) | set(re.findall(r"\d+", evidence_sent))
        for n in self._extract_numbers(claim):
            if self.use_norm:
                if any(numbers_equivalent(n, e) for e in ev_nums):
                    continue
                if any(numbers_near(n, e, rel_tol=self.near_tolerance, abs_tol=self.near_tolerance)
                       for e in ev_nums):
                    continue
            elif n in evidence_sent:
                continue
            parts = re.findall(r"\d+", n)
            if all(p in ev_nums for p in parts):
                continue
            missing.append(n)

        # 2) 绑定值锚点：'P(A)=3/5' 按符号绑定核对（对全证据，捕获改值型伪忠实）
        if self.use_bound:
            ev_binds = dict(extract_bound_values(ev_all))
            for sym, val in extract_bound_values(claim):
                if sym not in ev_binds:
                    continue
                if numbers_equivalent(val, ev_binds[sym]) or numbers_near(
                        val, ev_binds[sym], rel_tol=self.near_tolerance, abs_tol=self.near_tolerance):
                    continue
                missing.append(f"{sym}={val}")

        # 3) 公式等价锚点：答案中的公式须在全证据中有等价式（捕获改写型伪忠实）
        if self.use_formula:
            for m in _FORMULA_RE.finditer(claim):
                f = m.group(0).strip()
                if len(f) < 6:
                    continue
                ev_formulas = [x.group(0) for x in _FORMULA_RE.finditer(ev_all)]
                if not ev_formulas:
                    continue
                if not any(formulas_equivalent(f, ef) for ef in ev_formulas):
                    missing.append(f"公式:{f}")
        return missing

    # ── 2b. 权威度冲突消解 ─────────────────────────────────
    def resolve_conflicts(self, conflicts: list[dict], evidence: list[dict]) -> list[dict]:
        """跨文档数值冲突按来源权威度+版本消解（教材 > 课件 > 教辅 > 网络）"""
        def auth_of(idx: int) -> tuple[int, str]:
            doc = evidence[idx] if 0 <= idx < len(evidence) else {}
            st = (doc.get("source_type") or "unknown").lower()
            version = str(doc.get("version") or "")
            return SOURCE_AUTHORITY.get(st, SOURCE_AUTHORITY["unknown"]), version

        for c in conflicts:
            doc_ids = c.get("doc_indexes", [])
            if len(doc_ids) < 2:
                continue
            ranked = sorted(doc_ids, key=lambda i: auth_of(i), reverse=True)
            best_idx = ranked[0]
            best_auth, best_ver = auth_of(best_idx)
            rivals = [i for i in ranked[1:] if auth_of(i)[0] == best_auth]
            nums_by_doc = {}
            for kw_num_idx in range(len(c.get("numbers", []))):
                pass  # numbers 是去重后的集合，不带 doc；preferred 用 doc 侧文本反查
            if rivals:
                c["resolution"] = ("权威度并列，无法自动消解，需人工核对（版本差异或错误内容）")
                c["preferred_doc_index"] = None
            else:
                c["resolution"] = (
                    f"以权威度更高的来源为准（doc#{best_idx}，"
                    f"{evidence[best_idx].get('source_type') or 'unknown'}，版本 {best_ver or '—'}）"
                )
                c["preferred_doc_index"] = best_idx
            c["authority_ranked_docs"] = ranked
        return conflicts

    # ── 2c. 反事实证据依赖（真依赖 vs 事后合理化）─────────────
    def check_reliance(self, claims: list[ClaimCheck], evidence: list[dict]) -> None:
        """移除被引证据后支撑分应显著下降；不降 → 事后合理化（false_dependency）"""
        if not evidence:
            return
        ev_sents = self._evidence_sentences(evidence)
        for c in claims:
            if c.status != "supported" or c.best_evidence_idx < 0:
                continue
            sent_words = self._tokenize(c.sentence)
            score_without = 0.0
            for ev_sent, doc_idx in ev_sents:
                if doc_idx == c.best_evidence_idx:
                    continue
                s = self._support_score(c.sentence, sent_words, ev_sent)
                if s > score_without:
                    score_without = s
            c.reliance_drop = round(c.support_score - score_without, 4)
            if c.reliance_drop < self.reliance_drop_eps:
                c.false_dependency = True
                c.reason += f", false_dependency(drop={c.reliance_drop:.2f})"


# 全局单例
faithfulness_verifier = FaithfulnessVerifier()
