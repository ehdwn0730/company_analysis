from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from company_job_analyzer.report.report_template import build_pdf_story_html
from company_job_analyzer.schema.job_posting_schema import CompanyReport


def _register_korean_font() -> str:
    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]
    for path in candidates:
        if path.exists():
            font_name = "KoreanBaseFont"
            pdfmetrics.registerFont(TTFont(font_name, str(path)))
            return font_name
    return "Helvetica"


def render_company_pdf(report: CompanyReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_korean_font()

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "KoreanBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceAfter=5,
    )
    title = ParagraphStyle("KoreanTitle", parent=base, fontSize=18, leading=24, spaceAfter=12)
    heading = ParagraphStyle("KoreanHeading", parent=base, fontSize=13, leading=18, spaceBefore=12, spaceAfter=6)
    subheading = ParagraphStyle("KoreanSubHeading", parent=base, fontSize=11, leading=16, spaceBefore=8, spaceAfter=4)
    meta = ParagraphStyle("KoreanMeta", parent=base, fontSize=8, leading=12, textColor=colors.HexColor("#555555"))

    style_map = {"title": title, "heading": heading, "subheading": subheading, "meta": meta, "body": base, "html": base}
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    flowables = []
    for kind, content in build_pdf_story_html(report):
        flowables.append(Paragraph(content, style_map[kind]))
        if kind in {"title", "html"}:
            flowables.append(Spacer(1, 5 * mm))
    doc.build(flowables)
    return output_path


def build_download_link(pdf_path: Path, public_base_url: str | None) -> str:
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{quote(pdf_path.name)}"
    return pdf_path.resolve().as_uri()

