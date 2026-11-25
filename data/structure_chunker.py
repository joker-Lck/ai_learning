"""教学结构感知分块器（structure-aware chunking）

解决教育 RAG 的核心痛点：固定长度分块切断教材章节/知识点/推导链条。

创新点（对应教育 RAG 文献空白）：
1. 结构树切块：解析「章/节/知识点」标题层级，切块携带 section_path（如
   "第3章 概率 › 3.2 条件概率 › 二、全概率公式"），检索结果可回溯教学位置；
2. 教学语义类型标记：定义/定理/例题/证明/公式/练习 不同块型，评估与生成可差异化处理；
3. 结构完整优先：长段落只在段落边界/句读处切，证明与例题整块保留，避免论证链被截断；
4. 为长上下文组装服务：expand_context() 用命中块的父子关系重建连贯上下文窗口。

纯逻辑模块，无 DB/模型依赖，可独立测试。
"""

import hashlib
import re
from dataclasses import dataclass, field, asdict

# ── 标题层级识别（中文教材惯例，兼容 Markdown # 前缀）────────
# L1 章/单元级
_L1_RE = re.compile(
    r"^\s*#{0,4}\s*(第\s*[0-9一二三四五六七八九十百千]+\s*[章单元课讲部分篇模块册辑])\s*[：:．.、\-—\s]*(.{0,40})$"
)
# L2 节级：「3.2 条件概率」「第2节 xxx」；三段编号「### 1.7.1 xxx」按 L3 小节嵌套
_L2_DOT_RE = re.compile(r"^\s*#{0,4}\s*([0-9]{1,2}\.[0-9]{1,2})\s+([^\s].{0,40})$")
_L2_TRI_RE = re.compile(r"^\s*#{0,4}\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2})\s+([^\s].{0,40})$")
_L2_JIE_RE = re.compile(r"^\s*#{0,4}\s*(第\s*[0-9一二三四五六七八九十]+\s*节)\s*[：:．.、\-—\s]*(.{0,40})$")
# L3 小节：「一、全概率公式」「（一）xxx」「1. xxx」（行首、短行）
_L3_RE = re.compile(
    r"^\s*#{0,4}\s*([一二三四五六七八九十]{1,3}、|（[一二三四五六七八九十]{1,3}）|\([一二三四五六七八九十]{1,3}\)|[0-9]{1,2}[.、．]\s)(.{0,40})$"
)

# 教学语义类型标记
_KIND_PATTERNS = [
    ("definition", re.compile(r"(定义|概念|含义)")),
    ("theorem", re.compile(r"(定理|定律|引理|性质|推论|法则|公式)")),
    ("example", re.compile(r"(例题|例\s*\d|示例|实例|案例)")),
    ("proof", re.compile(r"(证明|推导|推证)")),
    ("exercise", re.compile(r"(练习|习题|作业|思考题|巩固)")),
    ("note", re.compile(r"(注意|易错|提示|归纳|小结|总结)")),
]

_HEADING_MAX_LEN = 60


@dataclass
class Chunk:
    """一个教学结构化文本块"""

    chunk_id: str
    order: int
    level: int  # 0=无结构 1=章 2=节 3=小节 4=正文
    section_path: str  # "第3章 概率 › 3.2 条件概率 › 二、全概率公式"
    heading: str  # 本块所属标题（或自身标题行）
    kind: str  # body/definition/theorem/example/proof/exercise/note
    text: str
    char_start: int
    char_end: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChunkTree:
    """整篇文档的切块结果（含结构统计）"""

    chunks: list[Chunk] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)  # 结构大纲 [{level, title, path}]
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "sections": self.sections,
            "stats": self.stats,
        }


