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
from .rules import DISPLAY_WEEKDAYS, german_date, minutes_between, parse_time, training_dates


def planned_weeks(project: TrainingProject) -> list[int]:
    """Return only weeks that still contain actual training blocks."""
    return sorted({block.week for block in project.blocks if block.type == BlockType.training})


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


def _format_duration(minutes: int) -> str:
    hours, rest = divmod(max(0, minutes), 60)
    return f"{hours} h {rest} min" if hours else f"{rest} min"


def _service_day_count(project: TrainingProject) -> int:
    # A service day is a trainer-day: two trainers delivering training on the
    # same calendar day represent two billable service days. Multiple blocks
    # by the same trainer on the same day still count once.
    return len({(block.week, block.day, block.trainer.strip()) for block in project.blocks if block.type == BlockType.training})


def _training_minutes(project: TrainingProject) -> int:
    return sum(max(0, minutes_between(block.start, block.end)) for block in project.blocks if block.type == BlockType.training)


def _trainer_week_has_visible_blocks(project: TrainingProject, week: int, trainer: str) -> bool:
    return any(
        block.week == week
        and block.trainer == trainer
        and block.type not in {BlockType.break_block, BlockType.lunch}
        for block in project.blocks
    )


def _unscheduled_minutes(project: TrainingProject) -> int:
    return sum(max(0, item.duration_minutes) for item in project.unscheduled_topics)


def _draw_overview_page(pdf: canvas.Canvas, project: TrainingProject, page_width: float, page_height: float, margin: float) -> None:
    product = next((item for item in project.product_lines if item.id == project.product_id), None)
    trainers = project_trainers(project)
    product_name = product.name if product else project.product_id or "—"
    customer = project.customer_name or "—" if project.customer_data_required else "Nicht erforderlich"
    location = project.location or "—" if project.customer_data_required else "Nicht erforderlich"

    pdf.setFillColor(colors.HexColor("#0f1b2d"))
    pdf.rect(0, page_height - 72, page_width, 72, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, page_height - 29, project.title or "Schulungsplan")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(margin, page_height - 47, "Planuebersicht")
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawRightString(page_width - margin, page_height - 34, f"Kunde: {customer}")
    pdf.drawRightString(page_width - margin, page_height - 47, f"Standort: {location}")

    top = page_height - 96
    left = margin
    gap = 14
    column_width = (page_width - 2 * margin - gap) / 2
    meta = [
        ("Kunde", customer),
        ("Standort", location),
        ("Produkt", product_name),
        ("Startdatum", german_date(project.start_date) or "—"),
        ("Trainer", ", ".join(value or "Nicht zugewiesen" for value in trainers) or "—"),
    ]
    for index, (label, value) in enumerate(meta):
        row = index // 2
        column = index % 2
        if index == 4:
            x = left
            width = page_width - 2 * margin
        else:
            x = left + column * (column_width + gap)
            width = column_width
        y = top - row * 52
        pdf.setFillColor(colors.HexColor("#f8fafc"))
        pdf.setStrokeColor(colors.HexColor("#dbe3ee"))
        pdf.roundRect(x, y - 39, width, 42, 5, fill=1, stroke=1)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica-Bold", 7.2)
        pdf.drawString(x + 9, y - 10, label)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        _draw_wrapped_text(pdf, value, x + 9, y - 23, width - 18, "Helvetica-Bold", 8.4, 2)

    metric_top = top - 160
    metrics = [
        ("Schulung", _format_duration(_training_minutes(project))),
        ("Dienstleistungstage", f"{_service_day_count(project)} {'Tag' if _service_day_count(project) == 1 else 'Tage'}"),
        ("Nicht eingeplant", _format_duration(_unscheduled_minutes(project))),
    ]
    metric_width = (page_width - 2 * margin - 2 * gap) / 3
    for index, (label, value) in enumerate(metrics):
        x = margin + index * (metric_width + gap)
        pdf.setFillColor(colors.HexColor("#f8fafc"))
        pdf.setStrokeColor(colors.HexColor("#dbe3ee"))
        pdf.roundRect(x, metric_top - 44, metric_width, 46, 5, fill=1, stroke=1)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica-Bold", 7.2)
        pdf.drawString(x + 9, metric_top - 13, label)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x + 9, metric_top - 31, value)

    section_top = metric_top - 70
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, section_top, "Produkt und Teilnehmergruppen")
    y = section_top - 17
    if product:
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(margin, y, product.name)
        y -= 13
        if product.description:
            pdf.setFillColor(colors.HexColor("#475569"))
            _draw_wrapped_text(pdf, product.description, margin, y, page_width - 2 * margin, "Helvetica", 7, 2)
            y -= 24
        group_text = " · ".join(f"{group.name}: {group.participant_count}" for group in product.participant_groups)
        if group_text:
            pdf.setFillColor(colors.HexColor("#3157d5"))
            _draw_wrapped_text(pdf, group_text, margin, y, page_width - 2 * margin, "Helvetica-Bold", 7, 2)
            y -= 24
    else:
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica", 7.5)
        pdf.drawString(margin, y, "Keine Produktdaten hinterlegt.")
        y -= 18

    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y, "Schulungsthemen")
    y -= 16
    pdf.setFont("Helvetica", 7.2)
    for index, topic in enumerate(project.topics):
        if y < 32:
            remaining = len(project.topics) - index
            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.drawString(margin, y, f"... {remaining} weitere Themen")
            break
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.drawString(margin, y, topic.title)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawRightString(page_width - margin, y, f"{topic.duration_minutes} min")
        y -= 13

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 6)
    pdf.drawRightString(page_width - margin, 14, "Schulungsplantool · Planuebersicht")
    pdf.showPage()


