from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZipFile

from pypdf import PdfReader

from app.server.customer_exchange import apply_customer_return, build_customer_package
from app.server.exporter import _appointment_participant_count, _service_day_count, export_pdf, planned_weeks
from app.server.main import _customer_export_filename, _project_export_filename
from app.server.models import CustomerPlanningReturn, ParticipantGroup, ProductLine, ProjectFile, ScheduleBlock, TrainingProject, TrainingTopic
from app.server.rules import minutes_between


def sample_project() -> TrainingProject:
    return TrainingProject(
        title="Mehrtrainer Schulung",
        customer_name="Musterklinik",
        location="Berlin",
        trainers=["Trainer A", "Trainer B"],
        start_date="2026-09-07",
        manual_weeks=[1, 2],
        blocks=[
            ScheduleBlock(
                id="block-a",
                type="training",
                week=1,
                day="Montag",
                title="Thema A",
                start="10:00",
                end="11:30",
                trainer="Trainer A",
                background_color="#dbeafe",
            ),
            ScheduleBlock(
                id="block-b",
                type="training",
                week=1,
                day="Montag",
                title="Thema B",
                start="10:00",
                end="11:30",
                trainer="Trainer B",
                background_color="#dcfce7",
            ),
        ],
    )


def test_project_file_roundtrip_preserves_planning_state():
    project = sample_project()
    payload = ProjectFile(app_version="0.2.32", exported_at="2026-09-02T12:00:00+00:00", project=project)
    restored = ProjectFile.model_validate(payload.model_dump(mode="json"))
    assert restored.project.model_dump(mode="json") == project.model_dump(mode="json")
    assert restored.project.trainers == ["Trainer A", "Trainer B"]
    assert restored.project.manual_weeks == [1, 2]




def test_service_days_count_trainer_days_for_parallel_trainers():
    project = sample_project()
    assert _service_day_count(project) == 2

def test_pdf_starts_with_overview_and_omits_weeks_without_training_blocks():
    project = sample_project()
    reader = PdfReader(BytesIO(export_pdf(project)))
    assert planned_weeks(project) == [1]
    assert len(reader.pages) == 4
    first = reader.pages[0]
    assert float(first.mediabox.width) > float(first.mediabox.height)
    first_text = first.extract_text() or ""
    schedule_text = reader.pages[1].extract_text() or ""
    assert "Schulungsthemen" in schedule_text
    assert "Datum" in schedule_text
    assert "Schulungsinhalt" in schedule_text
    assert "Anfang" in schedule_text
    assert "Ende" in schedule_text
    assert "Dauer" in schedule_text
    assert "Thema A" in schedule_text
    assert "10:00" in schedule_text
    assert "11:30" in schedule_text
    assert "1,5 h" in schedule_text
    assert "Planuebersicht" in first_text
    assert "Kunde" in first_text
    assert "Musterklinik" in first_text
    assert "Standort" in first_text
    assert "Berlin" in first_text
    assert "Kunde: Musterklinik" in first_text
    assert "Standort: Berlin" in first_text
    assert "Dienstleistungstage" in first_text
    assert "2 Tage" in first_text
    assert "Seite 1 · Uebersicht" not in first_text
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Trainer A" in text
    assert "Trainer B" in text
    assert "Thema A" in text
    assert "Thema B" in text


def test_server_project_export_filename_uses_customer_location_product_date_time():
    project = sample_project()
    filename = _project_export_filename(project, datetime(2026, 9, 2, 14, 23, tzinfo=timezone.utc))
    assert filename == "Musterklinik_Berlin_deepunity-pacs_2026-09-02_1423.json"




def test_customer_package_contains_single_self_contained_html(monkeypatch):
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    data = build_customer_package(sample_project())
    with ZipFile(BytesIO(data)) as archive:
        assert archive.namelist() == ["index.html"]
        html = archive.read("index.html").decode("utf-8")
        assert "data:image/png;base64," in html
        assert "Änderungen herunterladen" in html
        assert "window.SCHULUNGSPLAN_KUNDENPAKET = " in html
        assert "draggable" in html
        assert "<style>" in html
        assert "assets/style.css" not in html
        assert "assets/app.js" not in html
        assert "data.js" not in html
        assert "assets/dedalus.png" not in html
        assert "resize" not in html.lower()
        assert "Woche löschen" not in html


