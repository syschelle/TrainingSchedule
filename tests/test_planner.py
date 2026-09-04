from app.server.models import ParticipantGroup, PlanningSettings, ProductLine, ScheduleBlock, TrainerWeekAvailability, TrainingProject, TrainingTopic
from app.server.planner import plan_project, validate_project


def topic(title: str, minutes: int, priority: int = 3) -> TrainingTopic:
    return TrainingTopic(id=title.lower().replace(" ", "-"), title=title, duration_minutes=minutes, priority=priority)


def test_monday_arrival_and_thursday_departure_are_reserved():
    project = TrainingProject(topics=[topic("Einführung", 90), topic("Systemübersicht", 120), topic("Administration", 90)])
    planned = plan_project(project)
    assert any(block.type == "arrival" and block.day == "Montag" for block in planned.blocks)
    assert any(block.type == "departure" and block.day == "Donnerstag" for block in planned.blocks)
    assert not any(block.type == "training" and block.day == "Montag" and block.start < "10:00" for block in planned.blocks)


def test_breaks_and_lunch_are_valid():
    project = TrainingProject(topics=[topic("A", 90), topic("B", 90), topic("C", 90)])
    planned = plan_project(project)
    break_blocks = [block for block in planned.blocks if block.type == "break"]
    assert break_blocks
    assert all(20 <= (int(block.end[:2]) * 60 + int(block.end[3:]) - int(block.start[:2]) * 60 - int(block.start[3:])) <= 30 for block in break_blocks)
    assert any(block.type == "lunch" for block in planned.blocks)
    assert not [warning for warning in planned.warnings if "Mittagspause ist nicht exakt" in warning]


def test_many_hours_continue_into_following_weeks():
    project = TrainingProject(topics=[topic(f"Thema {index}", 360) for index in range(1, 8)])
    planned = plan_project(project)
    assert not planned.unscheduled_topics
    assert max(block.week for block in planned.blocks) > 1


def test_empty_manual_weeks_are_removed_from_new_automatic_plan():
    project = TrainingProject(manual_weeks=[1, 3], topics=[topic("Start", 45)])
    planned = plan_project(project)
    assert 1 in planned.manual_weeks
    assert 3 not in planned.manual_weeks


def test_overlap_validation():
    project = TrainingProject()
    project.blocks = [
        ScheduleBlock(id="a", type="training", day="Dienstag", title="A", start="10:00", end="11:00"),
        ScheduleBlock(id="b", type="training", day="Dienstag", title="B", start="10:30", end="11:30"),
    ]
    warnings = validate_project(project)
    assert any("ueberlappt" in warning for warning in warnings)


def test_custom_settings_are_used():
    project = TrainingProject(
        settings=PlanningSettings(day_start="09:00", monday_arrival_start="09:00", monday_arrival_end="09:30"),
        topics=[topic("Start", 45)],
    )
    planned = plan_project(project)
    training = next(block for block in planned.blocks if block.type == "training")
    assert training.start >= "09:30"


def test_training_background_color_is_copied_to_calendar_block():
    project = TrainingProject(topics=[TrainingTopic(id="farbe", title="Farbe", duration_minutes=45, background_color="#abcdef")])
    planned = plan_project(project)
    training = next(block for block in planned.blocks if block.type == "training")
    assert training.background_color == "#abcdef"


def test_friday_is_only_used_when_explicitly_available_for_trainer():
    default_project = TrainingProject(trainers=["Trainer A"], topics=[topic("Standard", 60)])
    default_planned = plan_project(default_project)
    assert not any(block.type == "training" and block.day == "Freitag" for block in default_planned.blocks)

    friday_project = TrainingProject(
        trainers=["Trainer A"],
        trainer_availability=[TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Freitag"])],
        topics=[topic("Freitag", 60)],
    )
    friday_planned = plan_project(friday_project)
    training = next(block for block in friday_planned.blocks if block.type == "training")
    assert training.week == 1
    assert training.day == "Freitag"


def test_dependencies_need_previous_day():
    project = TrainingProject(topics=[
        TrainingTopic(id="basic", title="Basic", duration_minutes=60, priority=1),
        TrainingTopic(id="advanced", title="Advanced", duration_minutes=60, priority=2, depends_on="basic"),
    ])
    planned = plan_project(project)
    by_topic = {block.topic_id: block for block in planned.blocks if block.type == "training"}
    assert by_topic["advanced"].day != by_topic["basic"].day


def test_topics_split_by_participant_group_capacity():
    project = TrainingProject(
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[ParticipantGroup(id="radiologen", name="Radiologen", participant_count=18)],
            )
        ],
        topics=[
            TrainingTopic(
                id="diagnost",
                title="Diagnost",
                duration_minutes=45,
                participant_group_ids=["radiologen"],
                participants_per_session=8,
            )
        ],
    )
    planned = plan_project(project)
    training_blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(training_blocks) == 3
    assert all("Gruppe" in block.title for block in training_blocks)