def _calendar_display_parts(project: TrainingProject, block: ScheduleBlock) -> tuple[str, str]:
    """Return visual calendar title and optional generated split-group label."""
    if block.type == BlockType.arrival:
        return "Anreise", ""
    if block.type != BlockType.training:
        return block.title, ""

    topic_key = block.source_topic_id or block.topic_id
    topic = next((item for item in project.topics if item.id == topic_key), None)
    title = (topic.title if topic else block.title).strip()
    group_label = ""
    group_names = sorted(
        {
            group.name.strip()
            for product in project.product_lines
            for group in product.participant_groups
            if group.name.strip()
        },
        key=len,
        reverse=True,
    )
    for group_name in group_names:
        marker = f" - {group_name}"
        marker_index = block.title.rfind(marker)
        if marker_index < 0:
            continue
        suffix = block.title[marker_index + len(marker):].lstrip()
        if suffix and not suffix.startswith("Gruppe "):
            continue
        if topic is None:
            title = block.title[:marker_index].strip()
        group_label = suffix if suffix.startswith("Gruppe ") else ""
        break
    return title, group_label


def _calendar_display_title(project: TrainingProject, block: ScheduleBlock) -> str:
    """Return a compact one-line title for contexts that cannot show three lines."""
    title, group_label = _calendar_display_parts(project, block)
    return f"{title} - {group_label}" if group_label else title


def _format_hours(minutes: int) -> str:
    hours = max(0, minutes) / 60
    value = f"{hours:.1f}" if hours.is_integer() else f"{hours:.2f}".rstrip("0").rstrip(".")
    return f"{value.replace('.', ',')} h"



def _training_schedule_blocks(project: TrainingProject):
    day_order = {day: index for index, day in enumerate(DISPLAY_WEEKDAYS)}

    def key(block):
        day_index = day_order.get(block.day, 0)
        current_date = _week_date(project, block.week, day_index)
        ordinal = current_date.toordinal() if current_date else block.week * 7 + day_index
        return (ordinal, parse_time(block.start), block.trainer or "", block.title or "")

    return sorted((block for block in project.blocks if block.type == BlockType.training), key=key)


def _training_schedule_groups(project: TrainingProject):
    blocks = _training_schedule_blocks(project)
    trainer_order = list(project_trainers(project))
    for block in blocks:
        trainer = (block.trainer or "").strip()
        if trainer not in trainer_order:
            trainer_order.append(trainer)
    return [
        (trainer, [block for block in blocks if (block.trainer or "").strip() == trainer])
        for trainer in trainer_order
        if any((block.trainer or "").strip() == trainer for block in blocks)
    ]


