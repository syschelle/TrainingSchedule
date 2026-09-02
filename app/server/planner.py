from __future__ import annotations

from collections import defaultdict
from math import ceil
from uuid import uuid4

from .models import BlockType, ScheduleBlock, TrainingProject, TrainingTopic
from .rules import DISPLAY_WEEKDAYS, WEEKDAYS, format_time, is_overlap, minutes_between, parse_time


def sort_topics(topics: list[TrainingTopic]) -> list[TrainingTopic]:
    by_id = {topic.id: topic for topic in topics}
    visited: set[str] = set()
    result: list[TrainingTopic] = []

    def visit(topic: TrainingTopic) -> None:
        if topic.id in visited:
            return
        if topic.depends_on and topic.depends_on in by_id:
            visit(by_id[topic.depends_on])
        visited.add(topic.id)
        result.append(topic)

    for topic in sorted(topics, key=lambda item: (item.preferred_day or "", item.preferred_order or 999, item.priority, item.title.lower())):
        visit(topic)
    return result


def training_days(project: TrainingProject) -> list[str]:
    days = list(WEEKDAYS)
    if project.settings.friday_training_enabled:
        days.append("Freitag")
    return days


def absolute_day_index(week: int, day: str) -> int:
    return (week - 1) * len(DISPLAY_WEEKDAYS) + DISPLAY_WEEKDAYS.index(day)


def expand_topic_sessions(project: TrainingProject) -> tuple[list[TrainingTopic], dict[str, str]]:
    groups = {
        group.id: group
        for product in project.product_lines
        for group in product.participant_groups
    }
    expanded: list[TrainingTopic] = []
    source_by_id: dict[str, str] = {}
    for topic in project.topics:
        group_ids = topic.participant_group_ids or ([topic.participant_group_id] if topic.participant_group_id else [])
        max_participants = topic.participants_per_session or 0
        selected_groups = [groups[group_id] for group_id in group_ids if group_id in groups]
        if not selected_groups or max_participants <= 0:
            expanded.append(topic)
            source_by_id[topic.id] = topic.id
            continue
        for group in selected_groups:
            if group.participant_count <= max_participants:
                session_topic = topic.model_copy(update={
                    "id": topic.id if len(selected_groups) == 1 else f"{topic.id}-{group.id}",
                    "title": f"{topic.title} - {group.name}",
                    "participant_group_id": group.id,
                })
                expanded.append(session_topic)
                source_by_id[session_topic.id] = topic.id
                continue
            session_count = ceil(group.participant_count / max_participants)
            for index in range(1, session_count + 1):
                session_topic = topic.model_copy(update={
                    "id": topic.id if len(selected_groups) == 1 and index == 1 else f"{topic.id}-{group.id}-gruppe-{index}",
                    "title": f"{topic.title} - {group.name} Gruppe {index}/{session_count}",
                    "participant_group_id": group.id,
                    "sessions_required": session_count,
                })
                expanded.append(session_topic)
                source_by_id[session_topic.id] = topic.id
    return expanded, source_by_id


def _add_fixed_blocks(project: TrainingProject, day: str, week: int) -> list[ScheduleBlock]:
    settings = project.settings
    blocks: list[ScheduleBlock] = []
    if day == "Montag" and settings.monday_arrival_enabled:
        blocks.append(ScheduleBlock(
            id=f"arrival-{uuid4().hex[:8]}",
            type=BlockType.arrival,
            week=week,
            day=day,
            title=settings.monday_arrival_label,
            start=settings.monday_arrival_start,
            end=settings.monday_arrival_end,
        ))
    if day == "Donnerstag" and settings.thursday_departure_enabled and not settings.friday_training_enabled:
        blocks.append(ScheduleBlock(
            id=f"departure-{uuid4().hex[:8]}",
            type=BlockType.departure,
            week=week,
            day=day,
            title=settings.thursday_departure_label,
            start=settings.thursday_departure_start,
            end=settings.thursday_departure_end,
        ))
    return blocks


