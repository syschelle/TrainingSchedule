from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.server.content_db import (
    Base, DEFAULT_MASTER_DATA_BLOCKS, create_master_data_block, delete_master_data_block,
    ensure_master_data_block_columns, list_master_data_blocks, seed_database, update_master_data_block,
)
from app.server.models import TrainingProject


def test_default_master_data_collection_contains_numbered_17_blocks():
    assert len(DEFAULT_MASTER_DATA_BLOCKS) == 17
    assert [item["sort_order"] for item in DEFAULT_MASTER_DATA_BLOCKS] == list(range(1, 18))
    assert DEFAULT_MASTER_DATA_BLOCKS[0]["title"] == "Übersicht Installation DeepUnity Client"
    assert DEFAULT_MASTER_DATA_BLOCKS[-1]["title"] == "Fragen und Offene Punkte"
    assert all(item["product_id"] == "deepunity-pacs" for item in DEFAULT_MASTER_DATA_BLOCKS)


def test_master_data_blocks_are_extendable_reorderable_and_deletable():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        created = create_master_data_block(session, "deepunity-pacs", "Zusätzlicher Projektpunkt")
        assert created["sort_order"] == 18
        moved = update_master_data_block(session, created["id"], {
            "title": created["title"], "sort_order": 2, "active": True,
            "background_color": "#abcdef", "markdown_content": "- Neuer Punkt",
            "answer_type": "select", "answer_options": ["Online", "Präsenz", "Hybrid", "Online"],
            "resource_links": [
                {"title": "Dokumentation", "url": "https://example.org/docs", "description": "Herstellerdokumentation"},
                {"title": "Unsicher", "url": "javascript:alert(1)", "description": "wird verworfen"},
            ],
        })
        assert moved is not None
        assert moved["sort_order"] == 2
        assert moved["answer_type"] == "select"
        assert moved["answer_options"] == ["Online", "Präsenz", "Hybrid"]
        assert moved["resource_links"] == [{"title": "Dokumentation", "url": "https://example.org/docs", "description": "Herstellerdokumentation"}]
        items = list_master_data_blocks(session, "deepunity-pacs")
        assert [item["sort_order"] for item in items] == list(range(1, 19))
        assert items[1]["id"] == created["id"]
        assert delete_master_data_block(session, created["id"]) is True
        items = list_master_data_blocks(session, "deepunity-pacs")
        assert [item["sort_order"] for item in items] == list(range(1, 18))


def test_seed_does_not_overwrite_edited_master_data_block():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        first = list_master_data_blocks(session, "deepunity-pacs")[0]
        updated = update_master_data_block(session, first["id"], {
            "title": "Eigener Titel", "sort_order": 1, "active": False,
            "background_color": "#123456", "markdown_content": "- Eigener Inhalt",
        })
        assert updated["title"] == "Eigener Titel"
        seed_database(session)
        persisted = list_master_data_blocks(session, "deepunity-pacs")[0]
        assert persisted["title"] == "Eigener Titel"
        assert persisted["active"] is False
        assert persisted["markdown_content"] == "- Eigener Inhalt"


def test_project_master_data_collection_is_backward_compatible_and_serializable():
    legacy = TrainingProject.model_validate({"title": "Altprojekt"})
    assert legacy.master_data_collection_enabled is False
    assert legacy.master_data_blocks == []
    project = TrainingProject.model_validate({
        "title": "Mit Erhebung", "master_data_collection_enabled": True,
        "master_data_blocks": [{
            "id": "master-test", "sort_order": 1, "title": "Test",
            "markdown_content": "- Punkt", "completed": True, "notes": "Ergebnis",
        }],
    })
    dumped = project.model_dump(mode="json")
    assert dumped["master_data_collection_enabled"] is True
    assert dumped["master_data_blocks"][0]["completed"] is True
    assert dumped["master_data_blocks"][0]["notes"] == "Ergebnis"


def test_legacy_master_data_project_mode_becomes_training_project_with_collection_enabled():
    project = TrainingProject.model_validate({
        "title": "Erhebung",
        "project_mode": "master_data_collection",
        "master_data_collection_enabled": False,
    })
    assert project.project_mode == "training_plan"
    assert project.master_data_collection_enabled is True
    assert project.customer_data_required is True


