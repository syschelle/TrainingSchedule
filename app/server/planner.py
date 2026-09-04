from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
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


def trainer_available_days(project: TrainingProject, trainer: str, week: int) -> set[str]:
    for availability in project.trainer_availability:
        if availability.trainer == trainer and int(availability.week) == int(week):
            return {day for day in availability.weekdays if day in DISPLAY_WEEKDAYS}
    return set(training_days(project))


def trainer_is_available(project: TrainingProject, trainer: str, week: int, day: str) -> bool:
    if day not in trainer_available_days(project, trainer, week):
        return False
    if project.start_date is not None:
        monday = project.start_date - timedelta(days=project.start_date.weekday())
        calendar_day = monday + timedelta(days=(int(week) - 1) * 7 + DISPLAY_WEEKDAYS.index(day))
        if calendar_day < project.start_date:
            return False
    return True


def absolute_day_index(week: int, day: str) -> int:
    return (week - 1) * len(DISPLAY_WEEKDAYS) + DISPLAY_WEEKDAYS.index(day)


def _split_session_topic(topic: TrainingTopic) -> list[TrainingTopic]:
    """Split one planned session into two sequential halves when enabled."""
    if not topic.split_enabled or topic.duration_minutes < 2:
        return [topic]

    first_minutes = topic.duration_minutes // 2
    second_minutes = topic.duration_minutes - first_minutes
    sequence_id = topic.id
    return [
        topic.model_copy(update={
            "id": f"{topic.id}-teil-1",
            "duration_minutes": first_minutes,
            "split_part": 1,
            "split_parts": 2,
            "split_sequence_id": sequence_id,
        }),
        topic.model_copy(update={
            "id": f"{topic.id}-teil-2",
            "duration_minutes": second_minutes,
            "split_part": 2,
            "split_parts": 2,
            "split_sequence_id": sequence_id,
        }),
    ]


def expand_topic_sessions(project: TrainingProject) -> tuple[list[TrainingTopic], dict[str, str]]:
    groups = {
        group.id: group
        for product in project.product_lines
        for group in product.participant_groups
    }
    expanded: list[TrainingTopic] = []
    source_by_id: dict[str, str] = {}

    def append_session(session_topic: TrainingTopic, source_id: str) -> None:
        for planned_topic in _split_session_topic(session_topic):
            expanded.append(planned_topic)
            source_by_id[planned_topic.id] = source_id

    for topic in project.topics:
        group_ids = topic.participant_group_ids or ([topic.participant_group_id] if topic.participant_group_id else [])
        max_participants = topic.participants_per_session or 0
        selected_groups = [groups[group_id] for group_id in group_ids if group_id in groups]
        if not selected_groups or max_participants <= 0:
            append_session(topic, topic.id)
            continue
        for group in selected_groups:
            if group.participant_count <= max_participants:
                session_topic = topic.model_copy(update={
                    "id": topic.id if len(selected_groups) == 1 else f"{topic.id}-{group.id}",
                    "title": f"{topic.title} - {group.name}",
                    "participant_group_id": group.id,
                })
                append_session(session_topic, topic.id)
                continue
            session_count = ceil(group.participant_count / max_participants)
            for index in range(1, session_count + 1):
                session_topic = topic.model_copy(update={
                    "id": topic.id if len(selected_groups) == 1 and index == 1 else f"{topic.id}-{group.id}-gruppe-{index}",
                    "title": f"{topic.title} - {group.name} Gruppe {index}/{session_count}",
                    "participant_group_id": group.id,
                    "sessions_required": session_count,
                })
                append_session(session_topic, topic.id)
    return expanded, source_by_id