class StructureChunker:
    """教学结构感知分块器

    用法:
        tree = StructureChunker().chunk(text, max_length=900)
        for c in tree.chunks:
            ...
    """

    def __init__(
        self,
        max_length: int = 900,
        min_length: int = 60,
        merge_short: bool = True,
        heading_only_lines: bool = True,
    ):
        """
        参数:
            max_length: 正文块最大字符数（只在段落边界切分）
            min_length: 短于此长度的段落并入下一块（避免碎片块）
            merge_short: 是否启用短段合并
            heading_only_lines: 标题行独立成行才识别（避免正文中的序号误判）
        """
        self.max_length = max_length
        self.min_length = min_length
        self.merge_short = merge_short
        self.heading_only_lines = heading_only_lines

    # ── 标题识别 ───────────────────────────────────────────
    def _match_heading(self, line: str) -> tuple[int, str, str] | None:
        """返回 (level, 编号, 标题文字) 或 None"""
        s = line.strip()
        if not s or len(s) > _HEADING_MAX_LEN * 2:
            return None
        # 防止正文误判：标题行不应以句号结尾（"1. 速度是……。"是正文）
        if re.search(r"[。！？；，,!?;]$", s) and not _L1_RE.match(s):
            return None
        m = _L1_RE.match(s)
        if m:
            return (1, m.group(1).strip(), (m.group(2) or "").strip())
        m = _L2_DOT_RE.match(s) or _L2_JIE_RE.match(s)
        if m:
            return (2, m.group(1).strip(), (m.group(2) or "").strip())
        m = _L2_TRI_RE.match(s) or _L3_RE.match(s)
        if m:
            return (3, m.group(1).strip(), (m.group(2) or "").strip())
        return None

    @staticmethod
    def _detect_kind(text: str) -> str:
        # 最早出现的标记决定块型（"例题1…证明…公式"应判为 example 而非 theorem）
        best_kind, best_pos = "body", len(text)
        for kind, pat in _KIND_PATTERNS:
            m = pat.search(text[:200])
            if m and m.start() < best_pos:
                best_kind, best_pos = kind, m.start()
        return best_kind

    # ── 切分主流程 ─────────────────────────────────────────
    def chunk(self, text: str, doc_id: int | str = 0) -> ChunkTree:
        if not text or not text.strip():
            return ChunkTree(stats={"total_chars": 0, "n_chunks": 0, "structure_found": False})

        # 1. 逐行扫描，识别标题层级，构建「段落流 + 标题锚点」
        #    segments: [(level, heading_text, section_path, para_text, abs_start)]
        segments: list[tuple[int, str, str, str, int]] = []
        stack: list[tuple[int, str]] = []  # (level, title) 祖先标题栈
        cur_path_parts: list[str] = []
        sections: list[dict] = []
        buf: list[str] = []
        buf_start = 0
        pos = 0
        structure_found = False

        def flush_buf(end_pos: int):
            nonlocal buf, buf_start
            if not buf:
                return
            para = "\n".join(buf).strip()
            if para:
                path = " › ".join(cur_path_parts) if cur_path_parts else ""
                heading = cur_path_parts[-1] if cur_path_parts else ""
                level = stack[-1][0] if stack else 0
                segments.append((level, heading, path, para, buf_start))
            buf = []
            buf_start = end_pos

        for raw in text.split("\n"):
            line_start = pos
            pos += len(raw) + 1
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped:
                flush_buf(line_start)
                continue

            hit = self._match_heading(stripped) if self.heading_only_lines else None
            if hit and len(stripped) <= _HEADING_MAX_LEN + 20:
                flush_buf(line_start)
                level, num, title = hit
                structure_found = True
                full_title = f"{num} {title}".strip()
                # 维护祖先栈：弹出同级/更深的
                while stack and stack[-1][0] >= level:
                    stack.pop()
                    if cur_path_parts:
                        cur_path_parts.pop()
                stack.append((level, full_title))
                cur_path_parts.append(full_title)
                sections.append(
                    {"level": level, "title": full_title, "path": " › ".join(cur_path_parts)}
                )
                # 标题行本身作为极短段并入后续正文块的 heading，不单独成块
                buf_start = line_start
                buf = []
                continue

            if not buf:
                buf_start = line_start
            buf.append(stripped)

        flush_buf(pos)

        # 2. 短段合并（避免碎片；不跨节合并，防止小节被吞掉）
        if self.merge_short:
            merged: list[tuple[int, str, str, str, int]] = []
            for seg in segments:
                if (merged and len(seg[3]) < self.min_length
                        and seg[2] == merged[-1][2]):  # 同 section_path 才合并
                    lv, hd, pth, tx, st = merged[-1]
                    merged[-1] = (lv, hd, pth, tx + "\n" + seg[3], st)
                else:
                    merged.append(seg)
            segments = merged

        # 3. 正文段落按 max_length 在段落/句读边界切块
        chunks: list[Chunk] = []
        order = 0
        for level, heading, path, para, abs_start in segments:
            for piece_text, rel_start in self._split_para(para):
                kind = self._detect_kind(piece_text)
                cid = self._make_chunk_id(doc_id, order, abs_start + rel_start, piece_text)
                chunks.append(
                    Chunk(
                        chunk_id=cid,
                        order=order,
                        level=level or 4,
                        section_path=path,
                        heading=heading,
                        kind=kind,
                        text=piece_text,
                        char_start=abs_start + rel_start,
                        char_end=abs_start + rel_start + len(piece_text),
                    )
                )
                order += 1

        # 退化块清理：剔除有效内容过短的碎片（分隔线/标题残留等），
        # 同节则并入前块，孤立则丢弃——防止碎片块凭借标题前缀污染检索排序
        cleaned: list[Chunk] = []
        for c in chunks:
            effective = re.sub(r"[-=#*\s_>|]+", "", c.text)
            if len(effective) >= 15:
                cleaned.append(c)
            elif cleaned and cleaned[-1].section_path == c.section_path:
                prev = cleaned[-1]
                if c.text.strip():
                    prev.text = f"{prev.text}\n{c.text}"
                prev.char_end = c.char_end
        chunks = cleaned
        for i, c in enumerate(chunks):
            c.order = i

        return ChunkTree(
            chunks=chunks,
            sections=sections,
            stats={
                "total_chars": len(text),
                "n_chunks": len(chunks),
                "n_sections": len(sections),
                "structure_found": structure_found,
                "max_length": self.max_length,
                "kinds": {k: sum(1 for c in chunks if c.kind == k) for k in
                          ["body", "definition", "theorem", "example", "proof", "exercise", "note"]},
            },
        )

    # ── 内部工具 ───────────────────────────────────────────
    def _split_para(self, para: str) -> list[tuple[str, int]]:
        """段落内切块：先按教学语义硬边界（定义/定理/例题/证明开头）切，
        再按段落边界（\\n）、句读切，绝不硬切断论证内部"""
        out: list[tuple[str, int]] = []
        offset = 0
        # 1) 教学语义硬边界：行首或句首出现 标记 → 新块
        for sub_start, sub in self._split_by_kind(para):
            # 2) 尺寸控制
            for piece_text, rel in self._split_by_size(sub):
                out.append((piece_text, sub_start + rel))
            offset += len(sub)
        return [(t, s) for t, s in out if t]

    @staticmethod
    def _split_by_kind(para: str) -> list[tuple[int, str]]:
        """在教学语义标记处硬切（定义/定理/例题/证明/注意/练习 开头的行或句）"""
        # 行首标记：保留原行起始偏移
        parts: list[tuple[int, str]] = []
        lines = para.split("\n")
        offset = 0
        cur = ""
        cur_start = 0
        marker_re = re.compile(
            r"^\s*\*{0,2}\s*(定义|定理|定律|引理|推论|性质|公式|例题|例\s*[0-9０-９]|证明|推导|注意|练习|习题|小结|归纳)"
            r"[：:．.、\s（(0-9０-９*]"
        )
        for ln in lines:
            if marker_re.match(ln.strip()) and cur.strip():
                parts.append((cur_start, cur))
                cur = ln
                cur_start = offset
            else:
                if not cur:
                    cur_start = offset
                cur = (cur + "\n" + ln) if cur else ln
            offset += len(ln) + 1
        if cur.strip():
            parts.append((cur_start, cur))
        return parts

    def _split_by_size(self, para: str) -> list[tuple[str, int]]:
        if len(para) <= self.max_length:
            return [(para, 0)] if para.strip() else []

        pieces: list[tuple[str, int]] = []
        # 先按段内换行切
        subs = para.split("\n")
        offset = 0
        cur = ""
        cur_start = 0
        for sub in subs:
            cand = (cur + "\n" + sub) if cur else sub
            if len(cand) <= self.max_length:
                if not cur:
                    cur_start = offset
                cur = cand
            else:
                if cur:
                    pieces.append((cur.strip(), cur_start))
                # 单行仍超长 → 句读切
                if len(sub) > self.max_length:
                    for t, st in self._split_by_punct(sub, offset):
                        pieces.append((t, st))
                    cur = ""
                else:
                    cur_start = offset
                    cur = sub
            offset += len(sub) + 1
        if cur:
            pieces.append((cur.strip(), cur_start))
        return [(t, s) for t, s in pieces if t]

    def _split_by_punct(self, text: str, base: int) -> list[tuple[str, int]]:
        """按中文句读切超长行，保持论证句完整"""
        seps = "。！？；!?;"
        pieces = []
        cur = ""
        cur_start = 0
        i = 0
        while i < len(text):
            cur += text[i]
            if text[i] in seps:
                if len(cur) >= self.max_length or i == len(text) - 1:
                    pieces.append((cur.strip(), base + cur_start))
                    cur = ""
                    cur_start = i + 1
            i += 1
        if cur.strip():
            pieces.append((cur.strip(), base + cur_start))
        return pieces

    @staticmethod
    def _make_chunk_id(doc_id, order, offset, text) -> str:
        h = hashlib.md5(f"{doc_id}:{order}:{offset}:{text[:32]}".encode("utf-8")).hexdigest()[:12]
        return f"c{h}"