def test_master_data_collection_appointment_metadata_is_serializable():
    project = TrainingProject.model_validate({
        "project_mode": "training_plan",
        "master_data_collection_enabled": True,
        "project_number": "P-4711",
        "master_data_collection_date": "2026-11-10",
        "master_data_collection_start_time": "09:30",
        "master_data_collection_duration_minutes": 240,
        "master_data_collection_dedalus_participants": "A. Dedalus",
        "master_data_collection_customer_participants": "K. Kunde",
        "master_data_collection_completed": True,
    })
    dumped = project.model_dump(mode="json")
    assert dumped["project_number"] == "P-4711"
    assert dumped["master_data_collection_date"] == "2026-11-10"
    assert dumped["master_data_collection_start_time"] == "09:30"
    assert dumped["master_data_collection_duration_minutes"] == 240
    assert dumped["master_data_collection_completed"] is True


def test_project_master_data_block_keeps_structured_answer_snapshot():
    project = TrainingProject.model_validate({
        "master_data_collection_enabled": True,
        "master_data_blocks": [{
            "id": "master-auth", "sort_order": 3, "title": "Authentifizierung",
            "markdown_content": "- Verfahren abstimmen",
            "answer_type": "checkboxes",
            "answer_options": ["DeepUnity Server", "LDAP", "ORBIS"],
            "answer_selected": ["LDAP", "ORBIS"],
            "resource_links": [
                {"title": "Authentifizierung", "url": "https://example.org/auth", "description": "Weitere Informationen"},
                {"title": "Rollen", "url": "https://example.org/roles", "description": ""},
            ],
            "answer_text": "",
            "completed": True,
            "notes": "Kunde prüft Gruppenstruktur",
        }],
    })
    dumped = project.model_dump(mode="json")["master_data_blocks"][0]
    assert dumped["answer_type"] == "checkboxes"
    assert dumped["answer_options"] == ["DeepUnity Server", "LDAP", "ORBIS"]
    assert dumped["answer_selected"] == ["LDAP", "ORBIS"]
    assert dumped["resource_links"] == [
        {"title": "Authentifizierung", "url": "https://example.org/auth", "description": "Weitere Informationen"},
        {"title": "Rollen", "url": "https://example.org/roles", "description": ""},
    ]
    assert dumped["completed"] is True
    assert dumped["notes"] == "Kunde prüft Gruppenstruktur"


def test_old_project_master_data_blocks_default_to_no_structured_answer():
    project = TrainingProject.model_validate({
        "master_data_blocks": [{
            "id": "legacy", "sort_order": 1, "title": "Alt", "markdown_content": "Text"
        }]
    })
    block = project.master_data_blocks[0]
    assert block.answer_type == "none"
    assert block.answer_options == []
    assert block.answer_text == ""
    assert block.answer_selected == []
    assert block.resource_links == []


def test_master_data_answer_columns_are_added_to_existing_database(monkeypatch):
    import app.server.content_db as content_db

    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE master_data_blocks (id VARCHAR(120) PRIMARY KEY, product_id VARCHAR(120) NOT NULL, sort_order INTEGER NOT NULL, title VARCHAR(240) NOT NULL, active BOOLEAN NOT NULL, background_color VARCHAR(20) NOT NULL, markdown_content TEXT NOT NULL)"))
    monkeypatch.setattr(content_db, "engine", engine)
    ensure_master_data_block_columns()
    columns = {column["name"] for column in inspect(engine).get_columns("master_data_blocks")}
    assert "answer_type" in columns
    assert "answer_options" in columns
    assert "resource_links" in columns


def test_master_data_resource_links_reject_non_http_schemes():
    from pydantic import ValidationError
    from app.server.models import MasterDataBlockUpdate

    try:
        MasterDataBlockUpdate.model_validate({
            "title": "Test",
            "sort_order": 1,
            "resource_links": [{"title": "Bad", "url": "javascript:alert(1)"}],
        })
    except ValidationError:
        pass
    else:
        raise AssertionError("javascript: resource link must be rejected")


def test_master_data_resource_links_accept_multiple_optional_links():
    from app.server.models import MasterDataBlockUpdate

    block = MasterDataBlockUpdate.model_validate({
        "title": "Test",
        "sort_order": 1,
        "resource_links": [
            {"title": "Docs", "url": "https://example.org/docs", "description": "Dokumentation"},
            {"title": "Support", "url": "http://example.org/support"},
        ],
    })
    assert len(block.resource_links) == 2
    assert block.resource_links[0].description == "Dokumentation"
    assert block.resource_links[1].description == ""
