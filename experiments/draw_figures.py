# -*- coding: utf-8 -*-
"""论文插图——Barnett (CAIN 2024) / TextbookQA (Pattern Recognition) 期刊风格

设计系统：
- 处理阶段：米色圆角块（黑字）
- 数据/文本：浅绿圆角块（黑字，可带文档图标）
- 风险/强调：浅粉圆角块（红字）
- 分组：虚线圆角边界 + 斜体标签（Index Process / Query Process 式）
- 黑色细箭头 + 简单图标（文档页/数据库圆柱）+ 图例
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Ellipse, Polygon
import numpy as np
from pathlib import Path

OUT = Path(r"C:\Users\Administrator\Desktop\edu-rag-papers")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ── Barnett 配色 ──────────────────────
P_PROC = ("#FAF3E3", "#2B2B2B")   # 处理阶段 米色
P_DATA = ("#E4F2E0", "#3E6B3E")   # 数据/文本 浅绿
P_FAIL = ("#F9D8D8", "#B44848")   # 风险/强调 浅粉
P_NEUT = ("#F4F4F2", "#555555")   # 中性灰
P_ENC = ("#E8ECEF", "#4A5A6A")    # 编码器 冷灰
RED = "#B44848"
DARK = "#1E1E1E"


def rbox(ax, x, y, w, h, text, fs=8.2, style=P_PROC, bold=False, rot=0):
    fill, edge = style
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.8",
                                linewidth=1.0, edgecolor=edge, facecolor=fill, zorder=2))
    tc = RED if style == P_FAIL else DARK
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=3,
            color=tc, fontweight="bold" if bold else "normal", linespacing=1.45, rotation=rot)


def arrow(ax, x1, y1, x2, y2, lw=1.1):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, linewidth=lw, color=DARK,
                                 shrinkA=1, shrinkB=1, zorder=1))


def group(ax, x, y, w, h, label):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2.5",
                                linewidth=1.0, edgecolor="#666666", facecolor="none",
                                linestyle=(0, (4, 3)), zorder=0))
    ax.text(x + 1.5, y + h - 1.2, label, fontsize=8.5, fontweight="bold",
            fontstyle="italic", color="#333333", ha="left", va="top", zorder=3)


def icon_doc(ax, x, y, s=2.4, color="#C96A6A"):
    """简笔文档页图标"""
    ax.add_patch(Rectangle((x, y), s, s * 1.25, facecolor="white", edgecolor=color,
                           linewidth=0.9, zorder=3))
    for i in range(3):
        ax.plot([x + 0.28 * s, x + 0.72 * s], [y + s * 1.25 - 0.28 * s - i * 0.22 * s] * 2,
                color=color, lw=0.7, zorder=4)


def icon_db(ax, x, y, w=3.2, h=3.6, color="#6B6B6B"):
    """数据库圆柱"""
    ax.add_patch(Ellipse((x + w / 2, y + h * 0.16), w, h * 0.32,
                         facecolor="#E9E9E9", edgecolor=color, lw=0.9, zorder=3))
    ax.add_patch(Rectangle((x, y + h * 0.16), w, h * 0.62,
                           facecolor="#E9E9E9", edgecolor="none", zorder=2))
    ax.add_patch(Rectangle((x, y + h * 0.16), 0.02, h * 0.62, facecolor=color, edgecolor="none", zorder=3))
    ax.add_patch(Rectangle((x + w - 0.02, y + h * 0.16), 0.02, h * 0.62, facecolor=color, edgecolor="none", zorder=3))
    ax.add_patch(Ellipse((x + w / 2, y + h * 0.78), w, h * 0.32,
                         facecolor="#F3F3F3", edgecolor=color, lw=0.9, zorder=3))


def legend_row(ax, x, y, items, fs=7.8):
    """items: [(style, label)]"""
    cx = x
    for style, label in items:
        if style is None:  # arrow legend
            arrow(ax, cx, y + 1.1, cx + 3.2, y + 1.1)
            ax.text(cx + 4, y + 1.1, label, fontsize=fs, va="center", color=DARK)
            cx += 4 + len(label) * 1.55 + 3
        else:
            rbox(ax, cx, y, 3.2, 2.4, "", fs=1, style=style)
            ax.text(cx + 4, y + 1.2, label, fontsize=fs, va="center", color=DARK)
            cx += 4 + len(label) * 1.6 + 3


def new_fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(name, "ok")


# ═══════════ 图1 LEAR 总体结构（Barnett 式双分组图）═══════════
def fig1():
    fig, ax = new_fig(7.8, 5.6)
    # 图例
    legend_row(ax, 8, 96, [(P_PROC, "处理阶段"), (P_DATA, "数据/文本"),
                           (P_FAIL, "风险/降级"), (P_ENC, "编码器"), (None, "数据流")])
    # ── 分组1：离线索引 ──
    group(ax, 1, 76, 97, 17, "Index Process　离线索引（入库时一次）")
    icon_doc(ax, 4, 81)
    ax.text(7, 84.5, "教材/课件\n长文本", fontsize=7.6, ha="left", va="center", zorder=3)
    rbox(ax, 17, 80, 19, 8.5, "M1 教学结构感知分块\n（语义硬边界·退化清理）", fs=7.6)
    rbox(ax, 41, 80, 15, 8.5, "教学语义\n单元块", fs=7.8, style=P_DATA)
    rbox(ax, 61, 80, 16, 8.5, "BGE-M3 编码器\n（冻结·零训练）", fs=7.4, style=P_ENC)
    icon_db(ax, 84, 79.5)
    ax.text(85.6, 88, "单元级\n索引", fontsize=7.2, ha="center", va="top", zorder=3)
    arrow(ax, 13, 84, 17, 84)
    arrow(ax, 36, 84, 41, 84)
    arrow(ax, 56, 84, 61, 84)
    arrow(ax, 77, 84, 83, 84)

    # ── 分组2：在线检索与生成 ──
    group(ax, 1, 34, 97, 38, "Query Process　在线检索、组装与生成门控")
    rbox(ax, 4, 60, 12, 7, "学生查询", fs=7.8, style=P_DATA)
    rbox(ax, 20, 60, 15, 7, "查询意图识别", fs=7.8)
    rbox(ax, 39, 60, 15, 7, "检索（混合）", fs=7.8)
    rbox(ax, 58, 60, 13, 7, "命中单元", fs=7.8, style=P_DATA)
    arrow(ax, 16, 63.5, 20, 63.5)
    arrow(ax, 35, 63.5, 39, 63.5)
    arrow(ax, 54, 63.5, 58, 63.5)
    arrow(ax, 66, 79.5, 64, 67, lw=1.0)   # 索引 → 检索
    rbox(ax, 75, 58, 20, 11, "M2 同节邻域 + M3 依赖回链\n（例题→定理→定义）", fs=7.2)
    arrow(ax, 71, 63.5, 75, 63.5)

    rbox(ax, 4, 42, 16, 8, "教学对齐\n+ 脚手架", fs=7.8)
    rbox(ax, 24, 42, 13, 8, "生成回答", fs=8, bold=True)
    rbox(ax, 41, 40, 22, 11, "F1–F3 符号锚点 ⊕ F4 神经\n忠实度门控", fs=7.4, style=P_FAIL)
    rbox(ax, 68, 40, 27, 11, "ℓ=0 答　ℓ=1 答+〔待核实〕\nℓ=2 教师复核　ℓ=3 拒答降级", fs=7.2, style=P_FAIL)
    arrow(ax, 85, 58, 85, 51)
    arrow(ax, 85, 51, 12, 51, lw=1.0); arrow(ax, 12, 51, 12, 50)
    arrow(ax, 20, 46, 24, 46)
    arrow(ax, 37, 46, 41, 46)
    arrow(ax, 63, 45.5, 68, 45.5)

    # ── 分组3：学习增益评估 ──
    group(ax, 1, 8, 97, 20, "Evaluation　学习增益评估旁路")
    rbox(ax, 6, 13, 22, 8, "BKT 前测—会话—后测", fs=7.8, style=P_DATA)
    rbox(ax, 33, 13, 26, 8, "学习增益 / 纠正率 / 覆盖率", fs=7.8, style=P_DATA)
    rbox(ax, 65, 13, 28, 8, "反事实依赖 · 权威度消解", fs=7.6, style=P_PROC)
    arrow(ax, 28, 17, 33, 17)
    arrow(ax, 59, 17, 65, 17)
    arrow(ax, 50, 42, 45, 21, lw=1.0)
    save(fig, "fig1_lear_framework.png")


# ═══════════ 图2 网络总体结构 ═══════════
def fig2():
    fig, ax = new_fig(7.8, 5.0)
    legend_row(ax, 30, 96, [(P_DATA, "输入/输出"), (P_PROC, "网络层"), (P_FAIL, "分类头")])
    group(ax, 1, 20, 47.5, 72, "T-CNN　教学语义类型分类网络")
    group(ax, 51.5, 20, 47.5, 72, "E-BiLSTM　句级蕴含判定网络（F4）")

    steps = [(80, P_DATA, "句 tokens　(B, L)"),
             (68, P_PROC, "Embedding  128 维"),
             (56, P_PROC, "Conv1d  k = 2/3/4  × 64"),
             (44, P_PROC, "ReLU + MaxPool"),
             (32, P_PROC, "Concat  (B, 192)")]
    for y, s, t in steps:
        rbox(ax, 7, y, 35, 8.5, t, fs=8, style=s)
        arrow(ax, 24.5, y, 24.5, y - 3.5)
    rbox(ax, 7, 14, 35, 10, "FC + Softmax → 6 类\n定义/定理/例题/证明/注意/正文", fs=7.4,
         style=P_FAIL, bold=True)
    arrow(ax, 24.5, 32, 24.5, 24)
    ax.text(24.5, 11.5, "L_kind = CrossEntropy · Adam(1e-3)", fontsize=7.4,
            color="#666", ha="center")

    steps2 = [(80, P_DATA, "claim / evidence  句 tokens"),
              (68, P_PROC, "共享 Embedding  128 维"),
              (56, P_PROC, "BiLSTM  hidden 64×2"),
              (44, P_PROC, "句向量 u, v　→　交互特征\n[u; v; |u−v|; u⊙v]")]
    for y, s, t in steps2:
        rbox(ax, 58, y, 34, 8.5, t, fs=7.8, style=s)
        arrow(ax, 75, y, 75, y - 3.5)
    rbox(ax, 58, 14, 34, 10, "MLP  512 → 64 → 2\nsupported / unsupported", fs=7.8,
         style=P_FAIL, bold=True)
    arrow(ax, 75, 44, 75, 24)
    ax.text(75, 11.5, "L_entail = CrossEntropy · Adam(1e-3)", fontsize=7.4,
            color="#666", ha="center")
    save(fig, "fig2_chunk_assembly.png" if False else "fig_network.png")


# ═══════════ 图3 分块与组装设计 ═══════════
def fig3():
    fig, ax = new_fig(7.8, 5.2)
    group(ax, 1, 30, 47.5, 62, "M1  教学结构感知分块（入库）")
    group(ax, 51.5, 30, 47.5, 62, "M2 / M3  教法序列组装（检索后）")

    icon_doc(ax, 4, 82)
    ax.text(7.5, 85, "教材原文\n（Markdown 章节层级）", fontsize=7.6, va="center", zorder=3)
    rbox(ax, 4, 70, 42, 8, "① 标题层级识别　章 / 节 / 小节", fs=7.8)
    rbox(ax, 4, 58, 42, 8, "② 教学语义硬边界切分　定义|定理|例题|证明|注意", fs=7.2)
    rbox(ax, 4, 46, 42, 8, "③ 退化块清理　分隔线 / 标题残留", fs=7.8)
    arrow(ax, 12, 82, 12, 78)
    arrow(ax, 25, 70, 25, 66)
    arrow(ax, 25, 58, 25, 54)
    rbox(ax, 4, 32, 42, 10,
         "教学语义单元块\nc = (id, order, level, section_path, kind, text, span)", fs=7.6,
         style=P_DATA)
    arrow(ax, 25, 46, 25, 42)

    rbox(ax, 54, 78, 42, 8, "④ 同节邻域窗口　w=1，预算 B=4800", fs=7.8)
    rbox(ax, 54, 66, 42, 8, "⑤ 依赖回链　显式引用（定理N）→ 类型优先级", fs=7.4)
    rbox(ax, 54, 54, 42, 8, "⑥ 脚手架排序 + 关键证据首尾排布", fs=7.8)
    rbox(ax, 54, 42, 42, 8, "排序：定义→定理→例题→证明→易错", fs=7.6)
    for y in (78, 66, 54):
        arrow(ax, 75, y, 75, y - 4)
    rbox(ax, 54, 32, 42, 10,
         "组装上下文\n【章节路径】定义2…｜定理1…｜例题1…（依赖回链补入）", fs=7.6, style=P_DATA)
    arrow(ax, 75, 42, 75, 42)

    # 底部粉色对照提示
    rbox(ax, 1, 10, 97, 12,
         "固定长度切分对照：同一证明被截断为两块、论证链断裂（消融验证）\n"
         "同节约束：跨节噪声为零　｜　依赖回链：例题命中自动补齐所依定理与定义",
         fs=7.8, style=P_FAIL)
    save(fig, "fig2_chunk_assembly.png")


# ═══════════ 图4 门控与分级拒答设计 ═══════════
def fig4():
    fig, ax = new_fig(7.8, 5.2)
    legend_row(ax, 26, 96, [(P_PROC, "核查通道"), (P_FAIL, "风险/降级"), (P_DATA, "输入/输出")])
    rbox(ax, 4, 82, 16, 7, "生成答案", fs=7.8, style=P_DATA)
    rbox(ax, 24, 82, 15, 7, "句级切分 {a_j}", fs=7.8, style=P_PROC)
    rbox(ax, 43, 82, 26, 7, "证据句（source_type / version）", fs=7.6, style=P_DATA)
    arrow(ax, 20, 85.5, 24, 85.5)
    arrow(ax, 39, 85.5, 43, 85.5)

    chans = [(4, "F1 数值归一化\n3/5 ≡ 0.6 ≡ 60%"), (28, "F2 绑定值核对\nP(A)=3/5 vs 5/3"),
             (52, "F3 公式等价\n项多重集/交叉相乘"), (76, "F4 神经蕴含\nE-BiLSTM")]
    for x, t in chans:
        rbox(ax, x, 64, 20, 11, t, fs=7.4, style=P_PROC, bold=True)
        arrow(ax, x + 10, 82, x + 10, 75)
    ax.text(50, 60.5, "＋词面通道（Jaccard / 包含度）", fontsize=7.6, color="#666", ha="center")

    rbox(ax, 4, 44, 45, 10, "证据侧检测\n权威度消解 · 投毒/注入 · 反事实依赖", fs=7.4)
    rbox(ax, 53, 44, 43, 10, "断言三态判定\nsupported / partial / unsupported（0.35）", fs=7.4)
    arrow(ax, 14, 64, 24, 54)
    arrow(ax, 86, 64, 76, 54)

    rbox(ax, 4, 28, 92, 8,
         "综合判定：支撑比例 ρ · 缺失锚点 m · 矛盾信号 → 拒答级别 ℓ", fs=8.2, bold=True)
    arrow(ax, 26, 44, 46, 36)
    arrow(ax, 74, 44, 54, 36)

    lv = [(4, "ℓ = 0\n直接作答", P_DATA), (28, "ℓ = 1\n答 +〔待核实〕", P_DATA),
          (52, "ℓ = 2\n教师复核提示", P_PROC), (76, "ℓ = 3\n拒答降级", P_FAIL)]
    for x, t, s in lv:
        rbox(ax, x, 10, 20, 11, t, fs=7.8, style=s, bold=True)
        arrow(ax, x + 10, 28, x + 10, 21)
    ax.text(50, 5.5, "阈值：句级支撑 0.35 · 教师复核 0.2 · 拒答 0.5（可按覆盖-风险曲线共形标定）",
            fontsize=7.6, color="#666", ha="center")
    save(fig, "fig3_faithfulness_gate.png")


# ═══════════ 图5 评估协议 ═══════════
def fig5():
    fig, ax = new_fig(7.8, 3.8)
    group(ax, 1, 55, 97, 40, "数据构造")
    icon_doc(ax, 4, 70)
    ax.text(7.5, 74, "教材语料\n7 章 · 83 文档", fontsize=7.4, va="center", zorder=3)
    rbox(ax, 22, 66, 20, 11, "金标知识单元抽取\n定义/定理/例题", fs=7.4)
    rbox(ax, 48, 66, 22, 11, "查询构造（金标对齐）\n术语 + 标签模板", fs=7.4)
    rbox(ax, 76, 66, 18, 11, "评测集\nN = 200", fs=7.8, style=P_DATA)
    arrow(ax, 15, 72, 22, 72)
    arrow(ax, 42, 71.5, 48, 71.5)
    arrow(ax, 70, 71.5, 76, 71.5)

    group(ax, 1, 26, 97, 24, "方法对比与消融")
    rbox(ax, 4, 30, 24, 11, "13 种方法同表比较\n经典 + 领先实现 + 本文", fs=7.4)
    rbox(ax, 33, 30, 18, 11, "检索\nBM25 / BGE-M3", fs=7.4)
    rbox(ax, 56, 30, 19, 11, "指标\nHit@k · MRR · nDCG@5", fs=7.2)
    rbox(ax, 80, 30, 15, 11, "模块消融\nM1×M2×M3", fs=7.4)
    arrow(ax, 28, 35.5, 33, 35.5)
    arrow(ax, 51, 35.5, 56, 35.5)
    arrow(ax, 75, 35.5, 80, 35.5)
    arrow(ax, 12, 66, 12, 41)

    group(ax, 1, 2, 97, 19, "忠实度评测")
    rbox(ax, 4, 5, 44, 11, "挑战集 401 例\n正例/数值篡改/绑定值篡改/公式改写/无支撑", fs=7.2, style=P_DATA)
    rbox(ax, 54, 5, 41, 11, "伪忠实检测 P / R / F1\n基线 vs 本文 · 通道消融 2³", fs=7.4, style=P_FAIL)
    arrow(ax, 26, 30, 26, 16)
    arrow(ax, 48, 10.5, 54, 10.5)
    save(fig, "fig2_eval_pipeline.png")


# ═══════════ 图6 检索对比 ═══════════
def fig6(data):
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.2), dpi=220)
    names = list(data.keys())
    short = [n.replace("（vanilla）", "").replace("（本文）", "*").replace("（消融）", "†")
             .replace("(small-to-big)", "").replace("[19]", "").replace("[18]", "")
             .replace("上下文化前缀(Late Chunking近似)", "上下文前缀")
             .replace("小块检索-大块返回", "小块大取") for n in names]
    panels = [("hit@5", "(a) Hit@5 · 全查询"), ("标签型_hit@5", "(b) Hit@5 · 标签型"),
              ("术语型_hit@5", "(c) Hit@5 · 术语型")]
    x = np.arange(len(names))
    for ax, (key, title) in zip(axes, panels):
        vals = [data[n].get(key, 0) for n in names]
        colors = [P_FAIL[0] if "LEAR" in n else "#D8D2C4" for n in names]
        edges = [P_FAIL[1] if "LEAR" in n else "#2B2B2B" for n in names]
        ax.bar(x, vals, 0.62, color=colors, edgecolor=edges, linewidth=0.6)
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.008, f"{v:.2f}", ha="center", fontsize=5.8)
        ax.set_title(title, fontsize=9.5, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(short, rotation=38, ha="right", fontsize=6.4)
        ax.set_ylim(0, 0.52)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linewidth=0.4, color="#DDDDDD")
        ax.set_axisbelow(True)
    axes[0].set_ylabel("得分", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_retrieval_compare.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig3_retrieval_compare.png ok")


# ═══════════ 图7 多视图正交组合与意图路由 ═══════════
def fig_fusion():
    fig, ax = plt.subplots(figsize=(7.6, 3.2), dpi=220)
    rows = [
        ("视图A\n（教学单元）", 0.185, 0.313, 0.125),
        ("视图B\n（正交簇）", 0.195, 0.531, 0.037),
        ("A⊕B\n（RRF融合）", 0.195, 0.453, 0.074),
        ("A＋标记重排\n（标签通道）", 0.195, 0.266, 0.162),
        ("意图路由系统\n（本文完整）", 0.280, 0.531, 0.162),
    ]
    x = np.arange(len(rows))
    w = 0.26
    series = [(0, "全查询 Hit@5"), (1, "术语型 Hit@5"), (2, "标签型 Hit@5")]
    colors = ["#2B2B2B", "#9DB4C8", P_FAIL[0]]
    for (idx, label), col in zip(series, colors):
        vals = [r[1 + idx] for r in rows]
        ax.bar(x + (idx - 1) * w, vals, w, label=label, color=col,
               edgecolor="#2B2B2B", linewidth=0.5)
        for xi, v in zip(x, vals):
            ax.text(xi + (idx - 1) * w, v + 0.008, f"{v:.2f}", ha="center", fontsize=5.6)
    # 最强基线参考线
    ax.axhline(0.18, color="#B44848", linewidth=0.9, linestyle="--")
    ax.text(len(rows) - 0.4, 0.186, "表1最强基线 0.18", fontsize=7, color="#B44848", ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], fontsize=7)
    ax.set_ylabel("Hit@5", fontsize=9)
    ax.set_ylim(0, 0.62)
    ax.legend(fontsize=7.5, frameon=False, ncol=3, loc="upper left")
    ax.set_title("多视图正交组合与意图路由（N=200）", fontsize=9.5, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linewidth=0.4, color="#DDDDDD")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_fusion.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig5_fusion ok")


# ═══════════ 图8 消融 + 忠实度 ═══════════
def fig7(abl, faith=None):
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.3), dpi=220)
    ax = axes[0]
    names = list(abl.keys())
    vals = [abl[n] for n in names]
    short = [n.replace("M1=", "").replace("M2=", "").replace("M3=", "").replace("+", "\n") for n in names]
    colors = [P_FAIL[0] if n == "M1=on+M2=on+M3=on" else "#D8D2C4" for n in names]
    edges = [P_FAIL[1] if n == "M1=on+M2=on+M3=on" else "#2B2B2B" for n in names]
    bars = ax.bar(range(len(names)), vals, 0.62, color=colors, edgecolor=edges, linewidth=0.6)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(short, fontsize=6.0)
    ax.set_ylabel("CtxRecall@5", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.32)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, f"{v:.3f}",
                ha="center", fontsize=6.2)
    ax.set_title("(a) 模块消融 2³（■ = 全开）", fontsize=9.5, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linewidth=0.4, color="#DDDDDD")
    ax.set_axisbelow(True)

    if faith:
        ax = axes[1]
        fkeys = [k for k in ("词面重叠基线", "词面数字锚点基线", "稠密蕴含基线(NLI近似)",
                             "符号锚点（本文全量）") if k in faith]
        labels = ["词面重叠", "词面数字", "稠密蕴含", "符号锚点\n（本文）"]
        prf = [faith[k] for k in fkeys]
        x = np.arange(len(fkeys))
        w = 0.25
        for i, key in enumerate(("P", "R", "F1")):
            ax.bar(x + (i - 1) * w, [p[key] for p in prf], w, label=key,
                   color=["#2B2B2B", "#B8B2A4", P_FAIL[0]][i],
                   edgecolor="#2B2B2B", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels[:len(fkeys)], fontsize=7.2)
        ax.set_ylim(0, 1.18)
        ax.legend(fontsize=7.5, frameon=False, ncol=3, loc="upper right")
        ax.set_title("(b) 伪忠实检测 P / R / F1", fontsize=9.5, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linewidth=0.4, color="#DDDDDD")
        ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_ablation.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig4_ablation.png ok")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    rfile = Path(r"F:\项目\ai教学辅助系统\experiments\eval_results.json")
    if rfile.exists():
        import json
        R = json.loads(rfile.read_text(encoding="utf-8"))
        src = {k.replace(" [Vec]", ""): R[k] for k in R if k.endswith("[Vec]")}
        if src:
            fig6(src)
        abl_final = {
            "M1=off+M2=off+M3=off": 0.085, "M1=off+M2=off+M3=on": 0.100,
            "M1=off+M2=on+M3=off": 0.125, "M1=off+M2=on+M3=on": 0.125,
            "M1=on+M2=off+M3=off": 0.025, "M1=on+M2=off+M3=on": 0.030,
            "M1=on+M2=on+M3=off": 0.075, "M1=on+M2=on+M3=on": 0.100,
        }
        # 新挑战集（语义级公式改写）下的基线与本文数字
        faith_final = {
            "词面重叠基线": {"P": 1.000, "R": 0.244, "F1": 0.392},
            "词面数字锚点基线": {"P": 0.993, "R": 0.838, "F1": 0.909},
            "稠密蕴含基线(NLI近似)": {"P": 1.000, "R": 0.072, "F1": 0.134},
            "符号锚点（本文全量）": {"P": 0.974, "R": 0.947, "F1": 0.960},
        }
        fig7(abl_final, faith_final)
    fig_fusion()
    print("all done")
