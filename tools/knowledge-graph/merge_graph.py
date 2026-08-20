"""
知识图谱合并器
合并 graph-draft.json (自动扫描) + annotations.yaml (手动标注) → graph-data.json
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("需要安装 PyYAML: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = Path(__file__).resolve().parent


def load_draft() -> dict:
    """加载自动扫描结果"""
    path = TOOLS_DIR / "graph-draft.json"
    if not path.exists():
        print(f"错误: 未找到 {path}，请先运行 extract_graph.py")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_annotations() -> dict:
    """加载手动标注"""
    path = TOOLS_DIR / "annotations.yaml"
    if not path.exists():
        print(f"警告: 未找到 {path}，跳过手动标注")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def merge_graph(draft: dict, annotations: dict) -> dict:
    """合并图谱"""
    nodes = draft["nodes"]
    edges = draft["edges"]

    # 建立节点索引
    node_index = {n["id"]: n for n in nodes}

    # ── 1. 填充描述 ──
    descriptions = annotations.get("descriptions", {})
    for node in nodes:
        nid = node["id"]
        if nid in descriptions:
            node["description"] = descriptions[nid]
        elif not node.get("description"):
            node["description"] = ""

    # ── 2. 添加额外边 ──
    extra_edges = annotations.get("extra_edges", [])
    for ee in extra_edges:
        source = ee["source"]
        target = ee["target"]
        etype = ee["type"]

        # 确保节点存在，不存在则创建
        for nid in [source, target]:
            if nid not in node_index:
                # 从ID推断类型
                ntype = nid.split(":")[0] if ":" in nid else "unknown"
                label = nid.split(":")[-1] if ":" in nid else nid
                new_node = {
                    "id": nid,
                    "type": ntype,
                    "label": label,
                    "file": "",
                    "description": descriptions.get(nid, ""),
                }
                nodes.append(new_node)
                node_index[nid] = new_node

        edges.append({
            "source": source,
            "target": target,
            "type": etype,
        })

    # ── 3. 删除覆盖的边 ──
    overrides = annotations.get("overrides", {})
    removes = overrides.get("remove", []) or []
    if removes:
        remove_set = set()
        for r in removes:
            if isinstance(r, dict):
                remove_set.add((r["source"], r["target"], r.get("type", "")))
            elif isinstance(r, list) and len(r) >= 3:
                remove_set.add((r[0], r[1], r[2]))

        edges = [
            e for e in edges
            if (e["source"], e["target"], e["type"]) not in remove_set
        ]

    # ── 4. 去重 ──
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # ── 5. 过滤无效边 ──
    valid_edges = [
        e for e in unique_edges
        if e["source"] in node_index and e["target"] in node_index
    ]

    # ── 6. 计算统计 ──
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(valid_edges),
        "node_types": {},
        "edge_types": {},
        "top_connected": [],
    }
    for n in nodes:
        t = n["type"]
        stats["node_types"][t] = stats["node_types"].get(t, 0) + 1
    for e in valid_edges:
        t = e["type"]
        stats["edge_types"][t] = stats["edge_types"].get(t, 0) + 1

    # 计算连接数最多的节点
    degree = {}
    for e in valid_edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1
    top = sorted(degree.items(), key=lambda x: -x[1])[:15]
    stats["top_connected"] = [
        {"id": nid, "label": node_index[nid]["label"], "degree": d}
        for nid, d in top
        if nid in node_index
    ]

    return {
        "nodes": nodes,
        "edges": valid_edges,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "project": "基于多智能体的个性化学习辅助系统",
            "stats": stats,
        },
    }


def main():
    print("=" * 50)
    print("知识图谱合并器")
    print("=" * 50)

    draft = load_draft()
    annotations = load_annotations()

    print(f"自动扫描: {len(draft['nodes'])} 节点, {len(draft['edges'])} 边")
    print(f"手动标注: {len(annotations.get('extra_edges', []))} 额外边")

    graph = merge_graph(draft, annotations)

    output = TOOLS_DIR / "graph-data.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    stats = graph["metadata"]["stats"]
    print(f"\n合并完成!")
    print(f"  最终节点数: {stats['total_nodes']}")
    print(f"  最终边数: {stats['total_edges']}")
    print(f"\n节点类型分布:")
    for t, c in sorted(stats["node_types"].items()):
        print(f"    {t}: {c}")
    print(f"\n边类型分布:")
    for t, c in sorted(stats["edge_types"].items()):
        print(f"    {t}: {c}")
    print(f"\n连接度最高的节点:")
    for item in stats["top_connected"][:10]:
        print(f"    {item['label']}: {item['degree']} 条连接")
    print(f"\n输出文件: {output}")


if __name__ == "__main__":
    main()
