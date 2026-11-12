"""学习增益导向评估（Learning Gain Evaluator）

解决教育 RAG 评估的核心缺口：主流指标（faithfulness/accuracy 等）全是技术性的，
缺少「学习成效」维度。本模块把评估接到学习科学上：

1. BKT 前测/后测快照（learning_gain_snapshots 表）
   —— 捕获学习会话前后各知识点掌握度，评估 RAG 辅导是否真正提升掌握；
2. 归一化学习增益（Hake's normalized gain g）
   —— g = (post - pre) / (1 - pre)，跨知识点/跨学生可比；
3. 误解纠正率（misconception correction rate）
   —— 同一知识点「答错 → 后来答对」的比例（quiz_answers 时序信号）；
4. 知识覆盖率（knowledge coverage）
   —— 提问所需知识点被检索证据（分块 section_path/text）覆盖的比例，
   与 T1 教学结构感知检索直接闭环：结构化分块使覆盖可度量。

评估口径:
- 掌握度来源默认 BKT（knowledge_tracer），可外接其他知识追踪器；
- 所有指标都给出分子/分母，不用单一分数掩盖样本量问题。
"""

from __future__ import annotations

import json
from datetime import datetime

from core.logger import error, info, warning

# 归一化增益的解释阈值（Hake 惯例：<0.3 低 / 0.3-0.7 中 / >0.7 高）
GAIN_BINS = {"low": 0.3, "medium": 0.7}


def _get_assessments_conn():
    """连接 ai_assessments 库（学习增益快照 + 答题记录均在此）"""
    from data import dbapi as dbapi
    from data.config import get_assessments_db_path

    conn = dbapi.connect(get_assessments_db_path())
    conn.row_factory = dbapi.Row
    return conn


