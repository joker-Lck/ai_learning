"""教学法对齐器（Pedagogy Aligner）

解决教育 RAG 的差异化缺口：检索"对"不等于教"对"。
现有系统检索只按语义相关性排序，不感知学生状态。本模块把「教学法」引入检索：

创新点:
1. 误解感知重排（misconception-aware rerank）
   - 学生错题本（error_notes）+ BKT 弱项 → 提升对应知识点证据（尤其"注意/易错"类块）
   - T1 结构分块的 kind 字段在此发挥价值：note/exercise 块对误解学生优先
2. 个性化重排（profile-aware rerank）
   - 学生画像 9 维（weak_points/learning_stage）→ 薄弱环节的证据加权
3. 脚手架上下文组装（scaffolding assembly）
   - 教学顺序：定义 → 定理/公式 → 例题 → 证明 → 注意/练习
   - 学习阶段感知：初学者定义前置，进阶者例题前置
   - 与 T1 expand_context 协同：组装时按教学法排序而非纯检索序
4. 教法依赖回链（dependency back-link，教法序列感知组装）
   - 命中例题/证明块时，沿"例题→所依定理→所依定义"回链拉入依赖块
   - 显式引用（定理1/定义2）优先，无显式引用时按 kind 优先级回退
   - 高价值证据排上下文首尾（RAG-Stress 位置规律：End > Beginning > Middle）

纯本地计算（无额外 LLM 调用），可插拔接在任意检索之后。
"""

from __future__ import annotations

import json
import re

from core.logger import debug, info, warning

# 教学顺序：脚手架默认排序（kind → 权重，小的排前）
PEDAGOGY_ORDER = {
    "definition": 0,
    "theorem": 1,
    "body": 2,
    "example": 3,
    "proof": 4,
    "note": 5,
    "exercise": 6,
    "context": 2,
}
# 进阶学生（learning_stage 高）例题/证明优先
ADVANCED_ORDER = {
    "example": 0,
    "proof": 1,
    "theorem": 2,
    "definition": 3,
    "body": 4,
    "note": 5,
    "exercise": 6,
    "context": 4,
}

# 显式教学引用：定理1 / 定义2 / 公式(3) / 引理1
_REF_RE = re.compile(r"(定义|定理|引理|公式|例题|例)\s*(\d+)")
# 依赖回链方向：命中块 kind → 需要拉入的依赖 kind（教学语义依赖序）
_DEPENDENCY_KINDS = {
    "example": ("theorem", "definition"),
    "proof": ("theorem", "definition"),
    "exercise": ("theorem", "definition"),
    "note": ("theorem", "definition"),
    "theorem": ("definition",),
}


def _get_profile_conn():
    from data import dbapi as dbapi
    from data.config import get_profile_db_path

    conn = dbapi.connect(get_profile_db_path())
    conn.row_factory = dbapi.Row
    return conn


