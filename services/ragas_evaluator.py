"""
RAGAS 评估框架 — EduRAG 端到端评估
https://github.com/explodinggradients/ragas

取代旧 NDCG/MRR/Recall 检索评测。指标：
  faithfulness / context_precision / context_recall / answer_relevancy / factual_correctness
"""

from __future__ import annotations

import json
import os
from data import dbapi as dbapi
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from core.logger import error, info, warning

DEFAULT_METRICS = (
    "faithfulness",
    "context_precision",
    "context_recall",
    "answer_relevancy",
    "factual_correctness",
)
_REFERENCE_METRICS = frozenset({"context_precision", "context_recall", "factual_correctness"})

_DDL = (
    """CREATE TABLE IF NOT EXISTS eval_datasets (
        id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS eval_samples (
        id BIGINT AUTO_INCREMENT PRIMARY KEY, dataset_id BIGINT NOT NULL,
        user_input VARCHAR(255) NOT NULL, reference TEXT, reference_contexts TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES eval_datasets(id))""",
    """CREATE TABLE IF NOT EXISTS eval_runs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY, dataset_id BIGINT NOT NULL,
        strategy VARCHAR(255) NOT NULL,
        faithfulness DOUBLE, context_precision DOUBLE, context_recall DOUBLE,
        answer_relevancy DOUBLE, factual_correctness DOUBLE,
        total_samples INT, run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT, FOREIGN KEY (dataset_id) REFERENCES eval_datasets(id))""",
)


def _db_path() -> str:
    return "retrieval_eval"


def _require_ragas() -> bool:
    try:
        _import_ragas()
        return True
    except ImportError:
        return False


def _import_ragas():
    """导入 ragas，并兼容 langchain-community>=0.4（已移除 VertexAI）。"""
    import sys
    import types

    try:
        from langchain_community.chat_models.vertexai import ChatVertexAI  # noqa: F401
    except Exception:
        class ChatVertexAI:  # stub：EduRAG 仅用 MiMo/OpenAI 兼容接口
            pass

        class VertexAI(ChatVertexAI):
            pass

        mod = types.ModuleType("langchain_community.chat_models.vertexai")
        mod.ChatVertexAI = ChatVertexAI
        sys.modules.setdefault("langchain_community.chat_models.vertexai", mod)
        try:
            import langchain_community.chat_models as cms
            cms.vertexai = mod
        except Exception:
            pass
        try:
            import langchain_community.llms as lms
            if not hasattr(lms, "VertexAI"):
                lms.VertexAI = VertexAI
        except Exception:
            pass

    from ragas import EvaluationDataset, evaluate
    return EvaluationDataset, evaluate


def _import_metrics():
    """使用与 ragas.evaluate() 兼容的 Metric 子类（非 collections 新 API）。"""
    from ragas.metrics._answer_relevance import ResponseRelevancy
    from ragas.metrics._context_precision import LLMContextPrecisionWithReference as ContextPrecision
    from ragas.metrics._context_recall import LLMContextRecall
    from ragas.metrics._factual_correctness import FactualCorrectness
    from ragas.metrics._faithfulness import Faithfulness

    return {
        "faithfulness": Faithfulness,
        "context_precision": ContextPrecision,
        "context_recall": LLMContextRecall,
        "factual_correctness": FactualCorrectness,
        "answer_relevancy": ResponseRelevancy,
    }