def test_topics_split_by_multiple_assigned_participant_groups():
    project = TrainingProject(
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[
                    ParticipantGroup(id="radiologen", name="Radiologen", participant_count=18),
                    ParticipantGroup(id="mfa", name="MFA", participant_count=5),
                ],
            )
        ],
        topics=[
            TrainingTopic(
                id="diagnost",
                title="Diagnost",
                duration_minutes=45,
                participant_group_ids=["radiologen", "mfa"],
                participants_per_session=8,
            )
        ],
    )
    planned = plan_project(project)
    training_blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(training_blocks) == 4
    assert any("MFA" in block.title for block in training_blocks)
    assert sum("Radiologen" in block.title for block in training_blocks) == 3


def test_project_supports_product_lines_and_participant_groups():
    project = TrainingProject(
        customer_name="Klinikum Beispiel",
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[
                    ParticipantGroup(id="radiologen", name="Radiologen", participant_count=12),
                    ParticipantGroup(id="admin", name="Administratoren", participant_count=3),
                ],
            ),
            ProductLine(id="future-product", name="Weiteres Produkt"),
        ],
    )
    assert project.product_lines[0].participant_groups[0].name == "Radiologen"
    assert project.product_lines[1].id == "future-product"


def test_service_calculation_can_skip_customer_data():
    project = TrainingProject(project_mode="service_calculation", customer_data_required=False)
    assert project.customer_data_required is False
    assert project.project_mode == "service_calculation"


def test_multiple_trainers_can_run_training_in_parallel():
    project = TrainingProject(
        trainers=["Trainer A", "Trainer B"],
        topics=[topic("Parallel A", 180), topic("Parallel B", 180)],
    )
    planned = plan_project(project)
    training_blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(training_blocks) == 2
    assert {block.trainer for block in training_blocks} == {"Trainer A", "Trainer B"}
    assert {block.day for block in training_blocks} == {"Montag"}
    assert {block.start for block in training_blocks} == {"10:00"}


def test_overlaps_are_checked_per_trainer_lane():
    project = TrainingProject(trainers=["Trainer A", "Trainer B"])
    project.blocks = [
        ScheduleBlock(id="a", type="training", day="Dienstag", title="A", start="10:00", end="11:00", trainer="Trainer A"),
        ScheduleBlock(id="b", type="training", day="Dienstag", title="B", start="10:00", end="11:00", trainer="Trainer B"),
    ]
    warnings = validate_project(project)
    assert not any("ueberlappt" in warning for warning in warnings)


def test_topic_trainer_legacy_value_does_not_restrict_equal_trainers():
    project = TrainingProject(
        trainers=["Trainer A", "Trainer B"],
        topics=[
            TrainingTopic(id="legacy-a", title="Legacy A", duration_minutes=180, trainer="Trainer A"),
            TrainingTopic(id="legacy-b", title="Legacy B", duration_minutes=180, trainer="Trainer A"),
        ],
    )
    planned = plan_project(project)
    training_blocks = [block for block in planned.blocks if block.type == "training"]
    assert {block.trainer for block in training_blocks} == {"Trainer A", "Trainer B"}


def test_automatic_training_starts_are_always_on_quarter_hours():
    project = TrainingProject(
        topics=[
            topic("A", 95),
            topic("B", 65),
            topic("C", 50),
            topic("D", 80),
        ]
    )
    planned = plan_project(project)
    starts = [block.start for block in planned.blocks]
    assert starts
    assert all(int(value.split(":")[1]) % 15 == 0 for value in starts)


def test_validation_flags_non_quarter_hour_start():
    project = TrainingProject()
    project.blocks = [
        ScheduleBlock(id="odd", type="training", day="Dienstag", title="Odd", start="15:05", end="16:05")
    ]
    warnings = validate_project(project)
    assert any("15-Minuten-Raster" in warning for warning in warnings)


