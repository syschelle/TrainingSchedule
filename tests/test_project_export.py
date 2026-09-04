from datetime import datetime, timezone
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

from pypdf import PdfReader

from app.server.exporter import _service_day_count, export_pdf, export_xlsx, planned_weeks
from app.server.main import _project_export_filename
from app.server.models import ParticipantGroup, ProductLine, ProjectFile, ScheduleBlock, TrainingProject


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



def _xlsx_sheet_names(data: bytes) -> list[str]:
    with ZipFile(BytesIO(data)) as archive:
        root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return [sheet.attrib["name"] for sheet in root.findall("main:sheets/main:sheet", namespace)]


def _xlsx_shared_strings(data: bytes) -> str:
    with ZipFile(BytesIO(data)) as archive:
        return archive.read("xl/sharedStrings.xml").decode("utf-8")


def test_xlsx_mirrors_pdf_structure_with_overview_and_week_sheets():
    project = sample_project()
    data = export_xlsx(project)
    assert _xlsx_sheet_names(data) == ["Übersicht", "Woche 1"]
    shared = _xlsx_shared_strings(data)
    assert "Planübersicht" in shared
    assert "Musterklinik" in shared
    assert "Dienstleistungstage" in shared
    assert "Trainer A" in shared
    assert "Trainer B" in shared
    assert "Montag" in shared
    assert "Thema A" in shared
    assert "Thema B" in shared


def test_xlsx_creates_one_worksheet_per_planned_week_only():
    project = sample_project()
    project.blocks.append(ScheduleBlock(
        id="block-c",
        type="training",
        week=2,
        day="Dienstag",
        title="Thema C",
        start="09:00",
        end="10:00",
        trainer="Trainer A",
        background_color="#fef3c7",
    ))
    data = export_xlsx(project)
    assert _xlsx_sheet_names(data) == ["Übersicht", "Woche 1", "Woche 2"]
    shared = _xlsx_shared_strings(data)
    assert "Woche 2" in shared
    assert "Thema C" in shared