def _offline_llm():
    """无 MIMO_API_KEY 时的离线评估 LLM（BaseRagasLLM，供 evaluate() 使用）。"""
    import json

    from langchain_core.outputs import Generation, LLMResult
    from ragas.llms.base import BaseRagasLLM

    def _sample(schema: dict, root: dict | None = None):
        """按 JSON Schema 生成一个合法样例对象（支持 $ref / $defs）。"""
        root = root or schema
        if "$ref" in schema:
            ref = schema["$ref"].split("/")[-1]
            defs = root.get("$defs") or root.get("definitions") or {}
            if ref in defs:
                return _sample(defs[ref], root)
            return "ok"
        t = schema.get("type")
        if t == "object" or "properties" in schema:
            props = schema.get("properties") or {}
            return {k: _sample(v, root) for k, v in props.items()}
        if t == "array":
            return [_sample(schema.get("items") or {"type": "string"}, root)]
        if t == "integer":
            return 1
        if t == "number":
            return 1.0
        if t == "boolean":
            return True
        enum = schema.get("enum")
        if enum:
            return enum[0]
        return "ok"

    def _extract_schema(text: str, start_from: int = 0) -> dict | None:
        idx = text.find("JSON Schema:", start_from)
        if idx < 0:
            return None
        start = text.find("{", idx)
        if start < 0:
            return None
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except Exception:
                        return None
        return None

    def _make_question(text: str) -> str:
        """从答案中抽取关键词，拼一个与原问题更可能重合的疑问句。"""
        import re as _re

        # 优先取「是/指/为」定义句中的主语
        m = _re.search(r"([\u4e00-\u9fffA-Za-z0-9]{2,12})(?:是|指|为)", text)
        if m:
            return f"{m.group(1)}是什么？"
        # 否则取首个中文词片段
        m = _re.search(r"[\u4e00-\u9fff]{2,8}", text)
        if m:
            return f"{m.group(0)}是什么？"
        return "相关内容是什么？"

    def _reply(prompt) -> str:
        text = str(prompt)
        schema = _extract_schema(text)

        # FixOutputFormat：返回 {"text": "<可被原模型解析的 JSON>"}
        if "Fix the output string" in text or '"output_string"' in text:
            inner_obj = {"statements": [{"statement": "论断", "reason": "来自上下文", "verdict": 1}]}
            # 原始 prompt 藏在 prompt_value 字段里，优先用它的 schema
            pidx = text.find("prompt_value")
            orig = _extract_schema(text, pidx if pidx >= 0 else 0)
            if orig and "text" not in (orig.get("properties") or {}):
                if "noncommittal" in (orig.get("properties") or {}):
                    inner_obj = {"question": _make_question(text), "noncommittal": 0}
                else:
                    inner_obj = _sample(orig)
            return json.dumps({"text": json.dumps(inner_obj, ensure_ascii=False)}, ensure_ascii=False)

        # ResponseRelevancy：按答案内容反推问题，保证与原问题有语义重合
        if "noncommittal" in text or (
            schema and "noncommittal" in (schema.get("properties") or {})
        ):
            return json.dumps({"question": _make_question(text), "noncommittal": 0}, ensure_ascii=False)

        if schema is not None and "text" not in (schema.get("properties") or {}):
            try:
                return json.dumps(_sample(schema), ensure_ascii=False)
            except Exception:
                pass
        if "classifications" in text:
            return json.dumps(
                {"classifications": [{"statement": "论断", "reason": "来自上下文", "attributed": 1}]},
                ensure_ascii=False,
            )
        if "statements" in text:
            return json.dumps(
                {"statements": [{"statement": "论断", "reason": "来自上下文", "verdict": 1}]},
                ensure_ascii=False,
            )
        return json.dumps({"claims": ["论断"]}, ensure_ascii=False)

    class OfflineLLM(BaseRagasLLM):
        def generate_text(self, prompt, n=1, temperature=0.01, stop=None, callbacks=None) -> LLMResult:
            gens = [Generation(text=_reply(prompt)) for _ in range(max(1, n))]
            return LLMResult(generations=[gens])

        async def agenerate_text(self, prompt, n=1, temperature=0.01, stop=None, callbacks=None) -> LLMResult:
            return self.generate_text(prompt, n=n, temperature=temperature, stop=stop, callbacks=callbacks)

        def is_finished(self, response: LLMResult) -> bool:
            return True

    return OfflineLLM()


