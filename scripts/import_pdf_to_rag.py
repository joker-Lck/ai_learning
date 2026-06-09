"""
PDF 导入 RAG 知识库脚本
读取 PDF → 提取文本 → AI 结构化 → 写入 knowledge_documents 表
"""

import os
import io
import sys
import json

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

from core.logger import info, error


def parse_pdf(filepath: str) -> str:
    """提取 PDF 全文"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("❌ 缺少 PyPDF2，正在安装...")
        os.system(f'"{sys.executable}" -m pip install PyPDF2 -q')
        from PyPDF2 import PdfReader

    reader = PdfReader(filepath)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[第{i+1}页]\n{text.strip()}")
    return "\n\n".join(pages)


def ai_structure(raw_text: str, filename: str) -> dict:
    """用 AI 将原始文本结构化为 JSON"""
    from services.qa_service import qa_service
    from core.json_utils import safe_parse_json

    # 截取前 8000 字（避免超 token）
    text = raw_text[:8000]

    prompt = f"""你是一位教育知识工程师。请将以下教材内容结构化为 JSON，便于知识库检索。

文件名: {filename}

教材内容:
{text}

请输出以下 JSON 格式（只输出 JSON，不要其他文字）:

{{
    "title": "文档标题（从内容推断）",
    "subject": "学科（如 机器学习、数学、物理 等）",
    "summary": "200字以内的内容摘要",
    "knowledge_points": [
        "知识点1",
        "知识点2",
        "知识点3"
    ],
    "key_concepts": [
        {{
            "name": "概念名称",
            "definition": "一句话定义",
            "importance": "核心/重要/了解"
        }}
    ],
    "difficulty_level": "入门/中级/高级",
    "tags": ["标签1", "标签2"]
}}"""

    try:
        response = qa_service.call_ai(prompt, max_tokens=2500)
        result = safe_parse_json(response)
        if result:
            return result
    except Exception as e:
        print(f"⚠️ AI 结构化失败: {e}")

    # 降级：用文件名作为标题
    return {
        "title": filename.rsplit(".", 1)[0],
        "subject": "综合",
        "summary": text[:200],
        "knowledge_points": [],
        "key_concepts": [],
        "difficulty_level": "中级",
        "tags": [],
    }


def save_to_rag(title: str, subject: str, content_text: str,
                knowledge_points: list, ai_summary: str,
                file_path: str, full_json: dict) -> int | None:
    """写入 RAG knowledge_documents 表"""
    from data.rag_knowledge_base import rag_kb

    doc_id = rag_kb.add_document(
        title=title,
        subject=subject,
        file_path=file_path,
        file_type="pdf",
        content_text=content_text,
        knowledge_points=knowledge_points,
        ai_summary=ai_summary,
        uploaded_by="pdf_import",
        file_size=os.path.getsize(file_path),
    )
    return doc_id


def main():
    # ── 配置 ──
    pdf_path = os.path.join(ROOT, "resources", "13974463_机器学习.pdf")

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return

    print(f"📄 正在解析 PDF: {os.path.basename(pdf_path)}")

    # Step 1: 提取文本
    raw_text = parse_pdf(pdf_path)
    print(f"   提取文本: {len(raw_text)} 字符, {raw_text.count('[第')} 页")

    if len(raw_text) < 50:
        print("⚠️ 提取内容过少，可能是扫描版 PDF，需要 OCR")
        return

    # Step 2: AI 结构化
    print("🤖 AI 正在结构化内容...")
    structured = ai_structure(raw_text, os.path.basename(pdf_path))

    title = structured.get("title", "机器学习")
    subject = structured.get("subject", "机器学习")
    summary = structured.get("summary", "")
    knowledge_points = structured.get("knowledge_points", [])
    key_concepts = structured.get("key_concepts", [])
    difficulty = structured.get("difficulty_level", "中级")
    tags = structured.get("tags", [])

    print(f"   标题: {title}")
    print(f"   学科: {subject}")
    print(f"   知识点: {len(knowledge_points)} 个")
    print(f"   核心概念: {len(key_concepts)} 个")
    print(f"   难度: {difficulty}")

    # Step 3: 写入 RAG
    print("💾 写入 RAG 数据库...")
    doc_id = save_to_rag(
        title=title,
        subject=subject,
        content_text=raw_text,
        knowledge_points=knowledge_points,
        ai_summary=summary,
        file_path=pdf_path,
        full_json=structured,
    )

    if doc_id:
        print(f"\n✅ 成功写入 RAG 知识库！")
        print(f"   doc_id = {doc_id}")
        print(f"   标题 = {title}")
        print(f"   知识点数 = {len(knowledge_points)}")
        print(f"\n📋 知识点列表:")
        for i, kp in enumerate(knowledge_points[:15], 1):
            print(f"   {i}. {kp}")
    else:
        print("❌ 写入 RAG 失败，请检查数据库连接")


if __name__ == "__main__":
    main()
