#!/usr/bin/env python3
"""T2 集成测试：学习增益评估（快照/增益/误解纠正/覆盖率/报告）"""
import sys, os
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

def main():
    from services.learning_gain_evaluator import learning_gain_evaluator as ev
    from services.knowledge_tracer import knowledge_tracer

    uid = 99001
    sid = "test-session-001"
    kps = ["一元二次方程", "韦达定理", "因式分解"]

    # ── 1. 前测快照 ──
    r1 = ev.capture_snapshot(uid, kps, phase="pre", session_id=sid)
    print("[1] pre:", r1["message"], r1.get("data", {}).get("snapshots"))
    assert r1["success"], r1

    # ── 2. 模拟学习：BKT 更新（答对）──
    for kp in kps:
        for _ in range(4):
            knowledge_tracer.update(kp, True, "fill_blank", user_id=uid)
    pre_m = {kp: knowledge_tracer.get_mastery(kp, user_id=uid) for kp in kps}
    print("[2] post-mastery:", pre_m)

    # ── 3. 后测快照 + 增益 ──
    r2 = ev.capture_snapshot(uid, kps, phase="post", session_id=sid)
    assert r2["success"], r2
    r3 = ev.compute_gain(uid, session_id=sid)
    print("[3] gain:", r3["message"])
    data3 = r3["data"]
    for d in data3["details"]:
        print(f"    {d['knowledge_point']}: pre={d.get('pre')} post={d.get('post')} "
              f"norm_gain={d.get('norm_gain')} bin={d.get('bin')}")
    print("    aggregate:", data3["aggregate"])
    assert r3["success"], r3
    agg = data3["aggregate"]
    assert agg["n_complete"] == 3, f"配对数不对: {agg}"
    assert agg["mean_norm_gain"] and agg["mean_norm_gain"] > 0, "学习增益应为正"
    assert agg["bin_distribution"]["low"] + agg["bin_distribution"]["medium"] + agg["bin_distribution"]["high"] == 3

    # ── 4. 误解纠正率（直接灌 quiz_answers 时序）──
    import json
    from data import dbapi as dbapi
    from data.config import get_assessments_db_path
    ev.ensure_table()
    conn = dbapi.connect(get_assessments_db_path())
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS quiz_answers ("
                "id BIGINT AUTO_INCREMENT PRIMARY KEY,"
                "session_id BIGINT NOT NULL,"
                "user_id BIGINT NOT NULL,"
                "question_index INT NOT NULL,"
                "question_type VARCHAR(64),"
                "question_text TEXT NOT NULL,"
                "options TEXT,"
                "correct_answer TEXT NOT NULL,"
                "user_answer TEXT,"
                "is_correct TINYINT DEFAULT 0,"
                "explanation TEXT,"
                "knowledge_point VARCHAR(255),"
                "difficulty VARCHAR(32),"
                "time_spent_seconds INT DEFAULT 0,"
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "KEY idx_quiz_answers_session (session_id))")
    # 清旧测试数据
    cur.execute("DELETE FROM quiz_answers WHERE user_id = ?", (uid,))
    # kpA: 错→对（应纠正）；kpB: 错→错（不纠正）；kpC: 对→对（不算误解）
    rows = [
        (990, uid, 1, "choice", "q1", "", "A", "B", 0, "", "一元二次方程", "easy", 0, "2026-11-01 10:00:00"),
        (990, uid, 2, "choice", "q2", "", "A", "A", 1, "", "一元二次方程", "easy", 0, "2026-11-02 10:00:00"),
        (990, uid, 3, "choice", "q3", "", "A", "B", 0, "", "韦达定理", "easy", 0, "2026-11-01 11:00:00"),
        (990, uid, 4, "choice", "q4", "", "A", "C", 0, "", "韦达定理", "easy", 0, "2026-11-02 11:00:00"),
        (990, uid, 5, "choice", "q5", "", "A", "A", 1, "", "因式分解", "easy", 0, "2026-11-01 12:00:00"),
    ]
    for r in rows:
        cur.execute(
            "INSERT INTO quiz_answers (session_id, user_id, question_index, question_type, "
            "question_text, options, correct_answer, user_answer, is_correct, explanation, "
            "knowledge_point, difficulty, time_spent_seconds, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
    conn.commit()
    conn.close()

    r4 = ev.misconception_correction_rate(uid)
    print("[4] correction:", r4["message"])
    d4 = r4["data"]
    print(f"    errored={d4['errored_kps']} corrected={d4['corrected_kps']} rate={d4['correction_rate']}")
    assert r4["success"], r4
    assert d4["errored_kps"] == 2, f"误解知识点数应=2: {d4}"
    assert d4["corrected_kps"] == 1, f"纠正数应=1: {d4}"
    assert abs(d4["correction_rate"] - 0.5) < 1e-6, f"纠正率应=0.5: {d4['correction_rate']}"

    # ── 5. 知识覆盖率 ──
    retrieved = [
        {"content_text": "定理1（求根公式）：x=(-b±√(b^2-4ac))/(2a)", "section_path": "第2章 › 2.1"},
        {"content_text": "因式分解得(x-1)(x-3)=0", "section_path": "第2章 › 2.1 › 例题1"},
    ]
    r5 = ev.knowledge_coverage(["求根公式", "因式分解", "韦达定理"], retrieved)
    print("[5] coverage:", r5["data"])
    assert r5["success"], r5
    d5 = r5["data"]
    assert d5["n_required"] == 3 and d5["n_covered"] == 2, f"覆盖数应=2/3: {d5}"
    assert "韦达定理" in d5["missing"], "韦达定理应缺失"

    # ── 6. 一站式报告 ──
    r6 = ev.learning_report(uid, session_id=sid)
    print("[6] report:", r6["message"])
    assert r6["success"], r6
    assert "learning_gain" in r6["data"] and "misconception_correction" in r6["data"]
    assert "weak_topics" in r6["data"]

    print("\nT2 INTEGRATION PASSED")

if __name__ == "__main__":
    main()
