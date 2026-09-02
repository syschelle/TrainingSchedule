from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .models import BlockType, TrainingProject
from .planner import project_trainers
from .rules import DISPLAY_WEEKDAYS, german_date, parse_time, training_dates


def planned_weeks(project: TrainingProject) -> list[int]:
    weeks = sorted({block.week for block in project.blocks} | set(project.manual_weeks))
    return weeks or [1]


def _easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _holiday_hints(value: date | None) -> list[str]:
    if value is None:
        return []
    year = value.year
    easter = _easter_sunday(year)
    entries: list[str] = []

    def add(country: str, name: str, when: date) -> None:
        if when == value:
            entries.append(f"{country}: {name}")

    add("DE", "Neujahr", date(year, 1, 1))
    add("DE", "Karfreitag", easter + timedelta(days=-2))
    add("DE", "Ostermontag", easter + timedelta(days=1))
    add("DE", "Tag der Arbeit", date(year, 5, 1))
    add("DE", "Christi Himmelfahrt", easter + timedelta(days=39))
    add("DE", "Pfingstmontag", easter + timedelta(days=50))
    add("DE", "Tag der Deutschen Einheit", date(year, 10, 3))
    add("DE", "1. Weihnachtstag", date(year, 12, 25))
    add("DE", "2. Weihnachtstag", date(year, 12, 26))

    add("AT", "Neujahr", date(year, 1, 1))
    add("AT", "Heilige Drei Koenige", date(year, 1, 6))
    add("AT", "Ostermontag", easter + timedelta(days=1))
    add("AT", "Staatsfeiertag", date(year, 5, 1))
    add("AT", "Christi Himmelfahrt", easter + timedelta(days=39))
    add("AT", "Pfingstmontag", easter + timedelta(days=50))
    add("AT", "Fronleichnam", easter + timedelta(days=60))
    add("AT", "Mariae Himmelfahrt", date(year, 8, 15))
    add("AT", "Nationalfeiertag", date(year, 10, 26))
    add("AT", "Allerheiligen", date(year, 11, 1))
    add("AT", "Mariae Empfaengnis", date(year, 12, 8))
    add("AT", "Christtag", date(year, 12, 25))
    add("AT", "Stefanitag", date(year, 12, 26))

    add("CH", "Bundesfeier", date(year, 8, 1))
    return entries


def _week_date(project: TrainingProject, week: int, day_index: int) -> date | None:
    dates = training_dates(project.start_date)
    base = dates[day_index]
    return base + timedelta(days=(week - 1) * 7) if base else None


def _safe_color(value: str | None, fallback: str = "#ffffff") -> colors.Color:
    try:
        return colors.HexColor(value or fallback)
    except (ValueError, TypeError):
        return colors.HexColor(fallback)


def _contrast_text(background: colors.Color) -> colors.Color:
    luminance = 0.299 * background.red + 0.587 * background.green + 0.114 * background.blue
    return colors.black if luminance > 0.62 else colors.white


def _draw_wrapped_text(pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float, font: str, size: float, max_lines: int = 3) -> None:
    words = str(text or "").split()
    if not words:
        return
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font, size) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(lines)) < len(" ".join(words)):
        last = lines[-1]
        while last and stringWidth(last + "...", font, size) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    pdf.setFont(font, size)
    for line_index, line in enumerate(lines):
        pdf.drawString(x, y - line_index * (size + 2), line)


