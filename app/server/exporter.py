from __future__ import annotations

from datetime import timedelta
from io import BytesIO

import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import TrainingProject
from .rules import DISPLAY_WEEKDAYS, german_date, training_dates


def planned_weeks(project: TrainingProject) -> list[int]:
    weeks = sorted({block.week for block in project.blocks} | set(project.manual_weeks))
    return weeks or [1]


def export_pdf(project: TrainingProject) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    product = next((item for item in project.product_lines if item.id == project.product_id), None)
    story = [
        Paragraph("Schulungsplan", styles["Title"]),
        Paragraph(f"Schulung: {project.title}", styles["Normal"]),
        Paragraph(f"Modus: {'Dienstleistungskalkulation' if project.project_mode == 'service_calculation' else 'Schulungsplanung'}", styles["Normal"]),
        Paragraph(f"Produkt: {product.name if product else project.product_id}", styles["Normal"]),
        Paragraph(f"Teilnehmer: {project.participant_group or '-'}", styles["Normal"]),
        Paragraph(f"Trainer: {project.trainer or '-'}", styles["Normal"]),
        Spacer(1, 14),
    ]
    if project.customer_data_required:
        story.insert(3, Paragraph(f"Kunde: {project.customer_name or '-'}", styles["Normal"]))
        story.insert(7, Paragraph(f"Standort: {project.location or '-'}", styles["Normal"]))
    dates = training_dates(project.start_date)
    for week in planned_weeks(project):
        story.append(Paragraph(f"Woche {week}", styles["Heading2"]))
        for index, day in enumerate(DISPLAY_WEEKDAYS):
            display_date = dates[index] + timedelta(days=(week - 1) * 7) if dates[index] else None
            suffix = f", {german_date(display_date)}" if display_date else ""
            story.append(Paragraph(f"{day}{suffix}", styles["Heading3"]))
            rows = [["Zeit", "Inhalt", "Trainer", "Raum"]]
            for block in [item for item in project.blocks if item.week == week and item.day == day]:
                rows.append([f"{block.start}-{block.end}", block.title, block.trainer or "", block.room or ""])
            table = Table(rows, colWidths=[85, 250, 90, 80])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4f5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d2d8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f9")]),
            ]))
            story.extend([table, Spacer(1, 12)])
    if project.warnings:
        story.append(Paragraph("Hinweise", styles["Heading2"]))
        for warning in project.warnings:
            story.append(Paragraph(warning, styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()


def export_xlsx(project: TrainingProject) -> bytes:
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    sheet = workbook.add_worksheet("Schulungsplan")
    header = workbook.add_format({"bold": True, "bg_color": "#1f4f5f", "font_color": "#ffffff"})
    sheet.write_row(0, 0, ["Tag", "Zeit", "Typ", "Inhalt", "Trainer", "Raum", "Hinweise"], header)
    row = 1
    for week in planned_weeks(project):
        for day in DISPLAY_WEEKDAYS:
            for block in [item for item in project.blocks if item.week == week and item.day == day]:
                sheet.write_row(row, 0, [f"Woche {week} {day}", f"{block.start}-{block.end}", block.type.value, block.title, block.trainer, block.room, block.notes])
                row += 1
    sheet.set_column(0, 0, 14)
    sheet.set_column(1, 1, 15)
    sheet.set_column(2, 6, 24)
    summary = workbook.add_worksheet("Uebersicht")
    summary.write_row(0, 0, ["Modus", "Kunde", "Standort"], header)
    summary.write_row(1, 0, [
        "Dienstleistungskalkulation" if project.project_mode == "service_calculation" else "Schulungsplanung",
        project.customer_name if project.customer_data_required else "",
        project.location if project.customer_data_required else "",
    ])
    summary.write_row(3, 0, ["Produkt", "Teilnehmergruppe", "Anzahl"], header)
    row = 4
    for product in project.product_lines:
        for group in product.participant_groups:
            summary.write_row(row, 0, [product.name, group.name, group.participant_count])
            row += 1
    row += 1
    summary.write_row(row, 0, ["Thema", "Geplant Minuten", "Benoetigt Minuten"], header)
    for index, topic in enumerate(project.topics, start=1):
        planned = sum(
            1 for block in project.blocks
            if block.topic_id == topic.id
        ) * topic.duration_minutes
        summary.write_row(row + index, 0, [topic.title, planned, topic.duration_minutes])
    workbook.close()
    return buffer.getvalue()
