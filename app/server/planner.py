from __future__ import annotations

from collections import defaultdict
from math import ceil
from uuid import uuid4

from .models import BlockType, ScheduleBlock, TrainingProject, TrainingTopic
from .rules import DISPLAY_WEEKDAYS, WEEKDAYS, format_time, is_overlap, minutes_between, parse_time, snap_minutes_to_quarter, snap_time_to_quarter


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

    for topic in sorted(
        topics,
        key=lambda item: (
            item.preferred_day or "",
            item.preferred_order or 999,
            item.priority,
            item.title.lower(),
        ),
    ):
        visit(topic)
    return result


def training_days(project: TrainingProject) -> list[str]:
    days = list(WEEKDAYS)
    if project.settings.friday_training_enabled:
        days.append("Freitag")
    return days


def project_trainers(project: TrainingProject) -> list[str]:
    trainers = [name.strip() for name in project.trainers if name.strip()]
    if not trainers and project.trainer.strip():
        trainers = [project.trainer.strip()]
    # A project without a named trainer remains planable. The empty name is
    # rendered as "Nicht zugewiesen" in the calendar.
    return trainers or [""]


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


def _add_fixed_blocks(project: TrainingProject, day: str, week: int, trainer: str) -> list[ScheduleBlock]:
    settings = project.settings
    blocks: list[ScheduleBlock] = []
    if day == "Montag" and settings.monday_arrival_enabled:
        blocks.append(ScheduleBlock(
            id=f"arrival-{uuid4().hex[:8]}",
            type=BlockType.arrival,
            week=week,
            day=day,
            title=settings.monday_arrival_label,
            start=snap_time_to_quarter(settings.monday_arrival_start),
            end=settings.monday_arrival_end,
            trainer=trainer,
        ))
    if day == "Donnerstag" and settings.thursday_departure_enabled and not settings.friday_training_enabled:
        blocks.append(ScheduleBlock(
            id=f"departure-{uuid4().hex[:8]}",
            type=BlockType.departure,
            week=week,
            day=day,
            title=settings.thursday_departure_label,
            start=snap_time_to_quarter(settings.thursday_departure_start),
            end=settings.thursday_departure_end,
            trainer=trainer,
        ))
    return blocks


def _latest_training_end(project: TrainingProject, day: str) -> int:
    settings = project.settings
    if day == "Donnerstag" and settings.thursday_departure_enabled and not settings.friday_training_enabled:
        return min(parse_time(settings.day_end), parse_time(settings.thursday_departure_start))
    return parse_time(settings.day_end)