def _latest_training_end(project: TrainingProject, day: str) -> int:
    settings = project.settings
    if day == "Donnerstag" and settings.thursday_departure_enabled and not settings.friday_training_enabled:
        return min(parse_time(settings.day_end), parse_time(settings.thursday_departure_start))
    return parse_time(settings.day_end)


def plan_project(project: TrainingProject) -> TrainingProject:
    settings = project.settings
    scheduled: list[ScheduleBlock] = []
    unscheduled: list[TrainingTopic] = []
    used_lunch: set[tuple[int, str]] = set()
    cursor_by_day: dict[tuple[int, str], int] = {}
    initialized_weeks: set[int] = set()
    topic_placement: dict[str, int] = {}
    available_days = training_days(project)

    def ensure_week(week: int) -> None:
        if week in initialized_weeks:
            return
        for day in available_days:
            scheduled.extend(_add_fixed_blocks(project, day, week))
            cursor = parse_time(settings.day_start)
            if day == "Montag" and settings.monday_arrival_enabled:
                cursor = max(cursor, parse_time(settings.monday_arrival_end))
            cursor_by_day[(week, day)] = cursor
        initialized_weeks.add(week)

    def place_lunch(week: int, day: str) -> None:
        key = (week, day)
        if key in used_lunch:
            return
        lunch_start = max(cursor_by_day[key], parse_time(settings.lunch_window_start))
        lunch_end = lunch_start + settings.lunch_minutes
        if lunch_end <= _latest_training_end(project, day):
            scheduled.append(ScheduleBlock(
                id=f"lunch-{uuid4().hex[:8]}",
                type=BlockType.lunch,
                week=week,
                day=day,
                title="Mittagspause",
                start=format_time(lunch_start),
                end=format_time(lunch_end),
            ))
            cursor_by_day[key] = lunch_end
            used_lunch.add(key)

    ensure_week(1)

    expanded_topics, source_by_id = expand_topic_sessions(project)

    for topic in sort_topics(expanded_topics):
        candidate_days = [topic.preferred_day] if topic.preferred_day in available_days else available_days
        earliest_day = topic_placement.get(topic.depends_on, -1) + 1 if topic.depends_on else 0
        placed = False
        for week in range(1, 13):
            ensure_week(week)
            for day in candidate_days:
                if day is None or absolute_day_index(week, day) < earliest_day:
                    continue
                key = (week, day)
                cursor = cursor_by_day[key]
                day_end = _latest_training_end(project, day)
                if cursor >= parse_time(settings.lunch_window_start) and key not in used_lunch:
                    place_lunch(week, day)
                    cursor = cursor_by_day[key]
                needed = topic.duration_minutes
                if scheduled and any(block.week == week and block.day == day and block.type == BlockType.training for block in scheduled):
                    needed += settings.break_preferred_minutes
                if cursor + needed > day_end:
                    continue
                if any(block.week == week and block.day == day and block.type == BlockType.training for block in scheduled):
                    break_end = cursor + settings.break_preferred_minutes
                    scheduled.append(ScheduleBlock(
                        id=f"break-{uuid4().hex[:8]}",
                        type=BlockType.break_block,
                        week=week,
                        day=day,
                        title="Pause",
                        start=format_time(cursor),
                        end=format_time(break_end),
                    ))
                    cursor = break_end
                start = cursor
                end = start + topic.duration_minutes
                scheduled.append(ScheduleBlock(
                    id=f"training-{uuid4().hex[:8]}",
                    type=BlockType.training,
                    week=week,
                    day=day,
                    title=topic.title,
                    description=topic.description,
                    start=format_time(start),
                    end=format_time(end),
                    topic_id=topic.id,
                    trainer=topic.trainer,
                    room=topic.room,
                    notes=topic.notes,
                    background_color=topic.background_color,
                ))
                cursor_by_day[key] = end
                topic_placement[topic.id] = absolute_day_index(week, day)
                topic_placement[source_by_id.get(topic.id, topic.id)] = absolute_day_index(week, day)
                placed = True
                break
            if placed:
                break
        if not placed:
            unscheduled.append(topic)

    for week in initialized_weeks:
        for day in available_days:
            key = (week, day)
            has_training = any(block.week == week and block.day == day and block.type == BlockType.training for block in scheduled)
            if not has_training or key in used_lunch:
                continue
            cursor = cursor_by_day[key]
            lunch_start = max(parse_time(settings.lunch_window_start), min(cursor, parse_time(settings.lunch_window_end)))
            if lunch_start + settings.lunch_minutes <= _latest_training_end(project, day):
                scheduled.append(ScheduleBlock(
                    id=f"lunch-{uuid4().hex[:8]}",
                    type=BlockType.lunch,
                    week=week,
                    day=day,
                    title="Mittagspause",
                    start=format_time(lunch_start),
                    end=format_time(lunch_start + settings.lunch_minutes),
                ))

    project.manual_weeks = sorted({week for week in project.manual_weeks if week > 0} | initialized_weeks)
    project.blocks = sorted(scheduled, key=lambda block: (block.week, DISPLAY_WEEKDAYS.index(block.day), block.start, block.type.value))
    project.unscheduled_topics = unscheduled
    project.warnings = validate_project(project)
    return project