def _package_payload_from_html(html: str) -> dict:
    prefix = "window.SCHULUNGSPLAN_KUNDENPAKET = "
    start = html.index(prefix) + len(prefix)
    end = html.index(";</script>", start)
    return __import__("json").loads(html[start:end])


def _customer_return_from_package(data: bytes, moves: list[dict]) -> CustomerPlanningReturn:
    with ZipFile(BytesIO(data)) as archive:
        html = archive.read("index.html").decode("utf-8")
    package = _package_payload_from_html(html)
    return CustomerPlanningReturn.model_validate({
        "format": "schulungsplantool-customer-return",
        "schema_version": 1,
        "returned_at": "2026-09-04T12:00:00Z",
        "exchange": package["exchange"],
        "moves": moves,
    })




def test_customer_single_html_escapes_script_breakout_from_project_text(monkeypatch):
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.customer_name = "Kunde </script><script>alert(1)</script>"
    data = build_customer_package(project)
    with ZipFile(BytesIO(data)) as archive:
        html = archive.read("index.html").decode("utf-8")
    assert "Kunde </script><script>alert(1)</script>" not in html
    assert r"Kunde \u003c/script\u003e\u003cscript\u003ealert(1)\u003c/script\u003e" in html
    payload = _package_payload_from_html(html)
    assert payload["view"]["customer"] == project.customer_name

def test_customer_return_moves_training_block_and_preserves_duration(monkeypatch):
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    package = build_customer_package(project)
    payload = _customer_return_from_package(package, [{
        "block_id": "block-a", "week": 1, "day": "Dienstag", "trainer": "Trainer A", "start": "12:00", "end": "13:30"
    }])
    updated = apply_customer_return(payload)
    block = next(item for item in updated.blocks if item.id == "block-a")
    assert (block.day, block.start, block.end) == ("Dienstag", "12:00", "13:30")
    assert minutes_between(block.start, block.end) == 90


def test_customer_return_rejects_duration_changes(monkeypatch):
    import pytest
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    package = build_customer_package(sample_project())
    payload = _customer_return_from_package(package, [{
        "block_id": "block-a", "week": 1, "day": "Dienstag", "trainer": "Trainer A", "start": "12:00", "end": "14:00"
    }])
    with pytest.raises(ValueError, match="duration_changed"):
        apply_customer_return(payload)


def test_customer_return_rejects_tampered_signed_baseline(monkeypatch):
    import pytest
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    package = build_customer_package(sample_project())
    payload = _customer_return_from_package(package, [])
    payload.exchange.baseline.customer_name = "Manipuliert"
    with pytest.raises(ValueError, match="signature_invalid"):
        apply_customer_return(payload)


def test_customer_zip_filename_uses_project_metadata():
    filename = _customer_export_filename(sample_project(), datetime(2026, 9, 4, 12, 34, tzinfo=timezone.utc))
    assert filename == "Musterklinik_Berlin_deepunity-pacs_kundenplanung_2026-09-04_1234.zip"


def test_pdf_calendar_hides_participant_group_name_but_keeps_generated_split_label():
    project = sample_project()
    project.product_lines = [
        ProductLine(
            id="deepunity-pacs",
            name="DeepUnity PACS",
            participant_groups=[ParticipantGroup(id="webviewer", name="Webviewer", participant_count=30)],
        )
    ]
    project.blocks[0].title = "DU Viewer - Webviewer Gruppe 4/6"
    reader = PdfReader(BytesIO(export_pdf(project)))
    calendar_text = "\n".join(page.extract_text() or "" for page in reader.pages[1:])
    assert "DU Viewer" in calendar_text
    assert "Gruppe 4/6" in calendar_text
    assert "DU Viewer - Gruppe 4/6" not in calendar_text
    assert "DU Viewer - Webviewer Gruppe 4/6" not in calendar_text
    assert "10:00-11:30 · 1,5 h" in calendar_text