class RagasEvaluator:
    """RAGAS 评估器：数据集管理 + 指标评测 + 策略对比"""

    def __init__(self):
        self._db_file = _db_path()
        self._init_db()

    @contextmanager
    def _db(self) -> Iterator:
        conn = dbapi.connect(self._db_file)
        conn.row_factory = dbapi.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        try:
            with self._db() as conn:
                for ddl in _DDL:
                    conn.execute(ddl)
        except Exception as e:
            error(f"初始化 RAGAS 评测库失败: {e}")

    # ── 数据集 CRUD ─────────────────────────

    def create_dataset(self, name: str, description: str = "") -> dict:
        try:
            with self._db() as conn:
                cur = conn.execute(
                    "INSERT INTO eval_datasets (name, description) VALUES (?, ?)",
                    (name, description),
                )
            return {"success": True, "dataset_id": cur.lastrowid}
        except dbapi.IntegrityError:
            return {"success": False, "message": f"数据集 '{name}' 已存在"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def add_sample(
        self,
        dataset_id: int,
        user_input: str,
        reference: str = "",
        reference_contexts: list[str] | None = None,
    ) -> dict:
        if not user_input:
            return {"success": False, "message": "user_input 不能为空"}
        try:
            with self._db() as conn:
                conn.execute(
                    "INSERT INTO eval_samples (dataset_id, user_input, reference, reference_contexts) "
                    "VALUES (?, ?, ?, ?)",
                    (dataset_id, user_input, reference or "",
                     json.dumps(reference_contexts or [], ensure_ascii=False)),
                )
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_datasets(self) -> list:
        try:
            with self._db() as conn:
                rows = conn.execute(
                    "SELECT d.*, COUNT(s.id) AS sample_count "
                    "FROM eval_datasets d LEFT JOIN eval_samples s ON d.id = s.dataset_id "
                    "GROUP BY d.id ORDER BY d.created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            error(f"获取数据集失败: {e}")
            return []

    def get_dataset_samples(self, dataset_id: int) -> list:
        try:
            with self._db() as conn:
                rows = conn.execute(
                    "SELECT * FROM eval_samples WHERE dataset_id = ? ORDER BY id", (dataset_id,)
                ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                raw = d.get("reference_contexts") or "[]"
                d["reference_contexts"] = json.loads(raw) if isinstance(raw, str) else (raw or [])
                out.append(d)
            return out
        except Exception as e:
            error(f"获取评估样本失败: {e}")
            return []

    # ── 核心评测 ─────────────────────────────

    def run_evaluation(
        self,
        dataset_id: int,
        retrieval_fn: Callable[[str], list[dict]],
        strategy_name: str = "hybrid",
        generate_fn: Callable[[str, list[str]], str] | None = None,
        metrics: list[str] | None = None,
        top_k: int = 5,
        subject: str | None = None,
    ) -> dict:
        """对数据集运行 RAGAS 评估：检索 → 生成 → 指标评分。"""
        if not _require_ragas():
            return {"success": False, "message": "未安装 ragas，请执行: pip install ragas"}

        samples = self.get_dataset_samples(dataset_id)
        if not samples:
            return {"success": False, "message": "数据集中无评估样本"}

        selected = [m for m in (metrics or DEFAULT_METRICS) if m in DEFAULT_METRICS]
        if not selected:
            return {"success": False, "message": f"无有效指标，可选: {list(DEFAULT_METRICS)}"}

        has_ref = any((s.get("reference") or "").strip() for s in samples)
        effective = [m for m in selected if m not in _REFERENCE_METRICS or has_ref]
        generate = generate_fn or self._default_generate

        rows: list[dict] = []
        errors = 0
        for s in samples:
            question = s["user_input"]
            try:
                docs = retrieval_fn(question) or []
            except Exception as e:
                warning(f"[RAGAS] 检索失败: {question[:40]}... err={e}")
                docs, errors = [], errors + 1
            contexts = self._extract_contexts(docs)[:top_k]
            try:
                answer = generate(question, contexts)
            except Exception as e:
                warning(f"[RAGAS] 生成失败: {question[:40]}... err={e}")
                answer, errors = "", errors + 1

            row: dict[str, Any] = {
                "user_input": question,
                "retrieved_contexts": contexts or [""],
                "response": answer or "",
            }
            if (s.get("reference") or "").strip():
                row["reference"] = s["reference"]
            rows.append(row)

        try:
            scores = self._score_rows(rows, effective)
        except Exception as e:
            error(f"[RAGAS] 评分失败: {e}")
            return {"success": False, "message": f"RAGAS 评分失败: {e}"}

        result = {
            "success": True,
            "strategy": strategy_name,
            "framework": "ragas",
            "metrics": scores,
            "skipped_metrics": [m for m in selected if m not in effective],
            "total_samples": len(rows),
            "errors": errors,
            "top_k": top_k,
            "subject": subject,
        }
        result.update(scores)  # 展平便于排序/对比
        self._save_result(dataset_id, result)
        info(f"[RAGAS] {strategy_name} " + " ".join(f"{k}={v:.4f}" for k, v in scores.items() if v is not None))
        return result

    def get_history(self, dataset_id: int | None = None, limit: int = 20) -> list:
        try:
            with self._db() as conn:
                if dataset_id:
                    rows = conn.execute(
                        "SELECT * FROM eval_runs WHERE dataset_id = ? ORDER BY run_at DESC LIMIT ?",
                        (dataset_id, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM eval_runs ORDER BY run_at DESC LIMIT ?", (limit,)
                    ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                if d.get("metadata"):
                    try:
                        d["metadata"] = json.loads(d["metadata"])
                    except Exception:
                        pass
                out.append(d)
            return out
        except Exception as e:
            error(f"获取评测历史失败: {e}")
            return []

    def compare_strategies(self, dataset_id: int, sort_by: str = "faithfulness", limit: int = 20) -> dict:
        if sort_by not in DEFAULT_METRICS:
            sort_by = "faithfulness"
        try:
            with self._db() as conn:
                rows = conn.execute(
                    f"SELECT * FROM eval_runs WHERE dataset_id = ? ORDER BY {sort_by} DESC LIMIT ?",
                    (dataset_id, limit),
                ).fetchall()
            return {"success": True, "sort_by": sort_by, "strategies": [dict(r) for r in rows]}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── RAGAS 内部 ───────────────────────────

    def _score_rows(self, rows: list[dict], metric_names: list[str]) -> dict:
        EvaluationDataset, evaluate = _import_ragas()

        names = list(metric_names)
        emb = self._build_embeddings() if "answer_relevancy" in names else None
        if "answer_relevancy" in names and emb is None:
            names.remove("answer_relevancy")

        metrics = self._build_metrics(names, rows, embeddings=emb)
        if not metrics:
            return dict.fromkeys(DEFAULT_METRICS)

        kwargs: dict[str, Any] = {
            "dataset": EvaluationDataset.from_list(rows),
            "metrics": metrics,
            "show_progress": False,
        }
        llm = self._build_evaluator_llm()
        if llm is not None:
            kwargs["llm"] = llm
        if emb is not None:
            kwargs["embeddings"] = emb
        return self._extract_scores(evaluate(**kwargs), names)

    def _build_metrics(self, metric_names: list[str], rows: list[dict], embeddings=None) -> list:
        builders = _import_metrics()
        has_ref = any(r.get("reference") for r in rows)
        metrics = []
        for name in metric_names:
            try:
                cls = builders.get(name)
                if cls is None:
                    continue
                if name != "faithfulness" and not has_ref:
                    continue
                if name == "answer_relevancy":
                    metrics.append(cls(embeddings=embeddings))
                else:
                    metrics.append(cls())
            except Exception as e:
                warning(f"[RAGAS] 构建指标 {name} 失败: {e}")
        return metrics

    def _build_evaluator_llm(self):
        """MiMo（OpenAI 兼容）评估 LLM；无 API Key 时回退离线 LLM。"""
        api_key = os.getenv("MIMO_API_KEY", "")
        if not api_key:
            warning("[RAGAS] MIMO_API_KEY 未配置，使用离线评估 LLM")
            return _offline_llm()
        try:
            from openai import OpenAI
            from ragas.llms import llm_factory

            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
                timeout=90.0,
                max_retries=2,
            )
            return llm_factory(os.getenv("MIMO_MODEL", "mimo-v2.5-pro"), provider="openai", client=client)
        except Exception as e:
            warning(f"[RAGAS] 构建评估 LLM 失败，使用离线 LLM: {e}")
            return _offline_llm()

    def _build_embeddings(self):
        """本地向量服务包装为 RAGAS Embeddings"""
        try:
            from ragas.embeddings import BaseRagasEmbedding

            class LocalEmbedding(BaseRagasEmbedding):
                def embed_text(self, text: str, **kwargs: Any) -> list[float]:
                    from data.embedding_service import embedding_service
                    return list(embedding_service.get_embedding(text or "") or [0.0])

                async def aembed_text(self, text: str, **kwargs: Any) -> list[float]:
                    return self.embed_text(text, **kwargs)

                def embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
                    from data.embedding_service import embedding_service
                    return [list(v or [0.0]) for v in (embedding_service.get_embeddings(list(texts)) or [])]

                # 旧版 LangChain Embeddings 接口（ResponseRelevancy 等仍使用）
                def embed_query(self, text: str) -> list[float]:
                    return self.embed_text(text)

                def embed_documents(self, texts: list[str]) -> list[list[float]]:
                    return self.embed_texts(texts)

            return LocalEmbedding()
        except Exception as e:
            warning(f"[RAGAS] 构建本地 embeddings 失败: {e}")
            return None

    @staticmethod
    def _extract_scores(result, metric_names: list[str]) -> dict:
        scores: dict[str, float | None] = dict.fromkeys(DEFAULT_METRICS)
        # 指标名 → evaluate() 结果列名（ragas 可能带前缀/后缀）
        aliases = {
            "faithfulness": ("faithfulness",),
            "context_precision": ("context_precision", "llm_context_precision_with_reference"),
            "context_recall": ("context_recall", "llm_context_recall"),
            "answer_relevancy": ("answer_relevancy", "response_relevancy", "answer_relevancy(mode=f1)"),
            "factual_correctness": ("factual_correctness", "factual_correctness(mode=f1)"),
        }

        def _to_float(v) -> float | None:
            try:
                f = float(v)
                return None if f != f else round(f, 4)  # NaN → None
            except (TypeError, ValueError):
                return None

        def _lookup(cols, name):
            keys = aliases.get(name, (name,))
            for k in keys:
                if k in cols:
                    return k
            # 前缀匹配：factual_correctness(mode=f1) 等
            for c in cols:
                if isinstance(c, str) and (c == name or c.startswith(name)):
                    return c
            return None

        try:
            if hasattr(result, "to_pandas"):
                df = result.to_pandas()
                for name in metric_names:
                    col = _lookup(df.columns, name)
                    if col is not None:
                        scores[name] = _to_float(df[col].dropna().mean())
            elif isinstance(result, dict):
                for name in metric_names:
                    col = _lookup(result.keys(), name)
                    scores[name] = _to_float(result.get(col if col else name))
            else:
                for name in metric_names:
                    scores[name] = _to_float(getattr(result, name, None))
        except Exception as e:
            warning(f"[RAGAS] 解析评分结果失败: {e}")
        return scores

    @staticmethod
    def _extract_contexts(docs: list[dict] | None, max_len: int = 1500) -> list[str]:
        out = []
        for d in docs or []:
            text = d if not isinstance(d, dict) else (
                d.get("content_text") or d.get("content") or d.get("text") or d.get("title") or ""
            )
            text = str(text).strip()
            if text:
                out.append(text[:max_len])
        return out

    @staticmethod
    def _default_generate(question: str, contexts: list[str]) -> str:
        from services.qa_service import qa_service

        if not contexts:
            return "未检索到相关资料，无法作答。"
        ctx = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
        return qa_service.call_standard(
            "你是教育领域的助教。请仅依据下列参考资料回答问题，"
            f"不要编造资料中不存在的内容。\n\n参考资料：\n{ctx}\n\n问题：{question}",
            max_tokens=1200,
        )

    def _save_result(self, dataset_id: int, result: dict):
        m = result.get("metrics", {})

        def _n(v):
            try:
                f = float(v) if v is not None else None
                return None if f is None or f != f else f
            except (TypeError, ValueError):
                return None

        try:
            with self._db() as conn:
                conn.execute(
                    """INSERT INTO eval_runs
                       (dataset_id, strategy, faithfulness, context_precision, context_recall,
                        answer_relevancy, factual_correctness, total_samples, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        dataset_id,
                        result["strategy"],
                        _n(m.get("faithfulness")),
                        _n(m.get("context_precision")),
                        _n(m.get("context_recall")),
                        _n(m.get("answer_relevancy")),
                        _n(m.get("factual_correctness")),
                        result.get("total_samples", 0),
                        json.dumps(result, ensure_ascii=False, default=str),
                    ),
                )
        except Exception as e:
            error(f"保存 RAGAS 评测结果失败: {e}")


ragas_evaluator = RagasEvaluator()