def test_training_topic_can_be_split_into_two_sequential_halves():
    project = TrainingProject(
        trainers=["Trainer A", "Trainer B"],
        topics=[TrainingTopic(id="lang", title="Lange Schulung", duration_minutes=180, split_enabled=True)],
    )
    planned = plan_project(project)
    blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(blocks) == 2
    assert [block.split_part for block in blocks] == [1, 2]
    assert all(block.split_parts == 2 for block in blocks)
    assert all(block.source_topic_id == "lang" for block in blocks)
    assert all(block.trainer == blocks[0].trainer for block in blocks)
    durations = [
        (int(block.end[:2]) * 60 + int(block.end[3:])) - (int(block.start[:2]) * 60 + int(block.start[3:]))
        for block in blocks
    ]
    assert sum(durations) == 180
    assert abs(durations[0] - durations[1]) <= 1


def test_training_topic_split_can_be_disabled():
    project = TrainingProject(
        topics=[TrainingTopic(id="lang", title="Lange Schulung", duration_minutes=180, split_enabled=False)]
    )
    planned = plan_project(project)
    blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(blocks) == 1
    assert blocks[0].source_topic_id == "lang"
    assert blocks[0].split_part is None


def test_participant_sessions_are_split_after_group_expansion():
    project = TrainingProject(
        trainers=["Trainer A"],
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[ParticipantGroup(id="radiologen", name="Radiologen", participant_count=18)],
            )
        ],
        topics=[
            TrainingTopic(
                id="diagnost",
                title="Diagnost",
                duration_minutes=90,
                participant_group_ids=["radiologen"],
                participants_per_session=8,
                split_enabled=True,
            )
        ],
    )
    planned = plan_project(project)
    blocks = [block for block in planned.blocks if block.type == "training"]
    assert len(blocks) == 6
    assert all(block.source_topic_id == "diagnost" for block in blocks)
    assert sum(block.split_part == 1 for block in blocks) == 3
    assert sum(block.split_part == 2 for block in blocks) == 3
    assert sum("Gruppe" in block.title for block in blocks) == 6


def test_planner_interleaves_generated_sessions_from_different_topics():
    project = TrainingProject(
        trainers=["Trainer A"],
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[
                    ParticipantGroup(id="group-a", name="Gruppe A", participant_count=4),
                    ParticipantGroup(id="group-b", name="Gruppe B", participant_count=4),
                ],
            )
        ],
        topics=[
            TrainingTopic(
                id="topic-a",
                title="Thema A",
                duration_minutes=90,
                participant_group_ids=["group-a"],
                participants_per_session=1,
            ),
            TrainingTopic(
                id="topic-b",
                title="Thema B",
                duration_minutes=90,
                participant_group_ids=["group-b"],
                participants_per_session=1,
            ),
        ],
    )
    planned = plan_project(project)
    monday_topics = {
        block.source_topic_id
        for block in planned.blocks
        if block.type == "training" and block.day == "Montag"
    }
    tuesday_topics = {
        block.source_topic_id
        for block in planned.blocks
        if block.type == "training" and block.day == "Dienstag"
    }
    assert monday_topics == {"topic-a", "topic-b"}
    assert tuesday_topics == {"topic-a", "topic-b"}


def test_project_specific_topic_duration_is_used_by_planner():
    project = TrainingProject(
        topics=[
            TrainingTopic(
                id="custom-duration",
                title="Projektzeit",
                duration_minutes=135,
                catalog_duration_minutes=120,
                duration_overridden=True,
            )
        ]
    )
    planned = plan_project(project)
    block = next(block for block in planned.blocks if block.type == "training")
    start_minutes = int(block.start[:2]) * 60 + int(block.start[3:])
    end_minutes = int(block.end[:2]) * 60 + int(block.end[3:])
    assert end_minutes - start_minutes == 135