def test_pdf_omits_empty_trainer_week_calendar_page():
    project = TrainingProject(
        title="Leere Trainerwoche",
        customer_name="Musterklinik",
        location="Berlin",
        trainers=["Trainer A", "Trainer B"],
        start_date="2026-09-07",
        blocks=[
            ScheduleBlock(
                id="training-a",
                type="training",
                week=1,
                day="Dienstag",
                title="Thema A",
                start="09:00",
                end="10:00",
                trainer="Trainer A",
            ),
        ],
    )
    reader = PdfReader(BytesIO(export_pdf(project)))
    # Overview + chronological appointment page + one visible trainer/week calendar.
    assert len(reader.pages) == 3
    calendar_text = reader.pages[-1].extract_text() or ""
    assert "Trainer: Trainer A" in calendar_text
    assert "Trainer: Trainer B" not in calendar_text


def test_training_schedule_participant_count_respects_generated_group_remainder():
    project = TrainingProject(
        title="Teilnehmergruppen",
        product_id="deepunity-pacs",
        trainers=["Trainer A"],
        start_date="2026-09-07",
        product_lines=[
            ProductLine(
                id="deepunity-pacs",
                name="DeepUnity PACS",
                participant_groups=[ParticipantGroup(id="webviewer", name="Webviewer", participant_count=12)],
            )
        ],
        topics=[
            TrainingTopic(
                id="viewer",
                product_id="deepunity-pacs",
                title="DU Viewer",
                duration_minutes=30,
                participants_per_session=5,
                participant_group_ids=["webviewer"],
            )
        ],
        blocks=[
            ScheduleBlock(
                id="g1", type="training", week=1, day="Montag", title="DU Viewer - Webviewer Gruppe 1/3",
                start="09:00", end="09:30", trainer="Trainer A", topic_id="viewer-webviewer-gruppe-1", source_topic_id="viewer"
            ),
            ScheduleBlock(
                id="g3", type="training", week=1, day="Montag", title="DU Viewer - Webviewer Gruppe 3/3",
                start="10:00", end="10:30", trainer="Trainer A", topic_id="viewer-webviewer-gruppe-3", source_topic_id="viewer"
            ),
        ],
    )
    assert _appointment_participant_count(project, project.blocks[0]) == 5
    assert _appointment_participant_count(project, project.blocks[1]) == 2


def test_pdf_training_schedule_groups_by_trainer_and_shows_weekday_and_participants():
    project = TrainingProject(
        title="Trainergruppen", customer_name="Musterklinik", location="Berlin", product_id="deepunity-pacs",
        trainers=["Trainer A", "Trainer B"], start_date="2026-09-07",
        product_lines=[ProductLine(id="deepunity-pacs", name="DeepUnity PACS", participant_groups=[ParticipantGroup(id="mfa", name="MFA", participant_count=8)])],
        topics=[TrainingTopic(id="review", product_id="deepunity-pacs", title="Review MFA", duration_minutes=60, participants_per_session=8, participant_group_ids=["mfa"])],
        blocks=[
            ScheduleBlock(id="a", type="training", week=1, day="Montag", title="Review MFA - MFA", start="09:00", end="10:00", trainer="Trainer A", topic_id="review", source_topic_id="review"),
            ScheduleBlock(id="b", type="training", week=1, day="Dienstag", title="Review MFA - MFA", start="11:00", end="12:00", trainer="Trainer B", topic_id="review", source_topic_id="review"),
        ],
    )
    reader = PdfReader(BytesIO(export_pdf(project)))
    schedule_text = "\n".join(page.extract_text() or "" for page in reader.pages[1:3])
    assert "Teilnehmer" in schedule_text
    assert "Trainer: Trainer A" in schedule_text
    assert "Trainer: Trainer B" in schedule_text
    assert "Mo, 07.09.2026" in schedule_text
    assert "Di, 08.09.2026" in schedule_text
    assert "Review MFA" in schedule_text
    assert "8" in schedule_text


def test_v0310_pdf_training_topic_columns_put_times_after_date() -> None:
    project = sample_project()
    reader = PdfReader(BytesIO(export_pdf(project)))
    text = reader.pages[1].extract_text() or ""
    positions = [text.index(label) for label in ["Datum", "Anfang", "Ende", "Dauer", "Schulungsinhalt", "Gruppe", "Teilnehmer"]]
    assert positions == sorted(positions)


