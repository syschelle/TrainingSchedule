from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .models import BlockType, CustomerPlanningReturn, ScheduleBlock, TrainingProject
from .planner import project_trainers, validate_project
from .rules import DISPLAY_WEEKDAYS, format_time, minutes_between, parse_time

BASE_DIR = Path(__file__).resolve().parents[1]
CUSTOMER_ASSETS_DIR = BASE_DIR / "customer_assets"
DEFAULT_DEV_SECRET = "schulungsplantool-development-customer-exchange-secret"


def _secret() -> bytes:
    configured = os.environ.get("CUSTOMER_EXCHANGE_SECRET", "").strip()
    if configured:
        return configured.encode("utf-8")
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return hashlib.sha256(("customer-exchange:" + database_url).encode("utf-8")).digest()
    return DEFAULT_DEV_SECRET.encode("utf-8")


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _exchange_core(exchange_id: str, exported_at: str, baseline: TrainingProject) -> dict:
    return {
        "format": "schulungsplantool-customer-package",
        "schema_version": 1,
        "exchange_id": exchange_id,
        "exported_at": exported_at,
        "baseline": baseline.model_dump(mode="json"),
    }


def _signature_for_core(core: dict) -> str:
    return hmac.new(_secret(), _canonical_json(core), hashlib.sha256).hexdigest()


def verify_customer_exchange(payload: CustomerPlanningReturn) -> TrainingProject:
    exchange = payload.exchange
    core = _exchange_core(exchange.exchange_id, exchange.exported_at, exchange.baseline)
    expected = _signature_for_core(core)
    if not hmac.compare_digest(expected, exchange.signature):
        raise ValueError("signature_invalid")
    return exchange.baseline.model_copy(deep=True)


def _product_name(project: TrainingProject) -> str:
    product = next((item for item in project.product_lines if item.id == project.product_id), None)
    return product.name if product else (project.product_id or "Produkt")


def _calendar_display_parts(project: TrainingProject, block: ScheduleBlock) -> tuple[str, str]:
    if block.type == BlockType.arrival:
        return "Anreise", ""
    if block.type == BlockType.departure:
        return "Abreise", ""
    if block.type == BlockType.break_block:
        return "Pause", ""
    if block.type == BlockType.lunch:
        return "Mittagspause", ""

    topic_id = block.source_topic_id or block.topic_id
    topic = next((item for item in project.topics if item.id == topic_id), None)
    title = (topic.title if topic else block.title).strip()
    group_label = ""
    marker = "Gruppe "
    marker_index = block.title.rfind(marker)
    if marker_index >= 0:
        candidate = block.title[marker_index:].strip()
        fraction = candidate[len(marker):]
        parts = fraction.split("/", 1)
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            group_label = candidate
    return title, group_label


def _view_data(project: TrainingProject) -> dict:
    weeks = sorted({int(block.week) for block in project.blocks if block.type == BlockType.training})
    trainers = project_trainers(project)
    blocks: list[dict] = []
    for block in project.blocks:
        title, group_label = _calendar_display_parts(project, block)
        blocks.append({
            "id": block.id,
            "type": block.type.value,
            "week": int(block.week),
            "day": block.day,
            "trainer": block.trainer,
            "start": block.start,
            "end": block.end,
            "title": title,
            "group": group_label,
            "background_color": block.background_color,
            "draggable": block.type == BlockType.training,
        })
    return {
        "title": project.title or "Schulungsplan",
        "customer": project.customer_name if project.customer_data_required else "",
        "location": project.location if project.customer_data_required else "",
        "product": _product_name(project),
        "start_date": project.start_date.isoformat() if project.start_date else "",
        "settings": project.settings.model_dump(mode="json"),
        "trainers": trainers,
        "weeks": weeks,
        "blocks": blocks,
    }



def _customer_baseline(project: TrainingProject) -> TrainingProject:
    baseline = project.model_copy(deep=True)
    baseline.product_lines = [item for item in baseline.product_lines if item.id == baseline.product_id]
    baseline.topics = [item for item in baseline.topics if item.product_id == baseline.product_id]
    baseline.unscheduled_topics = [item for item in baseline.unscheduled_topics if item.product_id == baseline.product_id]
    baseline.warnings = []
    return baseline

