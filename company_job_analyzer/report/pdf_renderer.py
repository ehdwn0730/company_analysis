from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from company_job_analyzer.report.report_template import build_report_table_rows
from company_job_analyzer.schema.job_posting_schema import RunReport


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


def render_run_pdf(report: RunReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_korean_font()

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "KoreanBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=6.5,
        leading=9,
        textColor=colors.HexColor("#222222"),
        spaceAfter=0,
    )
    header = ParagraphStyle(
        "KoreanHeader",
        parent=base,
        fontName=font_name,
        fontSize=8,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )
    title = ParagraphStyle("KoreanTitle", parent=base, fontSize=16, leading=22, spaceAfter=10)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    rows = build_report_table_rows(report)
    table_data = [
        [Paragraph(cell, header if row_index == 0 else base) for cell in row]
        for row_index, row in enumerate(rows)
    ]
    table = Table(
        table_data,
        colWidths=[34 * mm, 42 * mm, 70 * mm, 70 * mm, 58 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4858")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B9C3C9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8F9")]),
            ]
        )
    )
    flowables = [Paragraph(report.title, title), Spacer(1, 4 * mm), table]
    doc.build(flowables)
    return output_path


def build_download_link(pdf_path: Path, public_base_url: str | None) -> str:
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{quote(pdf_path.name)}"
    return pdf_path.resolve().as_uri()