def balanced_topic_order(
    project: TrainingProject,
    expanded_topics: list[TrainingTopic],
    source_by_id: dict[str, str],
) -> list[TrainingTopic]:
    """Spread participant sessions of different contents as evenly as possible.

    The old planner exhausted every generated session of one content before
    moving to the next content. That often created a day containing only one
    subject. Logical sessions are now merged proportionally: a content with
    many repetitions is distributed across the sequence while contents with
    fewer repetitions are kept for later slots instead of being consumed at
    the beginning. Split halves stay together as one logical session. A
    dependency becomes eligible only after all sessions of its prerequisite
    content have been taken.
    """
    source_topics = {topic.id: topic for topic in project.topics}
    source_order = [topic.id for topic in sort_topics(project.topics)]
    source_rank = {source_id: index for index, source_id in enumerate(source_order)}

    bundles_by_source: dict[str, list[list[TrainingTopic]]] = defaultdict(list)
    bundle_index: dict[tuple[str, str], list[TrainingTopic]] = {}
    for planned_topic in expanded_topics:
        source_id = source_by_id.get(planned_topic.id, planned_topic.id)
        bundle_id = planned_topic.split_sequence_id or planned_topic.id
        key = (source_id, bundle_id)
        bundle = bundle_index.get(key)
        if bundle is None:
            bundle = []
            bundle_index[key] = bundle
            bundles_by_source[source_id].append(bundle)
        bundle.append(planned_topic)

    for bundles in bundles_by_source.values():
        for bundle in bundles:
            bundle.sort(key=lambda item: item.split_part or 0)

    pending = {source_id: list(bundles) for source_id, bundles in bundles_by_source.items()}
    total_bundles = {source_id: len(bundles) for source_id, bundles in pending.items()}
    placed_bundles = {source_id: 0 for source_id in pending}
    ordered: list[TrainingTopic] = []

    while pending:
        eligible: list[str] = []
        for source_id in pending:
            dependency = source_topics.get(source_id).depends_on if source_id in source_topics else None
            if dependency and dependency in pending:
                continue
            eligible.append(source_id)

        if not eligible:
            # Defensive fallback for malformed/cyclic dependency data.
            eligible = [next(iter(pending))]

        # Each source has ideal positions at k/(n+1). Selecting the smallest
        # next position merges all source sequences proportionally. For 6
        # sessions of A and 2 of B this yields A,A,B,A,A,B,A,A instead of
        # A,B,A,B,A,A,A,A, so the smaller topic is not exhausted too early.
        source_id = min(
            eligible,
            key=lambda candidate: (
                (placed_bundles[candidate] + 1) / (total_bundles[candidate] + 1),
                source_rank.get(candidate, len(source_rank)),
            ),
        )
        ordered.extend(pending[source_id].pop(0))
        placed_bundles[source_id] += 1
        if not pending[source_id]:
            pending.pop(source_id, None)

    return ordered


def _trainer_week_days(project: TrainingProject, trainer: str, week: int) -> list[str]:
    allowed = trainer_available_days(project, trainer, week)
    return [day for day in DISPLAY_WEEKDAYS if day in allowed]


def _add_fixed_blocks(project: TrainingProject, day: str, week: int, trainer: str) -> list[ScheduleBlock]:
    settings = project.settings
    blocks: list[ScheduleBlock] = []
    week_days = _trainer_week_days(project, trainer, week)
    if not week_days:
        return blocks
    first_day, last_day = week_days[0], week_days[-1]
    if day == first_day and settings.monday_arrival_enabled:
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
    if day == last_day and settings.thursday_departure_enabled:
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