class LearningGainEvaluator:
    """学习增益评估器"""

    # ── 快照表 ────────────────────────────────────────────
    def ensure_table(self) -> bool:
        """确保 learning_gain_snapshots 表存在"""
        conn = None
        try:
            conn = _get_assessments_conn()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_gain_snapshots (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    session_id VARCHAR(64),
                    phase VARCHAR(16) NOT NULL,
                    knowledge_point VARCHAR(191) NOT NULL,
                    mastery DECIMAL(6,4) DEFAULT 0,
                    source VARCHAR(32) DEFAULT 'bkt',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_lgs_user_kp (user_id, knowledge_point),
                    KEY idx_lgs_session (session_id)
                )""")
            conn.commit()
            return True
        except Exception as e:
            warning(f"learning_gain_snapshots 建表失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ── 1. 前测/后测快照 ─────────────────────────────────
    def capture_snapshot(
        self,
        user_id: int,
        knowledge_points: list[str],
        phase: str = "pre",
        session_id: str | None = None,
        source: str = "bkt",
    ) -> dict:
        """捕获学习前/后的知识点掌握度快照

        参数:
            user_id: 学生
            knowledge_points: 知识点列表（空则取该生弱项全集）
            phase: 'pre'（前测）或 'post'（后测）
            session_id: 学习会话标识（前/后测配对依据）
            source: 掌握度来源（默认 BKT）
        """
        if phase not in ("pre", "post"):
            return {"success": False, "message": "phase 必须是 pre/post"}
        try:
            from services.knowledge_tracer import knowledge_tracer

            kps = list(knowledge_points or [])
            if not kps:
                kps = [s.knowledge_point for s in knowledge_tracer.get_weak_topics(user_id, threshold=1.0)]
            if not kps:
                return {"success": False, "message": "无知识点可快照（请指定 knowledge_points）"}

            self.ensure_table()
            conn = _get_assessments_conn()
            cur = conn.cursor()
            saved = []
            now = datetime.now()
            for kp in kps:
                mastery = knowledge_tracer.get_mastery(kp, user_id=user_id)
                cur.execute(
                    """INSERT INTO learning_gain_snapshots
                       (user_id, session_id, phase, knowledge_point, mastery, source, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, session_id or f"auto-{now.strftime('%Y%m%d%H%M%S')}",
                     phase, kp, float(mastery), source, now),
                )
                saved.append({"knowledge_point": kp, "mastery": round(float(mastery), 4)})
            conn.commit()
            conn.close()
            info(f"学习增益快照: user={user_id} phase={phase} kps={len(saved)}")
            return {
                "success": True,
                "message": f"{phase} 快照完成",
                "data": {"phase": phase, "session_id": session_id, "snapshots": saved},
            }
        except Exception as e:
            error(f"快照捕获失败: {e}")
            return {"success": False, "message": str(e)}

    # ── 2. 归一化学习增益 ─────────────────────────────────
    def compute_gain(self, user_id: int, session_id: str | None = None,
                     knowledge_points: list[str] | None = None) -> dict:
        """计算前测→后测的学习增益（Hake's normalized gain）

        g = (post - pre) / (1 - pre)；pre≈1 时退化为绝对增益。
        输出逐知识点 + 聚合（均值/中位数/分档），全部带分子分母。
        """
        try:
            self.ensure_table()
            conn = _get_assessments_conn()
            cur = conn.cursor()

            # 取该用户最近一组 pre/post 配对（按 session 或全局最近）
            sql = """SELECT session_id, phase, knowledge_point, mastery, created_at
                     FROM learning_gain_snapshots
                     WHERE user_id = ?"""
            params: list = [user_id]
            if session_id:
                sql += " AND session_id = ?"
                params.append(session_id)
            if knowledge_points:
                sql += f" AND knowledge_point IN ({','.join(['?'] * len(knowledge_points))})"
                params.extend(knowledge_points)
            sql += " ORDER BY created_at ASC"
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            if not rows:
                return {"success": False, "message": "无快照数据，请先 capture_snapshot(pre/post)"}

            # 每个知识点取最早的 pre 和最晚的 post
            pairs = {}
            for r in rows:
                kp = r["knowledge_point"]
                p = pairs.setdefault(kp, {"pre": None, "post": None})
                if r["phase"] == "pre" and p["pre"] is None:
                    p["pre"] = r
                if r["phase"] == "post":
                    p["post"] = r  # 最晚的 post 覆盖（ordered ASC）

            details = []
            gains = []
            for kp, p in pairs.items():
                pre_row, post_row = p["pre"], p["post"]
                if not pre_row or not post_row:
                    details.append({
                        "knowledge_point": kp,
                        "status": "incomplete",
                        "pre": pre_row["mastery"] if pre_row else None,
                        "post": post_row["mastery"] if post_row else None,
                    })
                    continue
                pre = float(pre_row["mastery"])
                post = float(post_row["mastery"])
                abs_gain = post - pre
                norm_gain = abs_gain / (1 - pre) if pre < 0.999 else abs_gain
                norm_gain = max(-1.0, min(1.0, norm_gain))
                bin_ = ("high" if norm_gain > GAIN_BINS["medium"]
                        else "medium" if norm_gain >= GAIN_BINS["low"]
                        else "low")
                gains.append(norm_gain)
                details.append({
                    "knowledge_point": kp,
                    "status": "complete",
                    "pre": round(pre, 4),
                    "post": round(post, 4),
                    "abs_gain": round(abs_gain, 4),
                    "norm_gain": round(norm_gain, 4),
                    "bin": bin_,
                })

            complete = [d for d in details if d["status"] == "complete"]
            agg = {
                "n_knowledge_points": len(pairs),
                "n_complete": len(complete),
                "mean_norm_gain": round(sum(gains) / len(gains), 4) if gains else None,
                "bin_distribution": {
                    "low": sum(1 for d in complete if d["bin"] == "low"),
                    "medium": sum(1 for d in complete if d["bin"] == "medium"),
                    "high": sum(1 for d in complete if d["bin"] == "high"),
                },
            }
            return {"success": True, "message": "增益计算完成",
                    "data": {"details": details, "aggregate": agg}}
        except Exception as e:
            error(f"学习增益计算失败: {e}")
            return {"success": False, "message": str(e)}

    # ── 3. 误解纠正率 ─────────────────────────────────────
    def misconception_correction_rate(self, user_id: int, subject: str | None = None) -> dict:
        """误解纠正率：同一知识点「先答错 → 后答对」的比例

        数据源: quiz_answers 时序（按 created_at 排序）。
        分母 = 出现过答错的知识点数；分子 = 其中后来答对的知识点数。
        """
        try:
            conn = _get_assessments_conn()
            cur = conn.cursor()
            sql = """SELECT knowledge_point, is_correct, created_at, question_type
                     FROM quiz_answers
                     WHERE user_id = ? AND knowledge_point IS NOT NULL
                     ORDER BY created_at ASC"""
            params: list = [user_id]
            if subject:
                # quiz_answers 无 subject 列，用题干/知识点过滤近似；此处仅按知识点
                pass
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            if not rows:
                return {"success": True, "message": "无答题记录",
                        "data": {"errored_kps": 0, "corrected_kps": 0,
                                 "correction_rate": None, "details": []}}

            # 逐知识点：曾错且后来对 → corrected
            kp_state: dict[str, dict] = {}
            for r in rows:
                kp = r["knowledge_point"]
                st = kp_state.setdefault(kp, {"ever_wrong": False, "wrong_first": False,
                                              "corrected": False, "n": 0, "n_correct": 0})
                st["n"] += 1
                ok = bool(r["is_correct"])
                if ok:
                    st["n_correct"] += 1
                    if st["ever_wrong"]:
                        st["corrected"] = True
                else:
                    if st["n_correct"] == 0 and not st["ever_wrong"]:
                        st["wrong_first"] = True  # 首次即错（误解起点）
                    st["ever_wrong"] = True

            errored = [kp for kp, st in kp_state.items() if st["ever_wrong"]]
            corrected = [kp for kp in errored if kp_state[kp]["corrected"]]
            rate = (len(corrected) / len(errored)) if errored else None

            details = [
                {
                    "knowledge_point": kp,
                    "n_attempts": kp_state[kp]["n"],
                    "n_correct": kp_state[kp]["n_correct"],
                    "corrected": kp_state[kp]["corrected"],
                }
                for kp in sorted(errored)
            ]
            return {
                "success": True,
                "message": "误解纠正率计算完成",
                "data": {
                    "errored_kps": len(errored),
                    "corrected_kps": len(corrected),
                    "correction_rate": round(rate, 4) if rate is not None else None,
                    "total_kps": len(kp_state),
                    "details": details,
                },
            }
        except Exception as e:
            error(f"误解纠正率计算失败: {e}")
            return {"success": False, "message": str(e)}

    # ── 4. 知识覆盖率 ─────────────────────────────────────
    def knowledge_coverage(self, query_knowledge_points: list[str],
                           retrieved_chunks: list[dict]) -> dict:
        """知识覆盖率：提问所需知识点被检索证据覆盖的比例

        与 T1 结构感知检索闭环：分块携带 section_path/kind，
        覆盖判定 = 知识点名出现在 命中块 text / section_path / heading 中。

        参数:
            query_knowledge_points: 问题所需知识点（来自出题标注或 LLM 抽取）
            retrieved_chunks: 检索结果（结构检索返回的 content_text/section_path），
                              或 [{text, section_path}] 通用格式

        返回: {coverage, covered[], missing[], evidence_map}
        """
        if not query_knowledge_points:
            return {"success": False, "message": "query_knowledge_points 不能为空"}
        try:
            # 证据语料：每块拼 text + path + heading
            blocks = []
            for c in retrieved_chunks or []:
                text = c.get("content_text") or c.get("text") or ""
                path = c.get("section_path") or ""
                heading = c.get("heading") or ""
                blocks.append({"haystack": f"{path}\n{heading}\n{text}",
                               "ref": {"chunk_ids": c.get("chunk_ids") or [c.get("chunk_id")],
                                       "section_path": path}})

            covered, missing, evidence_map = [], [], {}
            for kp in query_knowledge_points:
                kp_norm = kp.strip().lower()
                hit = None
                for b in blocks:
                    if kp_norm and kp_norm in b["haystack"].lower():
                        hit = b["ref"]
                        break
                if hit:
                    covered.append(kp)
                    evidence_map[kp] = hit
                else:
                    missing.append(kp)

            total = len(query_knowledge_points)
            return {
                "success": True,
                "message": "覆盖率计算完成",
                "data": {
                    "coverage": round(len(covered) / total, 4) if total else None,
                    "n_required": total,
                    "n_covered": len(covered),
                    "covered": covered,
                    "missing": missing,
                    "evidence_map": evidence_map,
                },
            }
        except Exception as e:
            error(f"知识覆盖率计算失败: {e}")
            return {"success": False, "message": str(e)}

    # ── 5. 学习报告（一站式）─────────────────────────────
    def learning_report(self, user_id: int, session_id: str | None = None,
                        subject: str | None = None) -> dict:
        """学习成效报告：增益 + 误解纠正率 + 弱项，一站式聚合"""
        try:
            from services.knowledge_tracer import knowledge_tracer

            gain = self.compute_gain(user_id, session_id=session_id)
            correction = self.misconception_correction_rate(user_id, subject=subject)
            weak = [
                {"knowledge_point": s.knowledge_point, "mastery": round(s.mastery, 4)}
                for s in knowledge_tracer.get_weak_topics(user_id, threshold=0.5)
            ]
            return {
                "success": True,
                "message": "学习报告生成完成",
                "data": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "learning_gain": gain.get("data") if gain.get("success") else {"error": gain.get("message")},
                    "misconception_correction": correction.get("data") if correction.get("success") else {"error": correction.get("message")},
                    "weak_topics": weak,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        except Exception as e:
            error(f"学习报告生成失败: {e}")
            return {"success": False, "message": str(e)}


# 全局单例
learning_gain_evaluator = LearningGainEvaluator()