def validate_project(project: TrainingProject) -> list[str]:
    settings = project.settings
    warnings: list[str] = []
    by_day: dict[tuple[int, str], list[ScheduleBlock]] = defaultdict(list)
    for block in project.blocks:
        by_day[(block.week, block.day)].append(block)
        if parse_time(block.start) < parse_time(settings.day_start) or parse_time(block.end) > parse_time(settings.day_end):
            warnings.append(f"Woche {block.week}, {block.day}: '{block.title}' liegt ausserhalb der Kernzeit.")
        if block.type == BlockType.break_block:
            duration = minutes_between(block.start, block.end)
            if duration < settings.break_min_minutes or duration > settings.break_max_minutes:
                warnings.append(f"Woche {block.week}, {block.day}: Pause '{block.title}' ist {duration} Minuten lang.")
        if block.type == BlockType.lunch and minutes_between(block.start, block.end) != settings.lunch_minutes:
            warnings.append(f"Woche {block.week}, {block.day}: Mittagspause ist nicht exakt {settings.lunch_minutes} Minuten lang.")
    training_by_topic = {block.topic_id: block for block in project.blocks if block.topic_id and block.type == BlockType.training}
    topics_by_id = {topic.id: topic for topic in project.topics}
    for topic in project.topics:
        if topic.depends_on and topic.id in training_by_topic and topic.depends_on in training_by_topic:
            current = training_by_topic[topic.id]
            dependency = training_by_topic[topic.depends_on]
            if absolute_day_index(current.week, current.day) <= absolute_day_index(dependency.week, dependency.day):
                dependency_title = topics_by_id[topic.depends_on].title if topic.depends_on in topics_by_id else topic.depends_on
                warnings.append(f"'{topic.title}' muss mindestens einen Tag nach '{dependency_title}' stattfinden.")
    for (week, day), blocks in by_day.items():
        ordered = sorted(blocks, key=lambda block: block.start)
        for index, block in enumerate(ordered):
            for other in ordered[index + 1:]:
                if is_overlap(block.start, block.end, other.start, other.end):
                    warnings.append(f"Woche {week}, {day}: '{block.title}' ueberlappt mit '{other.title}'.")
        if any(block.type == BlockType.training for block in blocks) and not any(block.type == BlockType.lunch for block in blocks):
            warnings.append(f"Woche {week}, {day}: Mittagspause fehlt.")
    if project.unscheduled_topics:
        missing = sum(topic.duration_minutes for topic in project.unscheduled_topics)
        warnings.append(f"Nicht eingeplante Schulungszeit: {missing} Minuten.")
    return warnings