def _short_weekday(day_name: str, current_date: date | None = None) -> str:
    by_name = {
        "Montag": "Mo",
        "Dienstag": "Di",
        "Mittwoch": "Mi",
        "Donnerstag": "Do",
        "Freitag": "Fr",
        "Samstag": "Sa",
        "Sonntag": "So",
    }
    if day_name in by_name:
        return by_name[day_name]
    if current_date is not None:
        return ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][current_date.weekday()]
    return (day_name or "—")[:2]


def _topic_for_block(project: TrainingProject, block: ScheduleBlock):
    topic_key = block.source_topic_id or block.topic_id
    return next((item for item in project.topics if item.id == topic_key), None)


def _participant_group_for_block(project: TrainingProject, block: ScheduleBlock, topic):
    if topic is None:
        return None
    product = next((item for item in project.product_lines if item.id == (topic.product_id or project.product_id)), None)
    if product is None:
        product = next((item for item in project.product_lines if item.id == project.product_id), None)
    groups = list(product.participant_groups) if product is not None else []
    title = block.title or ""
    for group in sorted(groups, key=lambda item: len((item.name or "").strip()), reverse=True):
        name = (group.name or "").strip()
        if name and f" - {name}" in title:
            return group
    group_ids = list(topic.participant_group_ids or [])
    if len(group_ids) == 1:
        return next((group for group in groups if group.id == group_ids[0]), None)
    if topic.participant_group_id:
        return next((group for group in groups if group.id == topic.participant_group_id), None)
    return None


def _generated_group_index(group_label: str) -> tuple[int, int] | None:
    prefix = "Gruppe "
    value = (group_label or "").strip()
    if not value.startswith(prefix):
        return None
    fraction = value[len(prefix):].split("/")
    if len(fraction) != 2:
        return None
    try:
        index = int(fraction[0])
        total = int(fraction[1])
    except ValueError:
        return None
    return (index, total) if index > 0 and total > 0 else None


def _appointment_participant_count(project: TrainingProject, block: ScheduleBlock) -> int | None:
    topic = _topic_for_block(project, block)
    if topic is None:
        return None
    product = next((item for item in project.product_lines if item.id == (topic.product_id or project.product_id)), None)
    if product is None:
        product = next((item for item in project.product_lines if item.id == project.product_id), None)
    groups = list(product.participant_groups) if product is not None else []
    group = _participant_group_for_block(project, block, topic)
    max_participants = int(topic.participants_per_session or 0)
    _, group_label = _calendar_display_parts(project, block)
    split = _generated_group_index(group_label)
    if group is not None:
        total_participants = max(0, int(group.participant_count or 0))
        if split is not None and max_participants > 0:
            index, _ = split
            return max(0, min(max_participants, total_participants - ((index - 1) * max_participants)))
        return total_participants or None
    selected_ids = list(topic.participant_group_ids or [])
    if selected_ids:
        total = sum(max(0, int(group_item.participant_count or 0)) for group_item in groups if group_item.id in selected_ids)
        return total or None
    return None


def _training_schedule_page_items(project: TrainingProject, rows_per_page: int = 18):
    pages: list[list[tuple[str, object]]] = []
    page: list[tuple[str, object]] = []
    used_rows = 0

    def flush() -> None:
        nonlocal page, used_rows
        if page:
            pages.append(page)
        page = []
        used_rows = 0

    for trainer, blocks in _training_schedule_groups(project):
        index = 0
        while index < len(blocks):
            if used_rows >= rows_per_page - 1:
                flush()
            page.append(("trainer", trainer))
            used_rows += 1
            capacity = max(1, rows_per_page - used_rows)
            chunk = blocks[index:index + capacity]
            page.extend(("block", block) for block in chunk)
            used_rows += len(chunk)
            index += len(chunk)
            if index < len(blocks):
                flush()
    flush()
    return pages or [[]]