def _script_safe_json(value: object) -> str:
    # Keep arbitrary project text from terminating the inline <script> element.
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _single_file_customer_html(payload: dict) -> str:
    template = (CUSTOMER_ASSETS_DIR / "index.html").read_text(encoding="utf-8")
    style = (CUSTOMER_ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    app_js = (CUSTOMER_ASSETS_DIR / "app.js").read_text(encoding="utf-8")
    logo_data = base64.b64encode((CUSTOMER_ASSETS_DIR / "dedalus.png").read_bytes()).decode("ascii")
    data_script = "window.SCHULUNGSPLAN_KUNDENPAKET = " + _script_safe_json(payload) + ";"
    return (
        template
        .replace("{{INLINE_STYLE}}", style)
        .replace("{{DEDALUS_DATA_URI}}", "data:image/png;base64," + logo_data)
        .replace("{{INLINE_DATA}}", data_script)
        .replace("{{INLINE_APP_JS}}", app_js)
    )


def build_customer_package(project: TrainingProject) -> bytes:
    if not any(block.type == BlockType.training for block in project.blocks):
        raise ValueError("no_training_blocks")
    baseline = _customer_baseline(project)
    exchange_id = uuid.uuid4().hex
    exported_at = datetime.now(timezone.utc).isoformat()
    core = _exchange_core(exchange_id, exported_at, baseline)
    exchange = {**core, "signature": _signature_for_core(core)}
    payload = {"exchange": exchange, "view": _view_data(baseline)}

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("index.html", _single_file_customer_html(payload).encode("utf-8"))
    return buffer.getvalue()


def _is_quarter(value: str) -> bool:
    try:
        return parse_time(value) % 15 == 0
    except ValueError:
        return False


def _overlap(left: ScheduleBlock, right: ScheduleBlock) -> bool:
    return parse_time(left.start) < parse_time(right.end) and parse_time(right.start) < parse_time(left.end)


def apply_customer_return(payload: CustomerPlanningReturn) -> TrainingProject:
    baseline = verify_customer_exchange(payload)
    updated = baseline.model_copy(deep=True)
    training_by_id = {block.id: block for block in updated.blocks if block.type == BlockType.training}
    original_by_id = {block.id: block for block in baseline.blocks if block.type == BlockType.training}
    allowed_weeks = {int(block.week) for block in baseline.blocks if block.type == BlockType.training}
    allowed_trainers = set(project_trainers(baseline))
    seen: set[str] = set()

    for move in payload.moves:
        if move.block_id in seen:
            raise ValueError("duplicate_move")
        seen.add(move.block_id)
        block = training_by_id.get(move.block_id)
        original = original_by_id.get(move.block_id)
        if block is None or original is None:
            raise ValueError("block_not_allowed")
        if move.week not in allowed_weeks:
            raise ValueError("week_not_allowed")
        if move.day not in DISPLAY_WEEKDAYS:
            raise ValueError("day_not_allowed")
        if move.day == "Freitag" and not updated.settings.friday_training_enabled:
            raise ValueError("friday_not_allowed")
        if move.trainer not in allowed_trainers:
            raise ValueError("trainer_not_allowed")
        if not _is_quarter(move.start) or not _is_quarter(move.end):
            raise ValueError("quarter_grid_required")
        original_duration = minutes_between(original.start, original.end)
        moved_duration = minutes_between(move.start, move.end)
        if moved_duration != original_duration or moved_duration <= 0:
            raise ValueError("duration_changed")
        if parse_time(move.start) < parse_time(updated.settings.day_start) or parse_time(move.end) > parse_time(updated.settings.day_end):
            raise ValueError("outside_working_hours")
        block.week = move.week
        block.day = move.day
        block.trainer = move.trainer
        block.start = move.start
        block.end = move.end

    relevant = [
        block for block in updated.blocks
        if block.type in {BlockType.training, BlockType.arrival, BlockType.departure, BlockType.break_block, BlockType.lunch}
    ]
    for index, left in enumerate(relevant):
        for right in relevant[index + 1:]:
            if left.week != right.week or left.day != right.day or left.trainer != right.trainer:
                continue
            if _overlap(left, right):
                raise ValueError("overlap")

    baseline_warnings = set(validate_project(baseline))
    new_warnings = [warning for warning in validate_project(updated) if warning not in baseline_warnings]
    # The customer exchange intentionally allows moving training onto a day that
    # previously contained no training (and therefore no generated lunch block).
    # Such organizational warnings can be resolved later in the main planner.
    # Configured training-content dependencies, however, must never be bypassed.
    strict_warnings = [warning for warning in new_warnings if "muss mindestens einen Tag nach" in warning]
    if strict_warnings:
        raise ValueError("new_validation_warning:" + " | ".join(strict_warnings[:3]))

    return updated
