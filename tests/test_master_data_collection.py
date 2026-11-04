from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.server.content_db import (
    Base, DEFAULT_MASTER_DATA_BLOCKS, create_master_data_block, delete_master_data_block,
    list_master_data_blocks, seed_database, update_master_data_block,
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
        })
        assert moved is not None
        assert moved["sort_order"] == 2
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