def export_pdf(project: TrainingProject) -> bytes:
    """Export the same trainer/week calendar concept as the browser preview.

    The PDF is landscape A4. Each trainer gets one full calendar week page,
    ordered chronologically by week and then by trainer. Break and lunch blocks
    stay hidden, exactly like in the browser calendar.
    """
    buffer = BytesIO()
    page_size = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    page_width, page_height = page_size
    margin = 22
    time_axis_width = 34
    top_y = page_height - margin
    grid_bottom = 34
    header_height = 82
    day_header_height = 52
    grid_top = top_y - header_height - day_header_height
    grid_height = grid_top - grid_bottom
    day_width = (page_width - margin * 2 - time_axis_width) / len(DISPLAY_WEEKDAYS)
    day_start = parse_time(project.settings.day_start)
    day_end = parse_time(project.settings.day_end)
    total_minutes = max(60, day_end - day_start)
    trainers = project_trainers(project)
    product = next((item for item in project.product_lines if item.id == project.product_id), None)

    for week in planned_weeks(project):
        for trainer in trainers:
            pdf.setFillColor(colors.HexColor("#0f1b2d"))
            pdf.rect(0, page_height - 66, page_width, 66, fill=1, stroke=0)
            pdf.setFillColor(colors.white)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(margin, page_height - 26, project.title or "Schulungsplan")
            pdf.setFont("Helvetica", 8)
            product_name = product.name if product else project.product_id
            info = f"Produkt: {product_name}  |  Trainer: {trainer or 'Nicht zugewiesen'}  |  Woche {week}"
            pdf.drawString(margin, page_height - 42, info)
            if project.customer_data_required:
                customer = " · ".join(value for value in [project.customer_name, project.location] if value)
                if customer:
                    pdf.drawRightString(page_width - margin, page_height - 42, customer)

            first = _week_date(project, week, 0)
            last = _week_date(project, week, 4)
            pdf.setFillColor(colors.HexColor("#334155"))
            pdf.setFont("Helvetica-Bold", 9)
            date_range = f"{german_date(first)}–{german_date(last)}" if first and last else ""
            pdf.drawString(margin, page_height - 78, f"Woche {week}{' · ' + date_range if date_range else ''}")

            # Day headers
            for day_index, day in enumerate(DISPLAY_WEEKDAYS):
                x = margin + time_axis_width + day_index * day_width
                pdf.setFillColor(colors.HexColor("#f7f9fc"))
                pdf.setStrokeColor(colors.HexColor("#cbd5e1"))
                pdf.rect(x, grid_top, day_width, day_header_height, fill=1, stroke=1)
                pdf.setFillColor(colors.HexColor("#0f172a"))
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(x + 5, grid_top + day_header_height - 14, day)
                current_date = _week_date(project, week, day_index)
                if current_date:
                    pdf.setFont("Helvetica", 7.5)
                    pdf.setFillColor(colors.HexColor("#475569"))
                    pdf.drawString(x + 5, grid_top + day_header_height - 27, german_date(current_date))
                    hints = _holiday_hints(current_date)
                    if hints:
                        pdf.setFillColor(colors.HexColor("#b42318"))
                        _draw_wrapped_text(pdf, " · ".join(hints), x + 5, grid_top + day_header_height - 39, day_width - 10, "Helvetica", 5.8, 2)

            # Quarter-hour grid and time labels.
            quarter_count = total_minutes // 15
            for q in range(quarter_count + 1):
                minute = day_start + q * 15
                y = grid_top - ((minute - day_start) / total_minutes) * grid_height
                is_hour = minute % 60 == 0
                pdf.setStrokeColor(colors.HexColor("#cbd5e1" if is_hour else "#e9eef5"))
                pdf.setLineWidth(0.55 if is_hour else 0.25)
                pdf.line(margin + time_axis_width, y, page_width - margin, y)
                if is_hour:
                    pdf.setFillColor(colors.HexColor("#64748b"))
                    pdf.setFont("Helvetica", 6.5)
                    pdf.drawRightString(margin + time_axis_width - 4, y - 2, f"{minute // 60:02d}:00")

            for day_index in range(len(DISPLAY_WEEKDAYS) + 1):
                x = margin + time_axis_width + day_index * day_width
                pdf.setStrokeColor(colors.HexColor("#cbd5e1"))
                pdf.setLineWidth(0.5)
                pdf.line(x, grid_bottom, x, grid_top)

            # Visible calendar blocks: training, arrival, departure. Break/lunch hidden.
            for day_index, day in enumerate(DISPLAY_WEEKDAYS):
                x = margin + time_axis_width + day_index * day_width
                blocks = [
                    block for block in project.blocks
                    if block.week == week
                    and block.day == day
                    and block.trainer == trainer
                    and block.type not in {BlockType.break_block, BlockType.lunch}
                ]
                for block in sorted(blocks, key=lambda item: item.start):
                    start = max(day_start, parse_time(block.start))
                    end = min(day_end, parse_time(block.end))
                    if end <= start:
                        continue
                    y_top = grid_top - ((start - day_start) / total_minutes) * grid_height
                    y_bottom = grid_top - ((end - day_start) / total_minutes) * grid_height
                    block_height = max(16, y_top - y_bottom)
                    y_bottom = y_top - block_height
                    bg = _safe_color(block.background_color if block.type == BlockType.training else "#eef2ff", "#eef2ff")
                    pdf.setFillColor(bg)
                    pdf.setStrokeColor(colors.HexColor("#94a3b8"))
                    pdf.roundRect(x + 3, y_bottom + 2, day_width - 6, block_height - 4, 3, fill=1, stroke=1)
                    text_color = _contrast_text(bg)
                    pdf.setFillColor(text_color)
                    _draw_wrapped_text(pdf, block.title, x + 7, y_top - 10, day_width - 14, "Helvetica-Bold", 6.8, 3)
                    pdf.setFont("Helvetica", 5.8)
                    pdf.drawString(x + 7, y_bottom + 6, f"{block.start}-{block.end}")

            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica", 6)
            pdf.drawRightString(page_width - margin, 14, "Schulungsplantool · Kalenderexport")
            pdf.showPage()

    pdf.save()
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
    sheet.set_column(0, 0, 18)
    sheet.set_column(1, 1, 15)
    sheet.set_column(2, 6, 24)

    summary = workbook.add_worksheet("Uebersicht")
    summary.write_row(0, 0, ["Modus", "Kunde", "Standort", "Trainer"], header)
    summary.write_row(1, 0, [
        "Dienstleistungskalkulation" if project.project_mode == "service_calculation" else "Schulungsplanung",
        project.customer_name if project.customer_data_required else "",
        project.location if project.customer_data_required else "",
        ", ".join(project_trainers(project)).strip(", "),
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
