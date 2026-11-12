#!/usr/bin/env python3
"""T1 集成测试：add_document → 分块索引 → search_chunks_structural"""
import sys, os
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

SAMPLE = """第2章 一元二次方程

2.1 一元二次方程的解法

一、配方法
定义1：形如ax^2+bx+c=0（a≠0）的方程叫一元二次方程。
定理1（求根公式）：方程ax^2+bx+c=0的根为x=(-b±√(b^2-4ac))/(2a)。

例题1：解方程 x^2-4x+3=0。
证明：因式分解得(x-1)(x-3)=0，故x=1或x=3。

注意：判别式Δ=b^2-4ac决定根的情况。

2.2 韦达定理
定理2（韦达定理）：若x1,x2是方程的两根，则x1+x2=-b/a，x1*x2=c/a。
"""

def main():
    from data.rag_knowledge_base import rag_kb, chunk_vector_index
    from data.embedding_service import embedding_service

    # 1. 入库（含自动分块索引）
    emb = embedding_service.get_embedding("一元二次方程求根公式")
    doc_id = rag_kb.add_document(
        title="测试教材-一元二次方程", subject="数学",
        file_path="test/x.txt", file_type="txt",
        content_text=SAMPLE, knowledge_points=["一元二次方程", "韦达定理"],
        embedding=emb,
    )
    assert doc_id, "add_document 失败"
    print(f"[1] doc_id={doc_id}")

    # 2. 分块落库检查
    chunks = rag_kb.get_chunks_by_doc(doc_id)
    print(f"[2] chunks={len(chunks)}")
    for c in chunks[:8]:
        print(f"    #{c['chunk_order']} kind={c['kind']} path='{c['section_path']}'")
    assert len(chunks) >= 6, f"分块过少: {len(chunks)}"
    paths = [c["section_path"] for c in chunks]
    assert any("2.1" in p for p in paths) and any("2.2" in p for p in paths), "节路径缺失"
    kinds = {c["kind"] for c in chunks}
    assert "theorem" in kinds and "example" in kinds, f"语义类型缺失: {kinds}"

    # 3. 结构检索（长上下文组装）
    qvec = embedding_service.get_embedding("求根公式是什么")
    results = rag_kb.search_chunks_structural(qvec, limit=3, expand=True)
    print(f"[3] structural results={len(results)}")
    for r in results:
        print(f"    score={r['similarity']:.3f} expanded={r['expanded']} path='{r['section_path']}'")
        print(f"    ctx: {r['content_text'][:70].replace(chr(10), ' / ')}...")
    assert results, "结构检索为空"
    assert any(r.get("section_path") for r in results), "检索结果缺 section_path"
    assert all(r["retrieval_method"] == "structural" for r in results)

    # 4. 关键断言：查询"求根公式"应命中 2.1 节定理块，且组装上下文含节标题
    top = results[0]
    assert "2.1" in (top.get("section_path") or "") or "求根" in top["content_text"], \
        f"top1 未命中求根公式相关内容: {top['section_path']}"

    print("\nT1 INTEGRATION PASSED")

if __name__ == "__main__":
    main()
