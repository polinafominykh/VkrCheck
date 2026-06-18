from pathlib import Path
from typing import List, Set, Tuple
from xml.sax.saxutils import escape
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from core.schemas import PipelineReport

def _register_fonts() -> Tuple[str, str]:
    regular_candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Times New Roman.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
    ]

    bold_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Times New Roman Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
    ]

    regular_path = next((p for p in regular_candidates if Path(p).exists()), None)
    bold_path = next((p for p in bold_candidates if Path(p).exists()), None)

    if regular_path:
        pdfmetrics.registerFont(TTFont("VKRRegular", regular_path))
    else:
        return "Helvetica", "Helvetica-Bold"

    if bold_path:
        pdfmetrics.registerFont(TTFont("VKRBold", bold_path))
    else:
        return "VKRRegular", "VKRRegular"

    return "VKRRegular", "VKRBold"


def _status_label(status: str) -> str:
    mapping = {
        "pass": "Соответствует",
        "warn": "Замечание",
        "fail": "Требует внимания",
    }
    return mapping.get(status.lower(), status)


def _shorten(text: str, limit: int = 170) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _convert_score_100_to_10(text: str) -> str:

    pattern = re.compile(r"Итоговая оценка:\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*100\.?")

    def repl(match: re.Match) -> str:
        score = float(match.group(1))
        short_score = round(score / 10, 1)
        return f"Оценка: {short_score}/10."

    return pattern.sub(repl, text)

def _neutralize_message(text: str) -> str:
    replacements = [
        ("Обязательные разделы найдены", "Обязательные разделы присутствуют"),
        ("Количество глав верхнего уровня в норме", "Количество глав верхнего уровня"),
        ("Введение найдено, объем выглядит достаточным", "Объем введения"),
        ("Список источников найден, позиций", "Количество источников"),
        ("Структура введения выглядит корректно", "Структура введения в целом корректна"),
        ("Смысловая проверка выполнена", "Смысловая оценка выполнена"),
    ]

    result = str(text)
    for old, new in replacements:
        result = result.replace(old, new)

    result = _convert_score_100_to_10(result)
    return result

def _translate_marker_word(text: str) -> str:
    mapping = {
        "actuality": "актуальность",
        "problem": "проблема",
        "goal": "цель",
        "tasks": "задачи",
        "practical_significance": "практическая значимость",
        "novelty": "научная новизна",
        "methods": "методы",
    }
    return mapping.get(text.strip(), text.strip())

def _clean_evidence_item(text: str) -> str:
    text = str(text).strip()

    prefix_map = {
        "found:": "Выявлено:",
        "issue:": "Замечание:",
        "strength:": "Сильная сторона:",
    }

    for old, new in prefix_map.items():
        if text.startswith(old):
            text = text.replace(old, new, 1).strip()
            break

    text = text.replace("найдено", "выделено")

    if ":" in text:
        left, right = text.split(":", 1)
        left = left.strip()
        right = right.strip()
        if left.lower() in {
            "actuality",
            "problem",
            "goal",
            "tasks",
            "practical_significance",
            "novelty",
            "methods",
        }:
            left = _translate_marker_word(left.lower())
            return f"{left}: {right}"

    return text

def _collect_recommendations(report: PipelineReport) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []

    for item in report.all_results:
        for rec in item.recommendations:
            rec = " ".join(str(rec).split()).strip()
            if rec and rec not in seen:
                seen.add(rec)
                result.append(rec)

    return result

def _main_section_titles(report: PipelineReport) -> List[str]:
    result: List[str] = []

    for title in report.chapters.keys():
        low = title.lower().strip()

        if low in {"введение", "заключение"}:
            result.append(title)
            continue

        if "список" in low and ("источник" in low or "литератур" in low):
            result.append(title)
            continue

        if re.match(r"^\d+\s+", title):
            result.append(title)
            continue

    deduped: List[str] = []
    seen = set()
    for item in result:
        if item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped

def _make_result_table(results, body_style):
    rows = [
        [
            Paragraph("<b>Статус</b>", body_style),
            Paragraph("<b>Проверка</b>", body_style),
            Paragraph("<b>Вывод</b>", body_style),
        ]
    ]

    for result in results:
        rows.append(
            [
                Paragraph(f"<b>{escape(_status_label(result.status))}</b>", body_style),
                Paragraph(escape(result.criterion_name), body_style),
                Paragraph(escape(_shorten(_neutralize_message(result.message), 150)), body_style),
            ]
        )

    table = Table(
        rows,
        colWidths=[32 * mm, 52 * mm, 90 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("FONTNAME", (0, 0), (-1, -1), body_style.fontName),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
            ]
        )
    )
    return table

def save_pipeline_report_pdf(report: PipelineReport, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    regular_font, bold_font = _register_fonts()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="VKR Report",
        author="VKRGuard",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleRU",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=17,
        leading=22,
        spaceAfter=10,
        textColor=colors.black,
    )

    heading_style = ParagraphStyle(
        "HeadingRU",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.black,
    )

    body_style = ParagraphStyle(
        "BodyRU",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.5,
        leading=12,
        spaceAfter=3,
        textColor=colors.black,
    )

    small_style = ParagraphStyle(
        "SmallRU",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=8.5,
        leading=10.5,
        spaceAfter=2,
        textColor=colors.black,
    )

    story = []

    story.append(Paragraph("Отчет по автоматической проверке ВКР", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Итог проверки", heading_style))

    summary_data = [
        [Paragraph("<b>Показатель</b>", body_style), Paragraph("<b>Значение</b>", body_style)],
        [Paragraph("Соответствует", body_style), Paragraph(str(report.passed), body_style)],
        [Paragraph("Замечания", body_style), Paragraph(str(report.warned), body_style)],
        [Paragraph("Требует внимания", body_style), Paragraph(str(report.failed), body_style)],
        [Paragraph("Всего проверок", body_style), Paragraph(str(len(report.all_results)), body_style)],
    ]

    summary_table = Table(summary_data, colWidths=[75 * mm, 35 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Основные разделы работы", heading_style))
    clean_titles = _main_section_titles(report)
    if clean_titles:
        for title in clean_titles:
            story.append(Paragraph(f"• {escape(title)}", body_style))
    else:
        story.append(Paragraph("Основные разделы не выделены.", body_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Формальные проверки", heading_style))
    story.append(_make_result_table(report.formal_results, body_style))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Смысловые проверки", heading_style))
    story.append(_make_result_table(report.semantic_results, body_style))

    story.append(PageBreak())

    story.append(Paragraph("Подробные замечания и рекомендации", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2, spaceAfter=8))

    for idx, result in enumerate(report.all_results, start=1):
        story.append(
            Paragraph(
                f"<b>{idx}. {escape(result.criterion_name)}</b> "
                f"({escape(_status_label(result.status))})",
                body_style,
            )
        )
        story.append(Paragraph(escape(_neutralize_message(result.message)), body_style))

        if result.evidence:
            story.append(Paragraph("Основания вывода:", small_style))
            for item in result.evidence[:3]:
                story.append(Paragraph(f"• {escape(_clean_evidence_item(item))}", small_style))

        if result.recommendations:
            story.append(Paragraph("Рекомендации:", small_style))
            for item in result.recommendations[:3]:
                story.append(Paragraph(f"• {escape(str(item))}", small_style))

        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.black, spaceBefore=1, spaceAfter=5))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Сводные рекомендации", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=2, spaceAfter=8))

    recommendations = _collect_recommendations(report)
    if recommendations:
        bullet_items = [ListItem(Paragraph(escape(item), body_style)) for item in recommendations]
        story.append(ListFlowable(bullet_items, bulletType="bullet", leftIndent=12))
    else:
        story.append(Paragraph("Существенных рекомендаций не выявлено.", body_style))

    doc.build(story)
    return str(path)