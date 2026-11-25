#!/usr/bin/env python3
"""T4 集成测试：教学法对齐（误解重排/脚手架/画像/一站式）"""
import sys, os, json
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

def main():
    from data import dbapi as dbapi
    from data.config import get_profile_db_path
    from services.pedagogy_aligner import pedagogy_aligner as pa

    uid = 88001

    # ── 准备数据：错题本 + 画像 ──
    conn = dbapi.connect(get_profile_db_path())
    conn.row_factory = dbapi.Row
    cur = conn.cursor()
    cur.execute("DELETE FROM error_notes WHERE user_id = ?", (uid,))
    cur.execute("DELETE FROM student_profiles WHERE user_id = ?", (uid,))
    cur.execute(
        "INSERT INTO error_notes (user_id, subject, question, my_answer, correct_answer, "
        "error_reason, tags, mastery) VALUES (?,?,?,?,?,?,?,?)",
        (uid, "数学", "求方程x^2-4x+3=0的根", "x=2", "x=1或x=3", "因式分解错误", "一元二次方程,因式分解", 0))
    cur.execute(
        "INSERT INTO student_profiles (user_id, profile_data, version) VALUES (?,?,?)",
        (uid, json.dumps({"weak_points": ["韦达定理"], "learning_stage": 2}, ensure_ascii=False), 1))
    conn.commit()
    conn.close()

    # ── 1. 学生信号聚合 ──
    sig = pa.get_student_signals(uid)
    print("[1] signals:", {k: (v[:5] if isinstance(v, list) else v) for k, v in sig.items()})
    assert "因式分解" in sig["error_topics"], sig["error_topics"]
    assert "韦达定理" in sig["profile_weak"]
    assert sig["learning_stage"] == 2

    # ── 2. 误解感知重排：因式分解相关块应被提升 ──
    chunks = [
        {"content_text": "因式分解得(x-1)(x-3)=0", "kind": "example", "similarity": 0.60,
         "section_path": "2.1 › 例题1"},
        {"content_text": "韦达定理：x1+x2=-b/a", "kind": "theorem", "similarity": 0.62,
         "section_path": "2.2"},
        {"content_text": "注意：因式分解时注意符号", "kind": "note", "similarity": 0.55,
         "section_path": "2.1 › 易错"},
        {"content_text": "三角函数的周期是2π", "kind": "body", "similarity": 0.70,
         "section_path": "5.1"},
    ]
    r2 = pa.misconception_rerank(chunks, uid)
    print("[2] rerank order:")
    for c in r2:
        print(f"    sim={c['similarity']:.3f} bonus={c['_pedagogy_bonus']} {c['content_text'][:22]}")
    # 因式分解 example(0.60+0.15=0.75) 应超过三角函数(0.70)
    assert "因式分解" in r2[0]["content_text"], r2[0]
    # note 块命中主题且 kind=note → bonus 0.15+0.075=0.225 → 0.775 应第一
    assert r2[0]["kind"] == "note", f"note 块应最高: {r2[0]}"
    assert r2[0]["_pedagogy_bonus"] >= 0.2, r2[0]["_pedagogy_bonus"]

    # ── 3. 脚手架排序：初学者 definition 前置 ──
    mixed = [
        {"content_text": "证明：…", "kind": "proof", "similarity": 0.9},
        {"content_text": "例题：…", "kind": "example", "similarity": 0.9},
        {"content_text": "定义：…", "kind": "definition", "similarity": 0.9},
        {"content_text": "定理：…", "kind": "theorem", "similarity": 0.9},
    ]
    s3 = pa.scaffold_order(mixed, learning_stage=2)
    kinds3 = [c["kind"] for c in s3]
    print("[3] beginner order:", kinds3)
    assert kinds3 == ["definition", "theorem", "example", "proof"], kinds3
    s3b = pa.scaffold_order(mixed, learning_stage=5)
    kinds3b = [c["kind"] for c in s3b]
    print("[3b] advanced order:", kinds3b)
    assert kinds3b[0] == "example", kinds3b  # 进阶者例题优先

    # ── 4. 脚手架上下文组装 ──
    ctx = pa.assemble_scaffold_context(mixed, user_id=uid, max_chars=4800)
    print("[4] scaffold context:")
    for line in ctx.split("\n"):
        if line.startswith("【"):
            print(f"    {line}")
    assert "【知识框架】" in ctx and "【典型例题】" in ctx
    assert ctx.index("【知识框架】") < ctx.index("【典型例题】") < ctx.index("【证明思路】")

    # ── 5. 一站式 align ──
    r5 = pa.align(chunks, uid, query="因式分解怎么做")
    print("[5] aligned top-2:", [(c['kind'], round(c['similarity'],3)) for c in r5[:2]])
    assert r5, "align 为空"
    assert r5[0]["_pedagogy_bonus"] > 0, "首位应有教学加权"

    # ── 6. 教法依赖回链：例题 → 所依定理 → 定义 ──
    all_chunks = [
        {"chunk_id": "c_def", "content_text": "定义2：设A、B为事件，P(B)>0，则P(A|B)=P(AB)/P(B)。",
         "kind": "definition", "order": 2, "section_path": "3.2 › 一、条件概率公式"},
        {"chunk_id": "c_thm", "content_text": "定理1（全概率公式）：设B1,B2为完备事件组，P(A)=ΣP(Bi)P(A|Bi)。",
         "kind": "theorem", "order": 3, "section_path": "3.2 › 一、条件概率公式"},
        {"chunk_id": "c_ex", "content_text": "例题1：袋中3个红球2个白球，由定理1得P(A)=3/5。",
         "kind": "example", "order": 4, "section_path": "3.2 › 一、条件概率公式"},
        {"chunk_id": "c_other", "content_text": "定理9：与本节无关。",
         "kind": "theorem", "order": 9, "section_path": "4.1"},
    ]
    hit = [dict(all_chunks[2], similarity=0.9)]
    r6 = pa.dependency_expand(hit, all_chunks)
    ids6 = {c.get("chunk_id") for c in r6}
    kinds6 = sorted(c["kind"] for c in r6)
    print(f"[6] dependency_expand ids={ids6}")
    assert "c_thm" in ids6, "应按显式引用拉入定理1"
    assert "c_def" in ids6, "应逐级补齐定义2"
    assert "c_other" not in ids6, "不应跨节拉入"
    assert any(c.get("_dep_linked") for c in r6), "依赖块应打标"

    # 依赖块进入脚手架组装后按教学序排布（知识框架在前）
    ctx6 = pa.assemble_scaffold_context(r6, user_id=0, max_chars=4800)
    assert "【知识框架】" in ctx6 and "【典型例题】" in ctx6
    assert ctx6.index("【知识框架】") < ctx6.index("【典型例题】")

    print("\nT4 INTEGRATION PASSED")

if __name__ == "__main__":
    main()