class PedagogyAligner:
    """教学法对齐器"""

    # ── 学生状态信号 ───────────────────────────────────────
    def get_student_signals(self, user_id: int) -> dict:
        """聚合学生状态：错题主题 + BKT 弱项 + 画像薄弱环节 + 学习阶段"""
        signals = {
            "error_topics": [],      # 错题本里的主题词
            "weak_kps": [],          # BKT 弱项知识点
            "profile_weak": [],      # 画像 weak_points
            "learning_stage": 3,     # 1-5，画像 learning_stage
        }
        # 1) 错题本（最近 50 条的题干关键词 + knowledge_point）
        try:
            conn = _get_profile_conn()
            cur = conn.cursor()
            cur.execute(
                """SELECT question, tags, error_reason
                   FROM error_notes WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT 50""", (user_id,))
            for r in cur.fetchall():
                r = dict(r)
                for field in ("question", "tags", "error_reason"):
                    val = r.get(field) or ""
                    for kw in re.findall(r"[\u4e00-\u9fff]{2,8}", val):
                        if kw not in signals["error_topics"]:
                            signals["error_topics"].append(kw)
            conn.close()
        except Exception as e:
            debug(f"错题本信号读取降级: {e}")

        # 2) BKT 弱项
        try:
            from services.knowledge_tracer import knowledge_tracer
            signals["weak_kps"] = [
                s.knowledge_point for s in knowledge_tracer.get_weak_topics(user_id, threshold=0.5)
            ]
        except Exception as e:
            debug(f"BKT 弱项读取降级: {e}")

        # 3) 画像 weak_points / learning_stage
        try:
            conn = _get_profile_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT profile_data FROM student_profiles WHERE user_id = ? "
                "ORDER BY version DESC LIMIT 1", (user_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                pdata = dict(row).get("profile_data") or {}
                if isinstance(pdata, str):
                    pdata = json.loads(pdata) if pdata else {}
                weak = pdata.get("weak_points") or pdata.get("weakness") or []
                if isinstance(weak, str):
                    weak = [weak]
                signals["profile_weak"] = [str(w) for w in weak][:20]
                stage = pdata.get("learning_stage")
                if isinstance(stage, (int, float)):
                    signals["learning_stage"] = int(stage)
                elif isinstance(stage, str) and stage.strip().isdigit():
                    signals["learning_stage"] = int(stage.strip())
        except Exception as e:
            debug(f"画像信号读取降级: {e}")

        return signals

    # ── 1. 误解感知重排 ────────────────────────────────────
    def misconception_rerank(self, chunks: list[dict], user_id: int,
                             boost: float = 0.15) -> list[dict]:
        """错题/BKT 弱项相关的证据加权；note 类块对误解学生额外加权"""
        signals = self.get_student_signals(user_id)
        topics = signals["error_topics"] + signals["weak_kps"] + signals["profile_weak"]
        if not topics:
            return chunks

        def topic_hit(text: str) -> bool:
            return any(t and t in text for t in topics)

        reranked = []
        for c in chunks:
            score = c.get("similarity", c.get("probability", c.get("score", 0)))
            hay = f"{c.get('section_path', '')}\n{c.get('content_text') or c.get('text') or ''}"
            bonus = 0.0
            if topic_hit(hay):
                bonus += boost
                # 误解相关时，注意/易错类证据优先（教学价值更高）
                if c.get("kind") in ("note", "exercise"):
                    bonus += boost * 0.5
            new_c = dict(c)
            new_c["_pedagogy_bonus"] = round(bonus, 4)
            new_c["similarity"] = score + bonus
            reranked.append(new_c)

        reranked.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        info(f"误解感知重排: user={user_id} topics={len(topics)} boosted="
             f"{sum(1 for c in reranked if c.get('_pedagogy_bonus', 0) > 0)}")
        return reranked

    # ── 2. 脚手架排序 ──────────────────────────────────────
    def scaffold_order(self, chunks: list[dict], learning_stage: int = 3) -> list[dict]:
        """按教学法顺序组装：定义→定理→例题→证明→注意（按学习阶段微调）"""
        order_map = ADVANCED_ORDER if learning_stage >= 4 else PEDAGOGY_ORDER

        def sort_key(c):
            kind = c.get("kind", "body")
            # 同 kind 内保持原检索序（similarity 优先）
            return (order_map.get(kind, 2), -(c.get("similarity", 0)))

        return sorted(chunks, key=sort_key)

    # ── 2b. 教法依赖回链（教法序列感知组装）──────────────────
    def dependency_expand(self, chunks: list[dict], all_chunks: list[dict] | None = None,
                          max_extra: int = 3) -> list[dict]:
        """命中例题/证明块时，沿教学语义依赖回链拉入所依定理/定义。

        显式引用（"定理1"“定义2”）优先匹配；无显式引用时按 kind 优先级
        回退到同节最近的定理/定义块。返回 原块 + 依赖块（标 _dep_linked）。
        """
        if not chunks:
            return chunks
        pool = list(chunks)
        if all_chunks:
            known_ids = {c.get("chunk_id") or id(c) for c in chunks}
            pool += [c for c in all_chunks
                     if (c.get("chunk_id") or id(c)) not in known_ids]

        have = {c.get("chunk_id") or id(c) for c in chunks}
        extras: list[dict] = []
        for c in chunks:
            if c.get("kind") not in _DEPENDENCY_KINDS:
                continue
            text = c.get("content_text") or c.get("text") or ""
            path = c.get("section_path", "")
            need_kinds = _DEPENDENCY_KINDS[c.get("kind")]
            refs = {(m.group(1), m.group(2)) for m in _REF_RE.finditer(text)}

            candidates = []
            for p in pool:
                if (p.get("chunk_id") or id(p)) in have:
                    continue
                if p.get("kind") not in need_kinds:
                    continue
                if path and p.get("section_path", "") != path:
                    continue  # 依赖回链默认不跨节
                candidates.append(p)

            # 显式引用优先：定理1/定义2 精确命中
            linked = []
            for p in candidates:
                p_text = p.get("content_text") or p.get("text") or ""
                for label, num in refs:
                    if re.search(rf"{label}\s*{num}", p_text):
                        linked.append(p)
                        break
            # 逐级补齐依赖链：例题→定理→定义（显式命中后仍补缺口）
            linked_kinds = {p.get("kind") for p in linked}
            center = c.get("order", 0)
            for kind in need_kinds:
                if kind in linked_kinds:
                    continue
                same_kind = [p for p in candidates if p.get("kind") == kind]
                if same_kind:
                    same_kind.sort(key=lambda p: abs(p.get("order", 0) - center))
                    linked.append(same_kind[0])
                    linked_kinds.add(kind)

            for p in linked[:max_extra]:
                key = p.get("chunk_id") or id(p)
                if key in have:
                    continue
                new_c = dict(p)
                new_c["_dep_linked"] = True
                new_c["_dep_for"] = c.get("chunk_id")
                extras.append(new_c)
                have.add(key)

        if extras:
            info(f"教法依赖回链: 补入 {len(extras)} 个定理/定义依赖块")
        return chunks + extras

    # ── 3. 个性化上下文组装（与 T1 expand_context 协同）─────
    def assemble_scaffold_context(self, chunks: list[dict], user_id: int = 0,
                                  max_chars: int = 4800) -> str:
        """把（已重排的）块组装成教学顺序的上下文文本

        返回的文本结构：
          【知识框架】定义/定理 …
          【典型例题】…
          【证明思路】…
          【易错提醒】…
        """
        signals = self.get_student_signals(user_id) if user_id else {"learning_stage": 3}
        ordered = self.scaffold_order(chunks, signals.get("learning_stage", 3))

        sections = [
            ("知识框架", ("definition", "theorem", "body")),
            ("典型例题", ("example",)),
            ("证明思路", ("proof",)),
            ("易错提醒", ("note", "exercise")),
        ]

        def by_score(c):
            return c.get("similarity", c.get("probability", c.get("score", 0)))

        parts = []
        total = 0
        used = set()
        for title, kinds in sections:
            bucket = [c for c in ordered
                      if c.get("kind") in kinds and id(c) not in used]
            if not bucket:
                continue
            # 关键证据排上下文首尾：知识框架最高分在前，易错提醒最高分殿后
            if title == "知识框架":
                bucket.sort(key=by_score, reverse=True)
            elif title == "易错提醒":
                bucket.sort(key=by_score, reverse=True)
                bucket.reverse()
            texts = []
            for c in bucket:
                t = c.get("content_text") or c.get("text") or ""
                path = c.get("section_path") or ""
                seg = f"（{path}）{t}" if path else t
                if total + len(seg) > max_chars:
                    break
                texts.append(seg)
                used.add(id(c))
                total += len(seg)
            if texts:
                parts.append(f"【{title}】\n" + "\n".join(texts))

        return "\n\n".join(parts)

    # ── 4. 一站式：检索后教学对齐 ─────────────────────────
    def align(self, chunks: list[dict], user_id: int, query: str = "",
              all_chunks: list[dict] | None = None) -> list[dict]:
        """依赖回链 + 重排 + 脚手架序输出（供 TutorAgent/检索层直接调用）"""
        if not chunks:
            return chunks
        expanded = self.dependency_expand(chunks, all_chunks)
        reranked = self.misconception_rerank(expanded, user_id)
        signals = self.get_student_signals(user_id)
        return self.scaffold_order(reranked, signals.get("learning_stage", 3))


# 全局单例
pedagogy_aligner = PedagogyAligner()
