"""
知识图谱自动提取器
扫描项目源码，通过正则表达式提取模块依赖关系，生成 graph-draft.json
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── 数据库定义 ──
DATABASES = {
    "ai_auth": {"file": "ai_auth.db", "desc": "认证与用户管理"},
    "ai_profiles": {"file": "ai_profiles.db", "desc": "学生画像、成绩、错题、课表"},
    "ai_resources": {"file": "ai_resources.db", "desc": "学习资源与安全日志"},
    "ai_paths": {"file": "ai_paths.db", "desc": "学习路径与进度"},
    "ai_tutor": {"file": "ai_tutor.db", "desc": "辅导会话与知识引用"},
    "ai_assessments": {"file": "ai_assessments.db", "desc": "评估、活动、测验、题库"},
    "ai_agents": {"file": "ai_agents.db", "desc": "智能体协作日志与任务"},
    "ai_rag_knowledge": {"file": "ai_rag_knowledge.db", "desc": "RAG知识库、FTS5索引、实体图谱"},
    "ai_memory": {"file": "ai_memory.db", "desc": "四层记忆系统(短期/情景/语义/实体)"},
    "retrieval_eval": {"file": "retrieval_eval.db", "desc": "检索效果评估"},
}

# DB名到config函数的映射
DB_CONFIG_MAP = {
    "auth": "ai_auth",
    "profile": "ai_profiles",
    "resources": "ai_resources",
    "paths": "ai_paths",
    "tutor": "ai_tutor",
    "assessments": "ai_assessments",
    "agents": "ai_agents",
    "rag": "ai_rag_knowledge",
    "memory": "ai_memory",
    "rag_knowledge": "ai_rag_knowledge",
    "accounts": "ai_auth",
    "qa": "ai_tutor",
}


def scan_python_imports(filepath: str) -> list[dict]:
    """扫描Python文件的import语句，提取依赖关系"""
    edges = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return edges

    rel_path = os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/")

    # from services.xxx import yyy
    for m in re.finditer(
        r"from\s+(services|data|core|backend)\.([\w.]+)\s+import\s+([\w,\s]+)",
        content,
    ):
        pkg = m.group(1)
        mod_parts = m.group(2).split(".")
        mod = mod_parts[0]
        imports = [x.strip() for x in m.group(3).split(",")]

        source_file = rel_path
        target_mod = f"{pkg}/{mod}"

        for imp in imports:
            if imp:
                edges.append({
                    "source_file": source_file,
                    "target_module": target_mod,
                    "target_class": imp,
                    "import_type": pkg,
                })

    return edges


def detect_db_usage(filepath: str) -> list[str]:
    """检测文件中使用的数据库"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    dbs = set()
    # get_xxx_db_path() or get_xxx_db_config()
    for m in re.finditer(r"get_(\w+)_db_(?:path|config)\(\)", content):
        key = m.group(1)
        if key in DB_CONFIG_MAP:
            dbs.add(DB_CONFIG_MAP[key])

    # 直接引用 db_operations 中的实例
    for m in re.finditer(r"(profile_db|resource_db|assessment_db|path_db|tutor_db|agent_db|db)\b", content):
        inst = m.group(1)
        inst_map = {
            "profile_db": "ai_profiles",
            "resource_db": "ai_resources",
            "assessment_db": "ai_assessments",
            "path_db": "ai_paths",
            "tutor_db": "ai_tutor",
            "agent_db": "ai_agents",
        }
        if inst in inst_map:
            dbs.add(inst_map[inst])

    return list(dbs)


def detect_message_bus(filepath: str) -> bool:
    """检测是否使用消息总线"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False
    return bool(re.search(r"message_bus|MessageBus|self\.bus", content))


def detect_prompt_usage(filepath: str) -> list[str]:
    """检测使用的Prompt模板"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    prompts = []
    for m in re.finditer(r"(ProfilePrompts|AnalysisPrompts|DocumentAnalysisPrompts|VoiceQAPrompts)", content):
        prompts.append(m.group(1))
    return list(set(prompts))