def _draw_training_schedule_pages(pdf: canvas.Canvas, project: TrainingProject, page_width: float, page_height: float, margin: float) -> None:
    pages = _training_schedule_page_items(project, 18)
    customer = project.customer_name or "—" if project.customer_data_required else "Nicht erforderlich"
    location = project.location or "—" if project.customer_data_required else "Nicht erforderlich"

    for page_index, page_items in enumerate(pages, start=1):
        pdf.setFillColor(colors.HexColor("#0f1b2d"))
        pdf.rect(0, page_height - 72, page_width, 72, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(margin, page_height - 29, project.title or "Schulungsplan")
        pdf.setFont("Helvetica", 9)
        suffix = f" · {page_index}/{len(pages)}" if len(pages) > 1 else ""
        pdf.drawString(margin, page_height - 47, f"Schulungsthemen{suffix}")
        pdf.setFont("Helvetica-Bold", 7.2)
        pdf.drawRightString(page_width - margin, page_height - 34, f"Kunde: {customer}")
        pdf.drawRightString(page_width - margin, page_height - 47, f"Standort: {location}")

        table_top = page_height - 96
        columns = [
            ("Datum", 100),
            ("Anfang", 52),
            ("Ende", 52),
            ("Dauer", 58),
            ("Schulungsinhalt", 246),
            ("Gruppe", 80),
            ("Teilnehmer", 64),
        ]
        available = page_width - 2 * margin
        widths = [width for _, width in columns]
        scale = available / sum(widths)
        widths = [width * scale for width in widths]
        header_height = 24
        row_height = 22
        trainer_height = 20

        pdf.setFillColor(colors.HexColor("#f3f6fb"))
        pdf.setStrokeColor(colors.HexColor("#dbe3ee"))
        pdf.rect(margin, table_top - header_height, available, header_height, fill=1, stroke=1)
        x = margin
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica-Bold", 6.8)
        for (label, _), width in zip(columns, widths):
            pdf.drawString(x + 5, table_top - 15, label)
            x += width

        if not page_items:
            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin + 8, table_top - header_height - 24, "Keine Schulungen eingeplant.")
        else:
            y = table_top - header_height
            row_index = 0
            for kind, value in page_items:
                if kind == "trainer":
                    y -= trainer_height
                    pdf.setFillColor(colors.HexColor("#eaf0fb"))
                    pdf.setStrokeColor(colors.HexColor("#dbe3ee"))
                    pdf.rect(margin, y, available, trainer_height, fill=1, stroke=1)
                    pdf.setFillColor(colors.HexColor("#0f172a"))
                    pdf.setFont("Helvetica-Bold", 7.4)
                    trainer_name = str(value or "Nicht zugewiesen")
                    pdf.drawString(margin + 6, y + 6, f"Trainer: {trainer_name}")
                    continue

                block = value
                y -= row_height
                if row_index % 2 == 1:
                    pdf.setFillColor(colors.HexColor("#fbfcfe"))
                    pdf.rect(margin, y, available, row_height, fill=1, stroke=0)
                row_index += 1
                pdf.setStrokeColor(colors.HexColor("#e2e8f0"))
                pdf.line(margin, y, margin + available, y)

                title, group_label = _calendar_display_parts(project, block)
                day_index = {day: index for index, day in enumerate(DISPLAY_WEEKDAYS)}.get(block.day, 0)
                current_date = _week_date(project, block.week, day_index)
                date_label = f"{_short_weekday(block.day, current_date)}, {german_date(current_date)}" if current_date else f"{_short_weekday(block.day)} · W{block.week}"
                participant_count = _appointment_participant_count(project, block)
                values = [
                    date_label,
                    block.start,
                    block.end,
                    _format_hours(max(0, minutes_between(block.start, block.end))),
                    title,
                    group_label or "—",
                    str(participant_count) if participant_count is not None else "—",
                ]
                x = margin
                for column_index, (cell_value, width) in enumerate(zip(values, widths)):
                    pdf.setFillColor(colors.HexColor("#0f172a" if column_index != 5 else "#3157d5"))
                    font = "Helvetica-Bold" if column_index == 4 else "Helvetica"
                    size = 6.9 if column_index == 4 else 6.6
                    if column_index == 4:
                        _draw_wrapped_text(pdf, str(cell_value), x + 5, y + 14, width - 10, font, size, 2)
                    else:
                        text = str(cell_value)
                        while text and stringWidth(text, font, size) > width - 10:
                            text = text[:-1]
                        pdf.setFont(font, size)
                        pdf.drawString(x + 5, y + 8, text)
                    x += width

        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica", 6)
        pdf.drawRightString(page_width - margin, 14, "Schulungsplantool · Schulungsthemen")
        pdf.showPage()