def test_v042_customer_return_can_move_arrival_and_preserves_duration(monkeypatch):
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.blocks.append(ScheduleBlock(
        id="arrival-a",
        type="arrival",
        week=1,
        day="Montag",
        title="Anreise / Eintreffen der Teilnehmer",
        start="08:30",
        end="09:30",
        trainer="Trainer A",
    ))
    package = build_customer_package(project)
    payload = _customer_return_from_package(package, [{
        "block_id": "arrival-a", "week": 1, "day": "Montag", "trainer": "Trainer A", "start": "08:45", "end": "09:45"
    }])
    updated = apply_customer_return(payload)
    block = next(item for item in updated.blocks if item.id == "arrival-a")
    assert (block.start, block.end) == ("08:45", "09:45")
    assert minutes_between(block.start, block.end) == 60


def test_v042_customer_return_rejects_arrival_duration_change(monkeypatch):
    import pytest
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.blocks.append(ScheduleBlock(
        id="arrival-a",
        type="arrival",
        week=1,
        day="Montag",
        title="Anreise / Eintreffen der Teilnehmer",
        start="08:30",
        end="09:30",
        trainer="Trainer A",
    ))
    package = build_customer_package(project)
    payload = _customer_return_from_package(package, [{
        "block_id": "arrival-a", "week": 1, "day": "Montag", "trainer": "Trainer A", "start": "08:30", "end": "09:45"
    }])
    with pytest.raises(ValueError, match="duration_changed"):
        apply_customer_return(payload)



def test_v044_customer_return_rejects_training_left_on_unavailable_day(monkeypatch):
    import pytest
    from app.server.models import TrainerWeekAvailability
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.trainer_availability = [
        TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Montag", "Dienstag", "Mittwoch", "Donnerstag"]),
        TrainerWeekAvailability(trainer="Trainer B", week=1, weekdays=["Montag", "Dienstag", "Mittwoch", "Donnerstag"]),
    ]
    training = next(block for block in project.blocks if block.type == "training" and block.trainer == "Trainer A")
    duration = minutes_between(training.start, training.end)
    package = build_customer_package(project)
    payload = _customer_return_from_package(package, [{
        "block_id": training.id,
        "week": training.week,
        "day": "Freitag",
        "trainer": training.trainer,
        "start": "09:00",
        "end": f"{(9 * 60 + duration) // 60:02d}:{(9 * 60 + duration) % 60:02d}",
    }])
    with pytest.raises(ValueError, match="trainer_day_unavailable"):
        apply_customer_return(payload)


def test_v044_customer_return_accepts_friday_when_trainer_is_available(monkeypatch):
    from app.server.models import TrainerWeekAvailability
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.trainer_availability = [
        TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Montag", "Freitag"]),
        TrainerWeekAvailability(trainer="Trainer B", week=1, weekdays=["Montag"]),
    ]
    training = next(block for block in project.blocks if block.type == "training" and block.trainer == "Trainer A")
    duration = minutes_between(training.start, training.end)
    package = build_customer_package(project)
    payload = _customer_return_from_package(package, [{
        "block_id": training.id,
        "week": 1,
        "day": "Freitag",
        "trainer": "Trainer A",
        "start": "09:00",
        "end": f"{(9 * 60 + duration) // 60:02d}:{(9 * 60 + duration) % 60:02d}",
    }])
    updated = apply_customer_return(payload)
    moved = next(block for block in updated.blocks if block.id == training.id)
    assert moved.day == "Freitag"


def test_v044_customer_package_rejects_internal_parked_training(monkeypatch):
    import pytest
    from app.server.models import TrainerWeekAvailability
    monkeypatch.setenv("CUSTOMER_EXCHANGE_SECRET", "test-secret")
    project = sample_project()
    project.trainer_availability = [
        TrainerWeekAvailability(trainer="Trainer A", week=1, weekdays=["Dienstag"]),
        TrainerWeekAvailability(trainer="Trainer B", week=1, weekdays=["Montag"]),
    ]
    with pytest.raises(ValueError, match="parked_training_blocks"):
        build_customer_package(project)