def test_planner_spreads_smaller_topic_across_days_instead_of_exhausting_it_early():
    project = TrainingProject(
        trainers=["Trainer A"],
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[
                    ParticipantGroup(id="many", name="Viele", participant_count=6),
                    ParticipantGroup(id="few", name="Wenige", participant_count=2),
                ],
            )
        ],
        topics=[
            TrainingTopic(
                id="many-topic",
                title="Haeufiges Thema",
                duration_minutes=90,
                participant_group_ids=["many"],
                participants_per_session=1,
            ),
            TrainingTopic(
                id="few-topic",
                title="Selteneres Thema",
                duration_minutes=90,
                participant_group_ids=["few"],
                participants_per_session=1,
            ),
        ],
    )
    planned = plan_project(project)
    few_days = [
        block.day
        for block in planned.blocks
        if block.type == "training" and block.source_topic_id == "few-topic"
    ]
    assert few_days == ["Montag", "Dienstag"]



def test_v043_trainer_specific_availability_is_respected():
    project = TrainingProject(
        trainers=["Trainer A", "Trainer B"],
        trainer_availability=[
            TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Dienstag"]),
            TrainerWeekAvailability(trainer="Trainer B", week=1, weekdays=["Mittwoch"]),
        ],
        topics=[topic("A", 120), topic("B", 120)],
    )
    planned = plan_project(project)
    training = [block for block in planned.blocks if block.type == "training" and block.week == 1]
    assert training
    assert all(
        (block.trainer == "Trainer A" and block.day == "Dienstag")
        or (block.trainer == "Trainer B" and block.day == "Mittwoch")
        for block in training
    )


def test_v043_explicit_friday_availability_overrides_default_friday_setting():
    project = TrainingProject(
        trainers=["Trainer A"],
        trainer_availability=[TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Freitag"])],
        topics=[topic("Freitag", 60)],
    )
    planned = plan_project(project)
    training = next(block for block in planned.blocks if block.type == "training")
    assert training.week == 1
    assert training.day == "Freitag"


def test_v043_arrival_and_departure_follow_first_and_last_enabled_training_day():
    project = TrainingProject(
        trainers=["Trainer A"],
        trainer_availability=[TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Dienstag", "Mittwoch"])],
        topics=[topic("A", 60)],
    )
    planned = plan_project(project)
    arrival = next(block for block in planned.blocks if block.type == "arrival" and block.week == 1)
    departure = next(block for block in planned.blocks if block.type == "departure" and block.week == 1)
    assert arrival.day == "Dienstag"
    assert departure.day == "Mittwoch"
    assert all(block.day in {"Dienstag", "Mittwoch"} for block in planned.blocks if block.type == "training" and block.week == 1)


def test_v043_first_week_never_plans_before_project_start_date():
    project = TrainingProject(
        start_date="2026-09-08",  # Tuesday
        trainers=["Trainer A"],
        trainer_availability=[TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Montag", "Dienstag", "Mittwoch"])],
        topics=[topic("Startdatum", 60)],
    )
    planned = plan_project(project)
    training = next(block for block in planned.blocks if block.type == "training")
    assert training.day != "Montag"


def test_v043_unused_trainer_week_does_not_keep_arrival_or_departure_only():
    project = TrainingProject(
        trainers=["Trainer A", "Trainer B"],
        trainer_availability=[
            TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Dienstag"]),
            TrainerWeekAvailability(trainer="Trainer B", week=1, weekdays=["Donnerstag", "Freitag"]),
        ],
        topics=[topic("A", 60)],
    )
    planned = plan_project(project)
    trainers_with_training = {block.trainer for block in planned.blocks if block.type == "training"}
    for block in planned.blocks:
        if block.type in {"arrival", "departure"}:
            assert block.trainer in trainers_with_training


def test_v044_validation_marks_training_on_unavailable_trainer_day_as_parked():
    project = TrainingProject(
        trainers=["Trainer A"],
        trainer_availability=[TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Dienstag"])],
        blocks=[ScheduleBlock(id="parked", type="training", week=1, day="Montag", title="Parken", start="10:00", end="11:00", trainer="Trainer A")],
    )
    warnings = validate_project(project)
    assert any("nur geparkt" in warning and "nicht verfügbar" in warning for warning in warnings)


def test_v046_final_lunch_never_overlaps_long_training_block():
    project = TrainingProject(
        trainers=["Trainer A"],
        topics=[topic("Langer Block", 360)],
    )
    planned = plan_project(project)
    training = next(block for block in planned.blocks if block.type == "training")
    lunches = [block for block in planned.blocks if block.type == "lunch" and block.week == training.week and block.day == training.day and block.trainer == training.trainer]
    assert not any(block.start < training.end and training.start < block.end for block in lunches)
    assert any("Mittagspause fehlt" in warning for warning in planned.warnings)