def build_clusters(chunks: list, max_cluster: int = 900) -> list[dict]:
    """教学语义簇：同节相邻教学块按依赖链（定义→定理→例题→证明）聚合为检索单元。

    长文本学习资源的主检索单元：簇内语义完整、簇间以教学/章节边界相隔，
    既保留单元完整性又解决单元过小导致的术语共现不足。
    返回 [{text, kind, section_path, char_start, char_end, order,
          member_chunk_ids, is_cluster: True}]
    """
    clusters: list[dict] = []
    cur: list = []
    total = 0

    def flush():
        nonlocal cur, total
        if not cur:
            return
        raw = "\n".join(c.text for c in cur)
        kinds = [c.kind for c in cur]
        primary = ("definition" if "definition" in kinds else
                   "theorem" if "theorem" in kinds else
                   "example" if "example" in kinds else kinds[0])
        clusters.append({
            "text": raw,
            "kind": primary,
            "section_path": cur[0].section_path,
            "char_start": cur[0].char_start,
            "char_end": cur[-1].char_end,
            "order": cur[0].order,
            "member_chunk_ids": [c.chunk_id for c in cur],
            "is_cluster": True,
        })
        cur, total = [], 0

    for c in chunks:
        if cur and (c.section_path != cur[-1].section_path
                    or total + len(c.text) > max_cluster):
            flush()
        cur.append(c)
        total += len(c.text)
    flush()
    return clusters


