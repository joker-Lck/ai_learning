# 知识图谱可视化

交互式知识图谱，展示项目的模块依赖、数据流和架构关系。

## 快速开始

```bash
# 1. 提取图谱数据
python tools/knowledge-graph/extract_graph.py

# 2. 合并手动标注
python tools/knowledge-graph/merge_graph.py

# 3. 启动可视化
python -m http.server 8080 -d tools/knowledge-graph
# 浏览器打开 http://localhost:8080/knowledge-graph.html
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `extract_graph.py` | 自动扫描器：正则提取 import/class/route/table |
| `annotations.yaml` | 手动标注：补充自动扫描遗漏的关系和描述 |
| `merge_graph.py` | 合并器：扫描结果 + 标注 → 最终 JSON |
| `knowledge-graph.html` | 可视化网页 (Cytoscape.js) |
| `graph-draft.json` | 自动扫描结果 (中间产物) |
| `graph-data.json` | 最终图谱数据 (可视化用) |

## 图谱规模

- **255 节点**: 6 Agent, 29 Service, 10 Database, 39 Table, 112 Endpoint, 28 Component, 9 Page, 4 Prompt, 8 DataLayer, 2 Infra, 7 Config
- **157 条边**: 12 种关系类型

## 可视化功能

- **搜索**: 按名称/描述/文件路径搜索节点
- **过滤**: 按节点类型和关系类型过滤显示
- **点击详情**: 侧边栏展示节点属性和所有连接
- **布局切换**: 层次/力导向/环形/广度优先
- **高亮**: 点击节点高亮其邻居，双击展开子图
- **导出**: 一键导出 PNG 截图

## 代码变更后重新生成

```bash
python tools/knowledge-graph/extract_graph.py
python tools/knowledge-graph/merge_graph.py
```

## 添加新的关系标注

编辑 `annotations.yaml`，在 `extra_edges` 中添加：

```yaml
extra_edges:
  - source: "service:your_service"
    target: "db:ai_xxx"
    type: "uses_database"
```

然后重新运行 `merge_graph.py`。
