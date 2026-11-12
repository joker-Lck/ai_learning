#!/usr/bin/env python3
"""structure_chunker 单测：结构识别 + 切块 + 上下文扩展"""
import sys, os
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

from data.structure_chunker import StructureChunker, expand_context

SAMPLE = """第3章 概率论基础

3.1 随机事件与概率

一、随机事件
随机事件是指在一定条件下可能发生也可能不发生的事件。样本空间是所有可能结果的集合。

二、概率的定义
定义1：概率是衡量事件发生可能性大小的数值，取值范围为[0,1]。
概率具有非负性、规范性和可列可加性。

3.2 条件概率

一、条件概率公式
定义2：设A、B为两个事件，P(B)>0，则P(A|B)=P(AB)/P(B)。
定理1（全概率公式）：设B1,B2,...,Bn为完备事件组，P(Bi)>0，则P(A)=ΣP(Bi)P(A|Bi)。

例题1：袋中有3个红球2个白球，不放回抽取两次，求第二次取到红球的概率。
证明：设A=第二次取到红球，由全概率公式，P(A)=P(B1)P(A|B1)+P(B2)P(A|B2)。
代入数据计算可得P(A)=3/5。

注意：全概率公式的关键是找到完备事件组。

第4章 随机变量

4.1 离散型随机变量
离散型随机变量的分布列描述其概率规律。常见的有二项分布、泊松分布。
"""

def main():
    chunker = StructureChunker(max_length=200, min_length=30)
    tree = chunker.chunk(SAMPLE, doc_id=1)

    print("=== 结构大纲 ===")
    for s in tree.sections:
        print(f"  L{s['level']}: {s['path']}")
    print("\n=== 统计 ===")
    print(tree.stats)

    print("\n=== 切块 ===")
    for c in tree.chunks:
        print(f"[{c.order}] L{c.level} kind={c.kind} path='{c.section_path}'")
        print(f"     {c.text[:60].replace(chr(10), ' / ')}...")

    # 断言
    assert tree.stats["structure_found"], "未识别出结构"
    assert tree.stats["n_sections"] >= 6, f"节数过少: {tree.stats['n_sections']}"
    kinds = set(c.kind for c in tree.chunks)
    assert "definition" in kinds, "未识别定义块"
    assert "theorem" in kinds, "未识别定理块"
    assert "example" in kinds or "proof" in kinds, "未识别例题/证明块"
    # section_path 应含层级链
    paths = [c.section_path for c in tree.chunks if c.section_path]
    assert any("3.2" in p for p in paths), "3.2 节路径缺失"
    assert any("›" in p for p in paths), "层级路径未串联"
    # 证明完整性：证明句不应被拦腰截断（含'由全概率公式'的块应同时含'代入数据'）
    proof_blocks = [c.text for c in tree.chunks if "全概率公式，P(A)" in c.text]
    assert proof_blocks and all("代入数据" in t or "P(A)=P(B1)" in t for t in proof_blocks), "证明链被切断"

    # 上下文扩展测试
    all_c = [c.to_dict() | {"doc_id": 1} for c in tree.chunks]
    hits = [all_c[i] | {"similarity": 0.9 - i * 0.05} for i in (4, 7)]
    contexts = expand_context(hits, all_c, max_chars=4800, neighbor_window=1)
    print("\n=== 上下文扩展 ===")
    for ctx in contexts:
        print(f"  score={ctx['score']:.2f} expanded={ctx.get('expanded')} ids={ctx['chunk_ids']}")
        print(f"  {ctx['context_text'][:80].replace(chr(10), ' / ')}...")
    assert contexts, "扩展结果为空"
    assert any(ctx.get("expanded") for ctx in contexts), "邻域未扩展"

    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    main()