def plan_project(project: TrainingProject) -> TrainingProject:
    settings = project.settings
    trainers = project_trainers(project)
    scheduled: list[ScheduleBlock] = []
    unscheduled: list[TrainingTopic] = []
    used_lunch: set[tuple[int, str, str]] = set()
    cursor_by_lane: dict[tuple[int, str, str], int] = {}
    initialized_weeks: set[int] = set()
    topic_placement: dict[str, int] = {}
    lane_has_training: set[tuple[int, str, str]] = set()
    available_days = training_days(project)

    def ensure_week(week: int) -> None:
        if week in initialized_weeks:
            return
        for day in available_days:
            for trainer in trainers:
                scheduled.extend(_add_fixed_blocks(project, day, week, trainer))
                cursor = snap_minutes_to_quarter(parse_time(settings.day_start), "ceil")
                if day == "Montag" and settings.monday_arrival_enabled:
                    cursor = snap_minutes_to_quarter(max(cursor, parse_time(settings.monday_arrival_end)), "ceil")
                cursor_by_lane[(week, day, trainer)] = cursor
        initialized_weeks.add(week)

    def candidate_for(topic: TrainingTopic, week: int, day: str, trainer: str) -> dict | None:
        key = (week, day, trainer)
        cursor = cursor_by_lane[key]
        day_end = _latest_training_end(project, day)
        lunch: tuple[int, int] | None = None

        if cursor >= parse_time(settings.lunch_window_start) and key not in used_lunch:
            lunch_start = snap_minutes_to_quarter(max(cursor, parse_time(settings.lunch_window_start)), "ceil")
            lunch_end = lunch_start + settings.lunch_minutes
            if lunch_end > day_end:
                return None
            lunch = (lunch_start, lunch_end)
            cursor = lunch_end

        break_slot: tuple[int, int] | None = None
        if key in lane_has_training:
            break_start = snap_minutes_to_quarter(cursor, "ceil")
            break_end = break_start + settings.break_preferred_minutes
            break_slot = (break_start, break_end)
            cursor = snap_minutes_to_quarter(break_end, "ceil")

        start = snap_minutes_to_quarter(cursor, "ceil")
        end = start + topic.duration_minutes
        if end > day_end:
            return None
        return {
            "week": week,
            "day": day,
            "trainer": trainer,
            "key": key,
            "lunch": lunch,
            "break": break_slot,
            "start": start,
            "end": end,
        }

    ensure_week(1)
    expanded_topics, source_by_id = expand_topic_sessions(project)

    for topic in sort_topics(expanded_topics):
        candidate_days = [topic.preferred_day] if topic.preferred_day in available_days else available_days
        earliest_day = topic_placement.get(topic.depends_on, -1) + 1 if topic.depends_on else 0
        chosen: dict | None = None

        for week in range(1, 13):
            ensure_week(week)
            candidates: list[dict] = []
            for day in candidate_days:
                if day is None or absolute_day_index(week, day) < earliest_day:
                    continue
                # All configured trainers are equally qualified for every topic.
                for trainer_index, trainer in enumerate(trainers):
                    candidate = candidate_for(topic, week, day, trainer)
                    if candidate is not None:
                        candidate["trainer_order"] = trainers.index(trainer) if trainer in trainers else trainer_index
                        candidates.append(candidate)
            if candidates:
                chosen = min(
                    candidates,
                    key=lambda item: (
                        absolute_day_index(item["week"], item["day"]),
                        item["start"],
                        item["trainer_order"],
                    ),
                )
                break

        if chosen is None:
            unscheduled.append(topic)
            continue

        key = chosen["key"]
        if chosen["lunch"] is not None:
            lunch_start, lunch_end = chosen["lunch"]
            scheduled.append(ScheduleBlock(
                id=f"lunch-{uuid4().hex[:8]}",
                type=BlockType.lunch,
                week=chosen["week"],
                day=chosen["day"],
                title="Mittagspause",
                start=format_time(lunch_start),
                end=format_time(lunch_end),
                trainer=chosen["trainer"],
            ))
            used_lunch.add(key)

        if chosen["break"] is not None:
            break_start, break_end = chosen["break"]
            scheduled.append(ScheduleBlock(
                id=f"break-{uuid4().hex[:8]}",
                type=BlockType.break_block,
                week=chosen["week"],
                day=chosen["day"],
                title="Pause",
                start=format_time(break_start),
                end=format_time(break_end),
                trainer=chosen["trainer"],
            ))

        scheduled.append(ScheduleBlock(
            id=f"training-{uuid4().hex[:8]}",
            type=BlockType.training,
            week=chosen["week"],
            day=chosen["day"],
            title=topic.title,
            description=topic.description,
            start=format_time(chosen["start"]),
            end=format_time(chosen["end"]),
            topic_id=topic.id,
            trainer=chosen["trainer"],
            room=topic.room,
            notes=topic.notes,
            background_color=topic.background_color,
        ))
        cursor_by_lane[key] = chosen["end"]
        lane_has_training.add(key)
        topic_placement[topic.id] = absolute_day_index(chosen["week"], chosen["day"])
        topic_placement[source_by_id.get(topic.id, topic.id)] = absolute_day_index(chosen["week"], chosen["day"])

    # Every active trainer/day gets a lunch break, even when all training took
    # place before the preferred lunch window. The break is not displayed in
    # the calendar, but remains part of validation and exports of raw data.
    for week in sorted(initialized_weeks):
        for day in available_days:
            for trainer in trainers:
                key = (week, day, trainer)
                if key not in lane_has_training or key in used_lunch:
                    continue
                cursor = cursor_by_lane[key]
                lunch_start = snap_minutes_to_quarter(max(parse_time(settings.lunch_window_start), min(cursor, parse_time(settings.lunch_window_end))), "ceil")
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
                        trainer=trainer,
                    ))
                    used_lunch.add(key)

    trainer_order = {name: index for index, name in enumerate(trainers)}
    training_weeks = {block.week for block in scheduled if block.type == BlockType.training}
    project.manual_weeks = sorted({week for week in project.manual_weeks if week > 0 and week in training_weeks})
    project.blocks = sorted(
        scheduled,
        key=lambda block: (
            block.week,
            DISPLAY_WEEKDAYS.index(block.day),
            trainer_order.get(block.trainer, len(trainer_order)),
            block.start,
            block.type.value,
        ),
    )
    project.unscheduled_topics = unscheduled
    project.warnings = validate_project(project)
    return project


