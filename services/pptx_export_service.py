"""
PPTX 专业导出服务（融合 pptx-official skill 专业规范）
- CJK 三槽字体：a:latin + a:ea + a:cs，中文不乱码
- 演讲者备注：每张幻灯片写入 notes_slide
- 背景层 z-order 控制
- 5 种主题 × 7 种版式，16:9 宽屏
"""
import os
import uuid
from datetime import datetime

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from core.logger import error, info, warning
from services.lesson_plan_service import PPT_STYLES

# 中文字体（Windows 通用）
CJK_FONT = "Microsoft YaHei"


# ── CJK 字体三槽设置（来自 pptx-official skill）──
def set_cjk_font(run, font_name=CJK_FONT):
    """同时设置 Latin / East-Asian / Complex-Script 字体，保证中文正常渲染"""
    run.font.name = font_name
    rPr = run._r.get_or_add_rPr()
    successors = {
        "a:ea": ("a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst"),
        "a:cs": ("a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst"),
    }
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.insert_element_before(el, *successors[tag])
        el.set("typeface", font_name)


def _set_notes(slide, text):
    """写入演讲者备注"""
    if not text:
        return
    try:
        slide.notes_slide.notes_text_frame.text = text
    except Exception:
        pass


class PPTXExportService:
    """PPTX 专业导出服务"""

    def __init__(self):
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)

    # ── 公开接口 ──

    def export(self, ppt_content: dict, style: str = "modern") -> dict:
        cfg = PPT_STYLES.get(style, PPT_STYLES["modern"])
        slides = ppt_content.get("slides", [])
        if not slides:
            return {"success": False, "message": "幻灯片内容为空"}

        try:
            prs = Presentation()
            prs.slide_width = Inches(13.333)   # 16:9
            prs.slide_height = Inches(7.5)

            for slide_data in slides:
                stype = slide_data.get("type", "content")
                handler = getattr(self, f"_slide_{stype}", self._slide_content)
                handler(prs, slide_data, cfg)

            fname = f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.pptx"
            fpath = os.path.join(self.export_dir, fname)
            prs.save(fpath)
            info(f"PPTX 导出成功: {fpath}")
            # 用 pptx-skill 诊断工具做 QA 校验
            self._validate(fpath)
            return {"success": True, "file_path": fpath, "filename": fname, "message": "导出成功"}
        except Exception as e:
            error(f"PPTX 导出失败: {e!s}")
            return {"success": False, "message": str(e)}

    def _validate(self, fpath: str):
        """用内置 pptx-skill 的 diagnose.py 做文件完整性检查"""
        import subprocess
        import sys

        script = os.path.join("tools", "pptx-skill", "scripts", "diagnose.py")
        if not os.path.exists(script):
            return
        try:
            result = subprocess.run(
                [sys.executable, script, fpath],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                warning(f"诊断警告: {result.stdout[:200]}")
            else:
                info("PPTX 诊断通过")
        except Exception as e:
            warning(f"诊断跳过: {e!s}")

    # ── 幻灯片布局 ──

    def _slide_title(self, prs, data, cfg):
        """封面页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_dark"])

        self._add_rect(slide, 0, 0, 13.333, 0.08, cfg["accent"])

        self._add_text(
            slide, 1.5, 2.2, 10.333, 1.5,
            data.get("title", ""),
            size=40, bold=True, color=cfg["text_light"],
            align=PP_ALIGN.CENTER,
        )
        self._add_text(
            slide, 2.5, 4.0, 8.333, 0.8,
            data.get("subtitle", ""),
            size=22, color=cfg["accent"],
            align=PP_ALIGN.CENTER,
        )
        self._add_rect(slide, 4.5, 5.2, 4.333, 0.03, cfg["accent"])
        self._add_text(
            slide, 2, 5.5, 9.333, 0.5,
            datetime.now().strftime("%Y年%m月"),
            size=14, color=cfg["accent"], align=PP_ALIGN.CENTER,
        )
        _set_notes(slide, data.get("notes", ""))

    def _slide_objectives(self, prs, data, cfg):
        """学习目标页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_light"])
        self._add_rect(slide, 0, 0, 0.15, 7.5, cfg["primary"])
        self._add_text(slide, 0.8, 0.5, 11, 0.9, data.get("title", "学习目标"),
                       size=32, bold=True, color=cfg["primary"])
        self._add_rect(slide, 0.8, 1.35, 3, 0.04, cfg["secondary"])

        bullets = data.get("bullets", [])
        y = 2.0
        for i, b in enumerate(bullets):
            self._add_circle(slide, 1.2, y + 0.05, 0.45, cfg["secondary"])
            self._add_text(slide, 1.2, y + 0.05, 0.45, 0.45, str(i + 1),
                           size=16, bold=True, color="FFFFFF",
                           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            self._add_text(slide, 2.0, y, 10, 0.7, b, size=20, color=cfg["text_dark"])
            y += 1.1
        _set_notes(slide, data.get("notes", ""))

    def _slide_section(self, prs, data, cfg):
        """章节分隔页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_dark"])
        self._add_rect(slide, 0, 3.2, 13.333, 1.2, cfg["primary"])
        self._add_text(slide, 1, 3.2, 11.333, 1.2, data.get("title", ""),
                       size=36, bold=True, color="FFFFFF",
                       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        self._add_text(slide, 1, 4.6, 11.333, 0.8, data.get("subtitle", ""),
                       size=20, color=cfg["accent"], align=PP_ALIGN.CENTER)
        _set_notes(slide, data.get("notes", ""))

    def _slide_content(self, prs, data, cfg):
        """标准内容页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_light"])
        self._add_rect(slide, 0, 0, 0.15, 7.5, cfg["primary"])
        self._add_text(slide, 0.8, 0.4, 11, 0.9, data.get("title", ""),
                       size=30, bold=True, color=cfg["primary"])
        self._add_rect(slide, 0.8, 1.25, 3, 0.04, cfg["secondary"])

        bullets = data.get("bullets", [])
        y = 1.8
        for b in bullets:
            self._add_rect(slide, 1.1, y + 0.15, 0.12, 0.12, cfg["secondary"])
            self._add_text(slide, 1.5, y, 11, 0.8, b, size=20, color=cfg["text_dark"])
            y += 0.9
        _set_notes(slide, data.get("notes", ""))

    def _slide_two_column(self, prs, data, cfg):
        """双栏对比页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_light"])
        self._add_rect(slide, 0, 0, 0.15, 7.5, cfg["primary"])
        self._add_text(slide, 0.8, 0.4, 11, 0.9, data.get("title", ""),
                       size=30, bold=True, color=cfg["primary"])
        self._add_rect(slide, 0.8, 1.25, 3, 0.04, cfg["secondary"])

        # 左栏
        self._add_rounded_rect(slide, 0.8, 1.8, 5.5, 5.0, cfg["bg_dark"])
        self._add_text(slide, 1.2, 2.1, 4.8, 0.7, data.get("left_title", ""),
                       size=22, bold=True, color=cfg["accent"])
        y = 3.0
        for b in data.get("left_bullets", []):
            self._add_text(slide, 1.4, y, 4.5, 0.7, f"▸ {b}",
                           size=17, color=cfg["text_light"])
            y += 0.8

        # 右栏
        self._add_rounded_rect(slide, 6.9, 1.8, 5.5, 5.0, cfg["bg_dark"])
        self._add_text(slide, 7.3, 2.1, 4.8, 0.7, data.get("right_title", ""),
                       size=22, bold=True, color=cfg["accent"])
        y = 3.0
        for b in data.get("right_bullets", []):
            self._add_text(slide, 7.5, y, 4.5, 0.7, f"▸ {b}",
                           size=17, color=cfg["text_light"])
            y += 0.8
        _set_notes(slide, data.get("notes", ""))

    def _slide_activity(self, prs, data, cfg):
        """课堂活动页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_light"])
        self._add_rect(slide, 0, 0, 0.15, 7.5, cfg["primary"])
        self._add_text(slide, 0.8, 0.4, 11, 0.9, data.get("title", "课堂活动"),
                       size=30, bold=True, color=cfg["primary"])

        time_tag = data.get("time", "10分钟")
        self._add_rounded_rect(slide, 10.5, 0.5, 2, 0.6, cfg["secondary"])
        self._add_text(slide, 10.5, 0.5, 2, 0.6, time_tag,
                       size=14, bold=True, color="FFFFFF",
                       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

        self._add_rect(slide, 0.8, 1.25, 3, 0.04, cfg["secondary"])
        self._add_text(slide, 0.8, 1.5, 11.5, 0.8, data.get("description", ""),
                       size=18, color=cfg["text_dark"])

        steps = data.get("steps", [])
        y = 2.6
        for i, step in enumerate(steps):
            self._add_rounded_rect(slide, 1.2, y, 10.5, 0.9, cfg["bg_dark"])
            self._add_circle(slide, 1.5, y + 0.15, 0.6, cfg["accent"])
            self._add_text(slide, 1.5, y + 0.15, 0.6, 0.6, str(i + 1),
                           size=16, bold=True, color="FFFFFF",
                           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            self._add_text(slide, 2.5, y + 0.15, 8.8, 0.6, step,
                           size=18, color=cfg["text_light"])
            y += 1.15
        _set_notes(slide, data.get("notes", ""))

    def _slide_summary(self, prs, data, cfg):
        """课堂小结页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_light"])
        self._add_rect(slide, 0, 0, 0.15, 7.5, cfg["primary"])
        self._add_text(slide, 0.8, 0.4, 11, 0.9, data.get("title", "课堂小结"),
                       size=32, bold=True, color=cfg["primary"])
        self._add_rect(slide, 0.8, 1.3, 3, 0.04, cfg["secondary"])

        bullets = data.get("bullets", [])
        y = 2.0
        for b in bullets:
            self._add_rounded_rect(slide, 1.2, y, 10.8, 0.9, cfg["bg_dark"])
            self._add_circle(slide, 1.6, y + 0.18, 0.55, cfg["accent"])
            self._add_text(slide, 1.6, y + 0.18, 0.55, 0.55, "✓",
                           size=18, bold=True, color="FFFFFF",
                           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            self._add_text(slide, 2.6, y + 0.15, 9, 0.6, b,
                           size=20, color=cfg["text_light"])
            y += 1.15
        _set_notes(slide, data.get("notes", ""))

    def _slide_qa(self, prs, data, cfg):
        """Q&A 页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._fill_bg(slide, cfg["bg_dark"])
        self._add_rect(slide, 0, 0, 13.333, 0.08, cfg["accent"])
        self._add_text(slide, 1, 2.5, 11.333, 1.2, data.get("title", "谢谢观看"),
                       size=44, bold=True, color=cfg["text_light"],
                       align=PP_ALIGN.CENTER)
        self._add_text(slide, 1, 4.0, 11.333, 0.8, data.get("subtitle", "Q & A"),
                       size=28, color=cfg["accent"], align=PP_ALIGN.CENTER)
        self._add_rect(slide, 5, 5.2, 3.333, 0.03, cfg["accent"])
        _set_notes(slide, data.get("notes", ""))

    # ── 基础绘图工具 ──

    @staticmethod
    def _fill_bg(slide, color_hex):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(color_hex)

    @staticmethod
    def _add_rect(slide, left, top, width, height, color_hex):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(left), Inches(top), Inches(width), Inches(height),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(color_hex)
        shape.line.fill.background()
        return shape

    @staticmethod
    def _add_rounded_rect(slide, left, top, width, height, color_hex):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left), Inches(top), Inches(width), Inches(height),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(color_hex)
        shape.line.fill.background()
        return shape

    @staticmethod
    def _add_circle(slide, left, top, size, color_hex):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(left), Inches(top), Inches(size), Inches(size),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(color_hex)
        shape.line.fill.background()
        return shape

    def _add_text(self, slide, left, top, width, height, text, *,
                  size=18, bold=False, color="000000",
                  align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        txbox = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        tf = txbox.text_frame
        tf.word_wrap = True
        try:
            tf.vertical_anchor = anchor
        except Exception:
            pass
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor.from_string(color)
        # CJK 三槽字体 — 保证中文正常显示
        set_cjk_font(run)
        return txbox


# 全局单例
pptx_export_service = PPTXExportService()