def export_pdf(project: TrainingProject) -> bytes:
    """Export the same trainer/week calendar concept as the browser preview.

    The PDF is landscape A4. Page 1 is the project overview. It is followed by
    a chronological training-appointment summary and then by the trainer/week
    calendar pages. Break and lunch blocks stay hidden in the calendar pages.
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

    _draw_overview_page(pdf, project, page_width, page_height, margin)
    _draw_training_schedule_pages(pdf, project, page_width, page_height, margin)

    for week in planned_weeks(project):
        for trainer in trainers:
            if not _trainer_week_has_visible_blocks(project, week, trainer):
                continue
            pdf.setFillColor(colors.HexColor("#0f1b2d"))
            pdf.rect(0, page_height - 66, page_width, 66, fill=1, stroke=0)
            pdf.setFillColor(colors.white)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(margin, page_height - 26, project.title or "Schulungsplan")
            pdf.setFont("Helvetica", 8)
            product_name = product.name if product else project.product_id
            info = f"Produkt: {product_name}  |  Trainer: {trainer or 'Nicht zugewiesen'}  |  Woche {week}"
            pdf.drawString(margin, page_height - 42, info)
            customer = project.customer_name or "—" if project.customer_data_required else "Nicht erforderlich"
            location = project.location or "—" if project.customer_data_required else "Nicht erforderlich"
            pdf.setFont("Helvetica-Bold", 7.2)
            pdf.drawRightString(page_width - margin, page_height - 34, f"Kunde: {customer}")
            pdf.drawRightString(page_width - margin, page_height - 47, f"Standort: {location}")

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
                    display_title, group_label = _calendar_display_parts(project, block)
                    _draw_wrapped_text(pdf, display_title, x + 7, y_top - 10, day_width - 14, "Helvetica-Bold", 6.8, 1)
                    if group_label:
                        pdf.setFont("Helvetica-Bold", 5.9)
                        pdf.drawString(x + 7, y_top - 21, group_label)
                    pdf.setFont("Helvetica", 5.8)
                    duration_minutes = max(0, parse_time(block.end) - parse_time(block.start))
                    pdf.drawString(x + 7, y_bottom + 6, f"{block.start}-{block.end} · {_format_hours(duration_minutes)}")

            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica", 6)
            pdf.drawRightString(page_width - margin, 14, "Schulungsplantool · Kalenderexport")
            pdf.showPage()

    pdf.save()
    return buffer.getvalue()


def _xlsx_font_color(background: str | None) -> str:
    value = (background or "#ffffff").lstrip("#")
    if len(value) != 6:
        return "#000000"
    try:
        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)
    except ValueError:
        return "#000000"
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return "#000000" if luminance > 158 else "#ffffff"


def _xlsx_write_overview(workbook: xlsxwriter.Workbook, project: TrainingProject) -> None:
    sheet = workbook.add_worksheet("Übersicht")
    sheet.hide_gridlines(2)
    sheet.set_landscape()
    sheet.set_paper(9)
    sheet.fit_to_pages(1, 1)
    sheet.set_margins(0.35, 0.35, 0.4, 0.4)
    sheet.set_zoom(90)
    sheet.set_column("A:F", 19)

    dark = "#0f1b2d"
    border = "#dbe3ee"
    light = "#f8fafc"
    muted = "#64748b"
    text = "#0f172a"
    accent = "#3157d5"

    title_fmt = workbook.add_format({
        "bold": True, "font_size": 20, "font_color": "#ffffff",
        "bg_color": dark, "valign": "vcenter",
    })
    sub_fmt = workbook.add_format({
        "font_size": 10, "font_color": "#ffffff", "bg_color": dark,
        "valign": "vcenter",
    })
    header_right_fmt = workbook.add_format({
        "bold": True, "font_size": 8, "font_color": "#ffffff",
        "bg_color": dark, "align": "right", "valign": "vcenter",
    })
    card_label_fmt = workbook.add_format({
        "bold": True, "font_size": 8, "font_color": muted,
        "bg_color": light, "border": 1, "border_color": border,
        "valign": "top",
    })
    card_value_fmt = workbook.add_format({
        "bold": True, "font_size": 10, "font_color": text,
        "bg_color": light, "border": 1, "border_color": border,
        "valign": "vcenter", "text_wrap": True,
    })
    metric_label_fmt = workbook.add_format({
        "bold": True, "font_size": 8, "font_color": muted,
        "bg_color": light, "border": 1, "border_color": border,
    })
    metric_value_fmt = workbook.add_format({
        "bold": True, "font_size": 14, "font_color": text,
        "bg_color": light, "border": 1, "border_color": border,
        "valign": "vcenter",
    })
    section_fmt = workbook.add_format({"bold": True, "font_size": 12, "font_color": text})
    strong_fmt = workbook.add_format({"bold": True, "font_size": 9, "font_color": text})
    body_fmt = workbook.add_format({"font_size": 8, "font_color": "#475569", "text_wrap": True})
    group_fmt = workbook.add_format({"bold": True, "font_size": 8, "font_color": accent, "text_wrap": True})
    topic_fmt = workbook.add_format({"font_size": 8, "font_color": text})
    topic_minutes_fmt = workbook.add_format({"font_size": 8, "font_color": "#475569", "align": "right"})
    footer_fmt = workbook.add_format({"font_size": 7, "font_color": muted, "align": "right"})

    product = next((item for item in project.product_lines if item.id == project.product_id), None)
    product_name = product.name if product else project.product_id or "—"
    trainers = project_trainers(project)
    customer = (project.customer_name or "—") if project.customer_data_required else "Nicht erforderlich"
    location = (project.location or "—") if project.customer_data_required else "Nicht erforderlich"

    sheet.set_row(0, 30)
    sheet.set_row(1, 20)
    sheet.merge_range("A1:D1", project.title or "Schulungsplan", title_fmt)
    sheet.merge_range("E1:F1", f"Kunde: {customer}", header_right_fmt)
    sheet.merge_range("A2:D2", "Planübersicht", sub_fmt)
    sheet.merge_range("E2:F2", f"Standort: {location}", header_right_fmt)

    def write_card(label_range: str, value_range: str, label: str, value: str) -> None:
        sheet.merge_range(label_range, label, card_label_fmt)
        sheet.merge_range(value_range, value, card_value_fmt)

    write_card("A4:C4", "A5:C6", "Kunde", customer)
    write_card("D4:F4", "D5:F6", "Standort", location)
    write_card("A8:C8", "A9:C10", "Produkt", product_name)
    write_card("D8:F8", "D9:F10", "Startdatum", german_date(project.start_date) or "—")
    write_card("A12:F12", "A13:F14", "Trainer", ", ".join(value or "Nicht zugewiesen" for value in trainers) or "—")

    metrics = [
        ("A16:B16", "A17:B18", "Schulung", _format_duration(_training_minutes(project))),
        ("C16:D16", "C17:D18", "Dienstleistungstage", f"{_service_day_count(project)} {'Tag' if _service_day_count(project) == 1 else 'Tage'}"),
        ("E16:F16", "E17:F18", "Nicht eingeplant", _format_duration(_unscheduled_minutes(project))),
    ]
    for label_range, value_range, label, value in metrics:
        sheet.merge_range(label_range, label, metric_label_fmt)
        sheet.merge_range(value_range, value, metric_value_fmt)

    row = 20
    sheet.merge_range(row, 0, row, 5, "Produkt und Teilnehmergruppen", section_fmt)
    row += 2
    if product:
        sheet.merge_range(row, 0, row, 5, product.name, strong_fmt)
        row += 1
        if product.description:
            sheet.merge_range(row, 0, row + 1, 5, product.description, body_fmt)
            row += 2
        group_text = " · ".join(f"{group.name}: {group.participant_count}" for group in product.participant_groups)
        if group_text:
            sheet.merge_range(row, 0, row + 1, 5, group_text, group_fmt)
            row += 3
    else:
        sheet.merge_range(row, 0, row, 5, "Keine Produktdaten hinterlegt.", body_fmt)
        row += 2

    sheet.merge_range(row, 0, row, 5, "Schulungsthemen", section_fmt)
    row += 2
    for topic in project.topics:
        sheet.merge_range(row, 0, row, 4, topic.title, topic_fmt)
        sheet.write(row, 5, f"{topic.duration_minutes} min", topic_minutes_fmt)
        row += 1

    row += 2
    sheet.merge_range(row, 0, row, 5, "Schulungsplantool · Planübersicht", footer_fmt)
    sheet.print_area(0, 0, row, 5)


def _xlsx_write_week(workbook: xlsxwriter.Workbook, project: TrainingProject, week: int) -> None:
    sheet = workbook.add_worksheet(f"Woche {week}")
    sheet.hide_gridlines(2)
    sheet.set_landscape()
    sheet.set_paper(9)
    sheet.fit_to_pages(1, 0)
    sheet.set_margins(0.3, 0.3, 0.35, 0.35)
    sheet.set_zoom(75)
    sheet.set_column("A:A", 8)
    sheet.set_column("B:F", 25)

    dark = "#0f1b2d"
    border = "#cbd5e1"
    quarter_border = "#e9eef5"
    muted = "#64748b"
    text = "#0f172a"

    title_fmt = workbook.add_format({
        "bold": True, "font_size": 18, "font_color": "#ffffff",
        "bg_color": dark, "valign": "vcenter",
    })
    info_fmt = workbook.add_format({
        "font_size": 8, "font_color": "#ffffff", "bg_color": dark,
        "valign": "vcenter",
    })
    right_header_fmt = workbook.add_format({
        "bold": True, "font_size": 8, "font_color": "#ffffff", "bg_color": dark,
        "align": "right", "valign": "vcenter",
    })
    week_fmt = workbook.add_format({"bold": True, "font_size": 10, "font_color": "#334155"})
    day_fmt = workbook.add_format({
        "bold": True, "font_size": 9, "font_color": text,
        "bg_color": "#f7f9fc", "border": 1, "border_color": border,
        "valign": "top", "text_wrap": True,
    })
    time_hour_fmt = workbook.add_format({
        "font_size": 7, "font_color": muted, "align": "right", "valign": "top",
        "bottom": 1, "bottom_color": border,
    })
    time_quarter_fmt = workbook.add_format({
        "font_size": 7, "font_color": muted, "align": "right", "valign": "top",
        "bottom": 1, "bottom_color": quarter_border,
    })
    grid_hour_fmt = workbook.add_format({
        "bottom": 1, "bottom_color": border, "right": 1, "right_color": border,
        "left": 1, "left_color": border,
    })
    grid_quarter_fmt = workbook.add_format({
        "bottom": 1, "bottom_color": quarter_border, "right": 1, "right_color": border,
        "left": 1, "left_color": border,
    })
    footer_fmt = workbook.add_format({"font_size": 7, "font_color": muted, "align": "right"})

    product = next((item for item in project.product_lines if item.id == project.product_id), None)
    product_name = product.name if product else project.product_id or "—"
    customer = (project.customer_name or "—") if project.customer_data_required else "Nicht erforderlich"
    location = (project.location or "—") if project.customer_data_required else "Nicht erforderlich"
    day_start = parse_time(project.settings.day_start)
    day_end = parse_time(project.settings.day_end)
    total_minutes = max(15, day_end - day_start)
    quarter_count = max(1, (total_minutes + 14) // 15)

    all_trainers = project_trainers(project)
    visible_trainers = [
        trainer for trainer in all_trainers
        if _trainer_week_has_visible_blocks(project, week, trainer)
    ]
    if not visible_trainers:
        visible_trainers = all_trainers

    block_formats: dict[tuple[str, str, int], xlsxwriter.format.Format] = {}

    def block_format(background: str, foreground: str, font_size: int) -> xlsxwriter.format.Format:
        key = (background, foreground, font_size)
        if key not in block_formats:
            block_formats[key] = workbook.add_format({
                "bold": True,
                "font_size": font_size,
                "font_color": foreground,
                "bg_color": background,
                "border": 1,
                "border_color": "#94a3b8",
                "text_wrap": True,
                "valign": "top",
                "align": "left",
            })
        return block_formats[key]

    current_row = 0
    page_breaks: list[int] = []
    for trainer_index, trainer in enumerate(visible_trainers):
        if trainer_index:
            page_breaks.append(current_row)

        sheet.set_row(current_row, 28)
        sheet.merge_range(current_row, 0, current_row, 2, project.title or "Schulungsplan", title_fmt)
        sheet.merge_range(current_row, 3, current_row, 5, f"Kunde: {customer}", right_header_fmt)
        current_row += 1
        sheet.set_row(current_row, 20)
        info = f"Produkt: {product_name}  |  Trainer: {trainer or 'Nicht zugewiesen'}  |  Woche {week}"
        sheet.merge_range(current_row, 0, current_row, 2, info, info_fmt)
        sheet.merge_range(current_row, 3, current_row, 5, f"Standort: {location}", right_header_fmt)
        current_row += 2

        first = _week_date(project, week, 0)
        last = _week_date(project, week, 4)
        date_range = f"{german_date(first)}-{german_date(last)}" if first and last else ""
        sheet.merge_range(current_row, 0, current_row, 5, f"Woche {week}{' · ' + date_range if date_range else ''}", week_fmt)
        current_row += 2

        header_row = current_row
        sheet.write(header_row, 0, "", day_fmt)
        for day_index, day in enumerate(DISPLAY_WEEKDAYS):
            current_date = _week_date(project, week, day_index)
            header_text = day
            if current_date:
                header_text += f"\n{german_date(current_date)}"
                hints = _holiday_hints(current_date)
                if hints:
                    header_text += "\n" + " · ".join(hints)
            sheet.write(header_row, day_index + 1, header_text, day_fmt)
        sheet.set_row(header_row, 42)
        grid_start = header_row + 1

        for quarter_index in range(quarter_count):
            row = grid_start + quarter_index
            sheet.set_row(row, 20)
            minute = day_start + quarter_index * 15
            is_hour = minute % 60 == 0
            time_label = f"{minute // 60:02d}:00" if is_hour else ""
            sheet.write(row, 0, time_label, time_hour_fmt if is_hour else time_quarter_fmt)
            for day_col in range(1, 6):
                sheet.write_blank(row, day_col, None, grid_hour_fmt if is_hour else grid_quarter_fmt)

        final_row = grid_start + quarter_count - 1
        for day_index, day in enumerate(DISPLAY_WEEKDAYS):
            day_col = day_index + 1
            blocks = [
                block for block in project.blocks
                if block.week == week
                and block.day == day
                and block.trainer == trainer
                and block.type not in {BlockType.break_block, BlockType.lunch}
            ]
            for block in sorted(blocks, key=lambda item: item.start):
                raw_start = max(day_start, parse_time(block.start))
                raw_end = min(day_end, parse_time(block.end))
                if raw_end <= raw_start:
                    continue
                start_index = max(0, (raw_start - day_start) // 15)
                end_index = min(quarter_count, (raw_end - day_start + 14) // 15)
                row_start = grid_start + start_index
                row_end = max(row_start, grid_start + end_index - 1)
                duration_minutes = max(0, parse_time(block.end) - parse_time(block.start))
                display_title, group_label = _calendar_display_parts(project, block)
                lines = [display_title]
                if group_label:
                    lines.append(group_label)
                lines.append(f"{block.start}-{block.end} · {_format_hours(duration_minutes)}")
                cell_text = "\n".join(lines)
                background = block.background_color if block.type == BlockType.training else "#eef2ff"
                if not background or not background.startswith("#") or len(background) != 7:
                    background = "#eef2ff"
                foreground = _xlsx_font_color(background)
                font_size = 6 if duration_minutes <= 30 else 7 if duration_minutes <= 60 else 8
                fmt = block_format(background, foreground, font_size)
                if row_end > row_start:
                    sheet.merge_range(row_start, day_col, row_end, day_col, cell_text, fmt)
                else:
                    sheet.write(row_start, day_col, cell_text, fmt)

        current_row = final_row + 2
        sheet.merge_range(current_row, 0, current_row, 5, "Schulungsplantool · Kalenderexport", footer_fmt)
        current_row += 3

    if page_breaks:
        sheet.set_h_pagebreaks(page_breaks)
    if current_row:
        sheet.print_area(0, 0, current_row - 1, 5)


def export_xlsx(project: TrainingProject) -> bytes:
    """Export a workbook that mirrors the PDF structure.

    The first worksheet is the project overview. Every planned calendar week
    gets its own worksheet (``Woche 1``, ``Woche 2``, ...). Trainer calendars
    are stacked vertically inside the matching week sheet and use the same
    Monday-Friday, quarter-hour presentation as the PDF calendar pages.
    """
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    workbook.set_properties({
        "title": project.title or "Schulungsplan",
        "subject": "Schulungsplan",
        "author": "Schulungsplantool",
    })

    _xlsx_write_overview(workbook, project)
    for week in planned_weeks(project):
        _xlsx_write_week(workbook, project, week)

    workbook.close()
    return buffer.getvalue()