def _latest_training_end(project: TrainingProject, day: str, week: int, trainer: str) -> int:
    settings = project.settings
    week_days = _trainer_week_days(project, trainer, week)
    if week_days and day == week_days[-1] and settings.thursday_departure_enabled:
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
    split_placement: dict[str, dict] = {}
    lane_has_training: set[tuple[int, str, str]] = set()
    available_days = list(DISPLAY_WEEKDAYS)

    def ensure_week(week: int) -> None:
        if week in initialized_weeks:
            return
        for day in available_days:
            for trainer in trainers:
                scheduled.extend(_add_fixed_blocks(project, day, week, trainer))
                cursor = snap_minutes_to_quarter(parse_time(settings.day_start), "ceil")
                week_days = _trainer_week_days(project, trainer, week)
                if week_days and day == week_days[0] and settings.monday_arrival_enabled:
                    cursor = snap_minutes_to_quarter(max(cursor, parse_time(settings.monday_arrival_end)), "ceil")
                cursor_by_lane[(week, day, trainer)] = cursor
        initialized_weeks.add(week)

    def candidate_for(topic: TrainingTopic, week: int, day: str, trainer: str) -> dict | None:
        if not trainer_is_available(project, trainer, week, day):
            return None
        key = (week, day, trainer)
        cursor = cursor_by_lane[key]
        day_end = _latest_training_end(project, day, week, trainer)
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

    for topic in balanced_topic_order(project, expanded_topics, source_by_id):
        candidate_days = [topic.preferred_day] if topic.preferred_day in available_days else available_days
        earliest_day = topic_placement.get(topic.depends_on, -1) + 1 if topic.depends_on else 0
        previous_split = split_placement.get(topic.split_sequence_id or "") if topic.split_part and topic.split_part > 1 else None
        if topic.split_part and topic.split_part > 1 and previous_split is None:
            unscheduled.append(topic)
            continue
        if previous_split is not None:
            # The second half may continue on the same day, but never before
            # the first half and always with the same trainer.
            earliest_day = max(earliest_day, previous_split["day_index"])
        chosen: dict | None = None

        for week in range(1, 13):
            ensure_week(week)
            candidates: list[dict] = []
            for day in candidate_days:
                if day is None or absolute_day_index(week, day) < earliest_day:
                    continue
                # All configured trainers are equally qualified. For the
                # second half of a split session, keep the trainer of part 1 so
                # both halves remain one coherent participant session.
                for trainer_index, trainer in enumerate(trainers):
                    if previous_split is not None and trainer != previous_split["trainer"]:
                        continue
                    candidate = candidate_for(topic, week, day, trainer)
                    if candidate is not None and previous_split is not None:
                        candidate_day = absolute_day_index(week, day)
                        if candidate_day == previous_split["day_index"] and candidate["start"] < previous_split["end"]:
                            continue
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
            source_topic_id=source_by_id.get(topic.id, topic.id),
            split_part=topic.split_part,
            split_parts=topic.split_parts,
            trainer=chosen["trainer"],
            room=topic.room,
            notes=topic.notes,
            background_color=topic.background_color,
        ))
        cursor_by_lane[key] = chosen["end"]
        lane_has_training.add(key)
        placed_day_index = absolute_day_index(chosen["week"], chosen["day"])
        topic_placement[topic.id] = placed_day_index
        topic_placement[source_by_id.get(topic.id, topic.id)] = placed_day_index
        if topic.split_sequence_id:
            split_placement[topic.split_sequence_id] = {
                "day_index": placed_day_index,
                "end": chosen["end"],
                "trainer": chosen["trainer"],
            }

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
                if lunch_end <= _latest_training_end(project, day, week, trainer):
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

    active_trainer_weeks = {(block.week, block.trainer) for block in scheduled if block.type == BlockType.training}
    scheduled = [
        block for block in scheduled
        if block.type not in {BlockType.arrival, BlockType.departure}
        or (block.week, block.trainer) in active_trainer_weeks
    ]

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

    training_by_source: dict[str, list[ScheduleBlock]] = defaultdict(list)
    for block in project.blocks:
        if block.type != BlockType.training:
            continue
        source_id = block.source_topic_id or block.topic_id
        if source_id:
            training_by_source[source_id].append(block)
    topics_by_id = {topic.id: topic for topic in project.topics}
    for topic in project.topics:
        if topic.depends_on and topic.id in training_by_source and topic.depends_on in training_by_source:
            current = min(training_by_source[topic.id], key=lambda block: (absolute_day_index(block.week, block.day), block.start))
            dependency = max(training_by_source[topic.depends_on], key=lambda block: (absolute_day_index(block.week, block.day), block.end))
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