def scan_api_routes(filepath: str) -> list[dict]:
    """扫描FastAPI路由定义"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    routes = []
    rel_path = os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/")

    for m in re.finditer(
        r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
        content,
    ):
        method = m.group(1).upper()
        path = m.group(2)
        routes.append({
            "method": method,
            "path": path,
            "file": rel_path,
        })

    return routes


def scan_create_tables(filepath: str) -> list[dict]:
    """扫描CREATE TABLE语句"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    tables = []
    for m in re.finditer(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\(",
        content,
        re.IGNORECASE,
    ):
        table_name = m.group(1)
        # 跳过FTS虚拟表和触发器
        if "_fts" in table_name:
            continue
        tables.append(table_name)

    return tables


def determine_db_for_table(init_func_name: str, filepath: str) -> str:
    """根据初始化函数名判断表属于哪个数据库"""
    func_to_db = {
        "init_auth": "ai_auth",
        "init_profile": "ai_profiles",
        "init_resources": "ai_resources",
        "init_paths": "ai_paths",
        "init_tutor": "ai_tutor",
        "init_assessments": "ai_assessments",
        "init_agents": "ai_agents",
        "init_rag": "ai_rag_knowledge",
        "init_memory": "ai_memory",
    }
    for prefix, db in func_to_db.items():
        if prefix in init_func_name:
            return db
    return "unknown"


def extract_tables_from_init_scripts() -> dict[str, list[str]]:
    """从初始化脚本中提取所有表"""
    db_tables: dict[str, list[str]] = {}

    init_files = [
        PROJECT_ROOT / "scripts" / "init_databases.py",
        PROJECT_ROOT / "scripts" / "init_rag_db.py",
        PROJECT_ROOT / "scripts" / "init_memory_db.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            continue
        try:
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # 按函数分段
        func_pattern = r"def\s+(init_\w+)\s*\("
        func_starts = [(m.start(), m.group(1)) for m in re.finditer(func_pattern, content)]

        for i, (start, func_name) in enumerate(func_starts):
            end = func_starts[i + 1][0] if i + 1 < len(func_starts) else len(content)
            func_body = content[start:end]
            db = determine_db_for_table(func_name, str(init_file))

            for tm in re.finditer(
                r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\(",
                func_body,
                re.IGNORECASE,
            ):
                table = tm.group(1)
                if "_fts" not in table:
                    db_tables.setdefault(db, [])
                    if table not in db_tables[db]:
                        db_tables[db].append(table)

    return db_tables


def scan_ts_fetch_calls(filepath: str) -> list[dict]:
    """扫描TypeScript中的fetch调用"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    calls = []
    rel_path = os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/")

    # fetch(`/api/...`) or fetch('/api/...')
    for m in re.finditer(r'fetch\([`\'"](/api/[^`\'"]+)[`\'"]', content):
        endpoint = m.group(1)
        calls.append({"file": rel_path, "endpoint": endpoint})

    # `${API_BASE}/xxx` patterns
    for m in re.finditer(r'[`\'"]\$\{API_BASE\}(/[^`\'"]+)[`\'"]', content):
        endpoint = "/api" + m.group(1)
        calls.append({"file": rel_path, "endpoint": endpoint})

    return calls


def scan_tsx_components(directory: str) -> list[dict]:
    """扫描前端组件"""
    components = []
    comp_dir = PROJECT_ROOT / directory
    if not comp_dir.exists():
        return components

    for fpath in sorted(comp_dir.rglob("*.tsx")) + sorted(comp_dir.rglob("*.ts")):
        if fpath.suffix == ".d.ts":
            continue
        rel_path = fpath.relative_to(PROJECT_ROOT).as_posix()
        f = fpath.name

        # 判断类型
        if f in ("page.tsx", "layout.tsx") and "/app/" in rel_path:
            # 从路径提取页面名: frontend/app/dashboard/page.tsx -> dashboard
            parts = rel_path.split("/")
            app_idx = parts.index("app") if "app" in parts else -1
            if app_idx >= 0 and app_idx + 1 < len(parts) - 1:
                name = parts[app_idx + 1]  # dashboard, profile, etc.
            else:
                name = f.replace(".tsx", "").replace(".ts", "")
            comp_type = "page"
        elif "/components/" in rel_path:
            name = f.replace(".tsx", "").replace(".ts", "")
            comp_type = "component"
        else:
            name = f.replace(".tsx", "").replace(".ts", "")
            comp_type = "module"

        components.append({
            "name": name,
            "file": rel_path,
            "type": comp_type,
        })

    return components


def classify_service(filepath: str) -> str:
    """分类服务文件"""
    name = os.path.basename(filepath).replace(".py", "")
    agent_names = {
        "agent_coordinator", "profile_agent", "resource_agent",
        "path_agent", "tutor_agent", "assessment_agent",
    }
    if name in agent_names:
        return "agent"
    if "service" in name or "client" in name:
        return "service"
    if name in ("agent_message", "message_bus"):
        return "infra"
    return "util"


def extract_all() -> dict:
    """主提取函数"""
    nodes = []
    edges = []
    node_ids = set()

    # ── 1. 数据库节点 ──
    for db_name, info in DATABASES.items():
        nid = f"db:{db_name}"
        nodes.append({
            "id": nid,
            "type": "database",
            "label": db_name,
            "file": f"data/databases/{info['file']}",
            "description": info["desc"],
        })
        node_ids.add(nid)

    # ── 2. 表节点 ──
    db_tables = extract_tables_from_init_scripts()
    for db_name, tables in db_tables.items():
        for table in tables:
            nid = f"table:{db_name}.{table}"
            nodes.append({
                "id": nid,
                "type": "table",
                "label": table,
                "file": f"scripts/init_databases.py",
                "description": f"{db_name}.{table}",
                "database": db_name,
            })
            node_ids.add(nid)
            # contains_table edge
            edges.append({
                "source": f"db:{db_name}",
                "target": nid,
                "type": "contains_table",
            })

    # ── 3. 服务/Agent节点 ──
    services_dir = PROJECT_ROOT / "services"
    if services_dir.exists():
        for f in sorted(services_dir.glob("*.py")):
            if f.name == "__init__.py":
                continue
            rel_path = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            name = f.stem
            category = classify_service(str(f))

            # 读取文件内容获取描述
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    first_lines = fp.read(500)
                doc_match = re.search(r'"""(.+?)"""', first_lines, re.DOTALL)
                desc = doc_match.group(1).strip().split("\n")[0][:80] if doc_match else ""
            except Exception:
                desc = ""

            if category == "agent":
                nid = f"agent:{name}"
                ntype = "agent"
            elif category == "infra":
                nid = f"infra:{name}"
                ntype = "infra"
            else:
                nid = f"service:{name}"
                ntype = "service"

            nodes.append({
                "id": nid,
                "type": ntype,
                "label": name,
                "file": rel_path,
                "description": desc,
            })
            node_ids.add(nid)

            # 扫描依赖
            imports = scan_python_imports(str(f))
            for imp in imports:
                target_mod = imp["target_module"].split("/")[-1]
                # 找到对应的节点
                for prefix in ["agent:", "service:", "infra:", "data:"]:
                    candidate = f"{prefix}{target_mod}"
                    if candidate in node_ids:
                        edges.append({
                            "source": nid,
                            "target": candidate,
                            "type": "imports",
                        })
                        break

            # 数据库使用
            dbs = detect_db_usage(str(f))
            for db in dbs:
                edges.append({
                    "source": nid,
                    "target": f"db:{db}",
                    "type": "uses_database",
                })

            # 消息总线
            if detect_message_bus(str(f)):
                edges.append({
                    "source": nid,
                    "target": "infra:message_bus",
                    "type": "communicates_via",
                })

            # Prompt使用
            prompts = detect_prompt_usage(str(f))
            for p in prompts:
                edges.append({
                    "source": nid,
                    "target": f"prompt:{p}",
                    "type": "uses_prompt",
                })

    # ── 4. 数据层节点 ──
    data_dir = PROJECT_ROOT / "data"
    if data_dir.exists():
        for f in sorted(data_dir.glob("*.py")):
            if f.name == "__init__.py":
                continue
            rel_path = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            name = f.stem

            try:
                with open(f, "r", encoding="utf-8") as fp:
                    first_lines = fp.read(500)
                doc_match = re.search(r'"""(.+?)"""', first_lines, re.DOTALL)
                desc = doc_match.group(1).strip().split("\n")[0][:80] if doc_match else ""
            except Exception:
                desc = ""

            nid = f"data:{name}"
            nodes.append({
                "id": nid,
                "type": "data_layer",
                "label": name,
                "file": rel_path,
                "description": desc,
            })
            node_ids.add(nid)

            dbs = detect_db_usage(str(f))
            for db in dbs:
                edges.append({
                    "source": nid,
                    "target": f"db:{db}",
                    "type": "uses_database",
                })

    # ── 5. API端点节点 ──
    api_dir = PROJECT_ROOT / "backend" / "api"
    if api_dir.exists():
        for f in sorted(api_dir.glob("*.py")):
            if f.name == "__init__.py":
                continue
            routes = scan_api_routes(str(f))
            for route in routes:
                nid = f"endpoint:{route['method']}{route['path']}"
                nodes.append({
                    "id": nid,
                    "type": "endpoint",
                    "label": f"{route['method']} {route['path']}",
                    "file": route["file"],
                    "method": route["method"],
                    "path": route["path"],
                })
                node_ids.add(nid)

    # ── 6. Prompt模板节点 ──
    prompts_file = PROJECT_ROOT / "core" / "prompts.py"
    if prompts_file.exists():
        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                content = f.read()
            for m in re.finditer(r"class\s+(\w+Prompts)\w*:", content):
                nid = f"prompt:{m.group(1)}"
                nodes.append({
                    "id": nid,
                    "type": "prompt",
                    "label": m.group(1),
                    "file": "core/prompts.py",
                    "description": "",
                })
                node_ids.add(nid)
        except Exception:
            pass

    # ── 7. 前端组件节点 ──
    for comp_dir in ["frontend/app", "frontend/components"]:
        comps = scan_tsx_components(comp_dir)
        for comp in comps:
            nid = f"{'page' if comp['type'] == 'page' else 'component'}:{comp['name']}"
            if nid not in node_ids:
                nodes.append({
                    "id": nid,
                    "type": comp["type"],
                    "label": comp["name"],
                    "file": comp["file"],
                })
                node_ids.add(nid)

    # ── 8. 前端→API端点连接 ──
    api_ts = PROJECT_ROOT / "frontend" / "lib" / "api.ts"
    if api_ts.exists():
        calls = scan_ts_fetch_calls(str(api_ts))
        for call in calls:
            # 尝试匹配到已知端点
            for node in nodes:
                if node["type"] == "endpoint":
                    ep_path = node.get("path", "")
                    # 简单匹配
                    call_ep = call["endpoint"].rstrip("/")
                    ep_clean = ep_path.rstrip("/")
                    if call_ep == ep_clean or call_ep.startswith(ep_clean + "/"):
                        # 找到前端发起者
                        source_nid = f"component:ApiClient"
                        if source_nid not in node_ids:
                            nodes.append({
                                "id": source_nid,
                                "type": "component",
                                "label": "ApiClient",
                                "file": "frontend/lib/api.ts",
                                "description": "前端API客户端(重试+超时+认证)",
                            })
                            node_ids.add(source_nid)
                        edges.append({
                            "source": source_nid,
                            "target": node["id"],
                            "type": "calls_endpoint",
                        })
                        break

    # ── 9. 配置文件节点 ──
    config_files = [
        (".env", "env", "环境变量配置"),
        ("pyproject.toml", "toml", "Python项目配置"),
        ("config/sensitive_words.json", "json", "敏感词库(127条)"),
        ("docker-compose.yml", "yaml", "Docker服务编排"),
        ("Dockerfile", "docker", "后端Docker镜像"),
        ("frontend/package.json", "json", "前端依赖配置"),
        ("frontend/tailwind.config.ts", "ts", "Tailwind CSS配置"),
    ]
    for cf_path, cf_type, cf_desc in config_files:
        if (PROJECT_ROOT / cf_path).exists():
            nid = f"config:{os.path.basename(cf_path)}"
            nodes.append({
                "id": nid,
                "type": "config",
                "label": os.path.basename(cf_path),
                "file": cf_path,
                "description": cf_desc,
                "config_type": cf_type,
            })
            node_ids.add(nid)

    # ── 去重边 ──
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    # ── 过滤不存在的节点引用 ──
    valid_edges = [e for e in unique_edges if e["source"] in node_ids and e["target"] in node_ids]

    return {
        "nodes": nodes,
        "edges": valid_edges,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "project_root": str(PROJECT_ROOT),
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(valid_edges),
                "node_types": {},
                "edge_types": {},
            },
        },
    }


def compute_stats(graph: dict):
    """计算统计信息"""
    stats = graph["metadata"]["stats"]
    for n in graph["nodes"]:
        t = n["type"]
        stats["node_types"][t] = stats["node_types"].get(t, 0) + 1
    for e in graph["edges"]:
        t = e["type"]
        stats["edge_types"][t] = stats["edge_types"].get(t, 0) + 1


def main():
    print("=" * 50)
    print("知识图谱自动提取器")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")

    graph = extract_all()
    compute_stats(graph)

    output = PROJECT_ROOT / "tools" / "knowledge-graph" / "graph-draft.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"\n提取完成!")
    print(f"  节点数: {graph['metadata']['stats']['total_nodes']}")
    print(f"  边数: {graph['metadata']['stats']['total_edges']}")
    print(f"\n节点类型分布:")
    for t, c in sorted(graph["metadata"]["stats"]["node_types"].items()):
        print(f"    {t}: {c}")
    print(f"\n边类型分布:")
    for t, c in sorted(graph["metadata"]["stats"]["edge_types"].items()):
        print(f"    {t}: {c}")
    print(f"\n输出文件: {output}")


if __name__ == "__main__":
    main()
