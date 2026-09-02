from io import BytesIO

from pypdf import PdfReader

from app.server.exporter import export_pdf
from app.server.models import ProjectFile, ScheduleBlock, TrainingProject


def sample_project() -> TrainingProject:
    return TrainingProject(
        title="Mehrtrainer Schulung",
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
    payload = ProjectFile(app_version="0.2.31", exported_at="2026-09-02T12:00:00+00:00", project=project)
    restored = ProjectFile.model_validate(payload.model_dump(mode="json"))
    assert restored.project.model_dump(mode="json") == project.model_dump(mode="json")
    assert restored.project.trainers == ["Trainer A", "Trainer B"]
    assert restored.project.manual_weeks == [1, 2]


def test_pdf_is_landscape_and_has_one_page_per_trainer_and_week():
    project = sample_project()
    reader = PdfReader(BytesIO(export_pdf(project)))
    assert len(reader.pages) == 4
    first = reader.pages[0]
    assert float(first.mediabox.width) > float(first.mediabox.height)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Trainer A" in text
    assert "Trainer B" in text
    assert "Thema A" in text
    assert "Thema B" in text