# ── 长上下文组装（检索后扩展）────────────────────────────────
def expand_context(
    hit_chunks: list[dict],
    all_chunks: list[dict],
    max_chars: int = 4800,
    neighbor_window: int = 1,
) -> list[dict]:
    """把命中块扩展为连贯上下文窗口（长上下文组装）

    参数:
        hit_chunks:   检索命中的块（dict，含 chunk_id/order/doc_id/section_path）
        all_chunks:   同文档全量块（用于取邻接块）
        max_chars:    组装预算（BGE-M3 8192 token 窗口内保守取 ~4800 字符）
        neighbor_window: 命中块前后各取几个邻接块

    返回:
        组装后的上下文块列表：每项 {
            "context_text": 带小节标题的连贯文本,
            "section_path", "chunk_ids": 参与组装的块, "score": 命中块最高分
        }
    """
    if not hit_chunks:
        return []

    # 按文档分组，命中块按 order 聚簇（相邻命中共用窗口）
    by_doc: dict = {}
    for h in hit_chunks:
        by_doc.setdefault(h.get("doc_id"), []).append(h)

    doc_pool: dict = {}
    for c in all_chunks:
        doc_pool.setdefault(c.get("doc_id"), []).append(c)

    contexts = []
    for doc_id, hits in by_doc.items():
        pool = sorted(doc_pool.get(doc_id, []), key=lambda x: x.get("order", 0))
        if not pool:
            # 无全量块时直接用命中文本
            for h in hits:
                contexts.append(
                    {
                        "context_text": f"【{h.get('section_path') or h.get('heading') or ''}】\n{h.get('text', '')}",
                        "section_path": h.get("section_path", ""),
                        "chunk_ids": [h.get("chunk_id")],
                        "score": h.get("similarity", h.get("score", 0)),
                        "doc_id": doc_id,
                        "title": h.get("title", ""),
                    }
                )
            continue

        order_index = {c.get("order"): c for c in pool}
        hits_sorted = sorted(hits, key=lambda x: x.get("order", 0))
        used_orders: set = set()
        for h in hits_sorted:
            center = h.get("order", 0)
            if center in used_orders:
                continue
            hit_path = h.get("section_path", "")
            # 收集邻域 [center-w, center+w]，同小节优先（不跨节拼接上下文）
            members = []
            for o in range(center - neighbor_window, center + neighbor_window + 1):
                c = order_index.get(o)
                if c is None:
                    continue
                if o != center and hit_path and c.get("section_path", "") != hit_path:
                    continue
                members.append(c)
                used_orders.add(o)
            members.sort(key=lambda x: x.get("order", 0))

            # 组装：命中块优先、两侧交替取块、按预算截断；输出按阅读序
            center_idx = next((i for i, c in enumerate(members) if c.get("order") == center), 0)
            picked = []
            total = 0
            for delta in range(len(members)):
                for idx in ([center_idx + delta, center_idx - delta] if delta else [center_idx]):
                    if not 0 <= idx < len(members):
                        continue
                    c = members[idx]
                    if any(p is c for p in picked):
                        continue
                    seg = c.get("text", "")
                    if total + len(seg) > max_chars and picked:
                        continue
                    picked.append(c)
                    total += len(seg)
            picked.sort(key=lambda x: x.get("order", 0))
            parts = [c.get("text", "") for c in picked]
            used_ids = [c.get("chunk_id") for c in picked]
            path = h.get("section_path") or members[0].get("section_path", "")
            context_text = f"【{path}】\n" + "\n".join(parts) if path else "\n".join(parts)
            contexts.append(
                {
                    "context_text": context_text,
                    "section_path": path,
                    "chunk_ids": used_ids,
                    "score": h.get("similarity", h.get("score", 0)),
                    "doc_id": doc_id,
                    "title": h.get("title", ""),
                    "expanded": len(used_ids) > 1,
                }
            )

    contexts.sort(key=lambda x: x.get("score", 0), reverse=True)
    return contexts