def validate_project(project: TrainingProject) -> list[str]:
    settings = project.settings
    warnings: list[str] = []
    by_lane: dict[tuple[int, str, str], list[ScheduleBlock]] = defaultdict(list)
    for block in project.blocks:
        by_lane[(block.week, block.day, block.trainer)].append(block)
        trainer_suffix = f", Trainer {block.trainer}" if block.trainer else ""
        if parse_time(block.start) % 15 != 0:
            warnings.append(f"Woche {block.week}, {block.day}{trainer_suffix}: Startzeit von '{block.title}' liegt nicht im 15-Minuten-Raster.")
        if parse_time(block.start) < parse_time(settings.day_start) or parse_time(block.end) > parse_time(settings.day_end):
            warnings.append(f"Woche {block.week}, {block.day}{trainer_suffix}: '{block.title}' liegt ausserhalb der Kernzeit.")
        if block.type == BlockType.break_block:
            duration = minutes_between(block.start, block.end)
            if duration < settings.break_min_minutes or duration > settings.break_max_minutes:
                warnings.append(f"Woche {block.week}, {block.day}{trainer_suffix}: Pause '{block.title}' ist {duration} Minuten lang.")
        if block.type == BlockType.lunch and minutes_between(block.start, block.end) != settings.lunch_minutes:
            warnings.append(f"Woche {block.week}, {block.day}{trainer_suffix}: Mittagspause ist nicht exakt {settings.lunch_minutes} Minuten lang.")

    training_by_topic = {block.topic_id: block for block in project.blocks if block.topic_id and block.type == BlockType.training}
    topics_by_id = {topic.id: topic for topic in project.topics}
    for topic in project.topics:
        if topic.depends_on and topic.id in training_by_topic and topic.depends_on in training_by_topic:
            current = training_by_topic[topic.id]
            dependency = training_by_topic[topic.depends_on]
            if absolute_day_index(current.week, current.day) <= absolute_day_index(dependency.week, dependency.day):
                dependency_title = topics_by_id[topic.depends_on].title if topic.depends_on in topics_by_id else topic.depends_on
                warnings.append(f"'{topic.title}' muss mindestens einen Tag nach '{dependency_title}' stattfinden.")

    for (week, day, trainer), blocks in by_lane.items():
        trainer_suffix = f", Trainer {trainer}" if trainer else ""
        ordered = sorted(blocks, key=lambda block: block.start)
        for index, block in enumerate(ordered):
            for other in ordered[index + 1:]:
                if is_overlap(block.start, block.end, other.start, other.end):
                    warnings.append(f"Woche {week}, {day}{trainer_suffix}: '{block.title}' ueberlappt mit '{other.title}'.")
        if any(block.type == BlockType.training for block in blocks) and not any(block.type == BlockType.lunch for block in blocks):
            warnings.append(f"Woche {week}, {day}{trainer_suffix}: Mittagspause fehlt.")

    if project.unscheduled_topics:
        missing = sum(topic.duration_minutes for topic in project.unscheduled_topics)
        warnings.append(f"Nicht eingeplante Schulungszeit: {missing} Minuten.")
    return warnings
