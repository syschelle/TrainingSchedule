from app.server.models import ParticipantGroup, PlanningSettings, ProductLine, ScheduleBlock, TrainingProject, TrainingTopic
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


def test_friday_is_only_used_when_enabled():
    project = TrainingProject(topics=[topic(f"Thema {index}", 240) for index in range(1, 6)])
    planned_without_friday = plan_project(project)
    assert not any(block.type == "training" and block.day == "Freitag" for block in planned_without_friday.blocks)

    project.settings.friday_training_enabled = True
    planned_with_friday = plan_project(project)
    assert any(block.type == "training" and block.day == "Freitag" for block in planned_with_friday.blocks)


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
