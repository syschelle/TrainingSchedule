from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session

import app.server.content_db as content_db

from app.server.content_db import (
    Base,
    DEFAULT_PRODUCTS,
    DEFAULT_TRAINING_CONTENTS,
    TRAINING_CONTENT_HISTORY_LIMIT,
    TrainingContentRevisionRecord,
    create_product,
    create_training_content,
    seed_database,
    list_training_content_history,
    prune_training_content_history,
    restore_training_content_revision,
    update_training_content,
    update_training_content_markdown,
)


def test_pacs_training_contents_are_product_bound():
    product_ids = {product["id"] for product in DEFAULT_PRODUCTS}
    assert "deepunity-pacs" in product_ids
    assert DEFAULT_TRAINING_CONTENTS
    assert {item["product_id"] for item in DEFAULT_TRAINING_CONTENTS} <= product_ids
    assert all("max_participants" in item for item in DEFAULT_TRAINING_CONTENTS)
    assert all("participant_group_ids" in item for item in DEFAULT_TRAINING_CONTENTS)
    assert all("background_color" in item for item in DEFAULT_TRAINING_CONTENTS)


def test_pacs_pdf_analysis_excludes_schedule_flow():
    searchable_values = "\n".join(
        str(value)
        for item in DEFAULT_TRAINING_CONTENTS
        for key, value in item.items()
        if key not in {"source_file"}
    )
    assert "Schulungsverlauf" not in searchable_values
    assert all(item["goals"] and item["target_group"] for item in DEFAULT_TRAINING_CONTENTS)


def test_training_content_can_be_edited_without_seed_overwrite():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        updated = update_training_content(
            session,
            "du-diagnost-basic",
            {
                "title": "DU Diagnost Basic angepasst",
                "target_group": "Neue Zielgruppe",
                "duration_minutes": 95,
                "max_participants": 7,
                "split_enabled": True,
                "dependency_content_id": None,
                "participant_group_ids": ["radiologen", "mfa"],
                "background_color": "#abcdef",
                "goals": "Neue Ziele",
                "requirements": "Neue Voraussetzungen",
                "preparation": "Neue Vorbereitung",
                "special_notes": "Neue Hinweise",
            },
        )
        assert updated is not None
        assert updated["title"] == "DU Diagnost Basic angepasst"
        assert updated["max_participants"] == 7
        assert updated["split_enabled"] is True
        assert updated["participant_group_ids"] == ["radiologen", "mfa"]
        assert updated["background_color"] == "#abcdef"

        seed_database(session)
        edited_again = update_training_content(
            session,
            "du-diagnost-basic",
            {
                "title": "DU Diagnost Basic angepasst",
                "target_group": "Neue Zielgruppe",
                "duration_minutes": 95,
                "max_participants": 7,
                "split_enabled": True,
                "dependency_content_id": None,
                "participant_group_ids": ["radiologen", "mfa"],
                "background_color": "#abcdef",
                "goals": "Neue Ziele",
                "requirements": "Neue Voraussetzungen",
                "preparation": "Neue Vorbereitung",
                "special_notes": "Neue Hinweise",
            },
        )
        assert edited_again is not None
        assert edited_again["title"] == "DU Diagnost Basic angepasst"
        assert edited_again["split_enabled"] is True
        assert "source_file" not in edited_again


def test_products_can_be_added_with_unique_ids():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        first = create_product(session, "Neues Produkt", "Beschreibung")
        second = create_product(session, "Neues Produkt", "")

        assert first["id"] == "neues-produkt"
        assert second["id"] == "neues-produkt-2"
        assert first["description"] == "Beschreibung"


def test_training_contents_can_be_added_for_product():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        created = create_training_content(session, "deepunity-pacs", "Neue Schulung")
        assert created["id"] == "neue-schulung"
        assert created["product_id"] == "deepunity-pacs"
        assert created["duration_minutes"] == 60
        assert created["background_color"] == "#eaf8f2"
        assert created["split_enabled"] is False


def test_markdown_content_has_persistent_history_and_can_be_restored():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)

        first = update_training_content_markdown(
            session,
            "du-diagnost-basic",
            "## Grundlagen\n\n- Anmeldung\n- Patientensuche",
        )
        assert first is not None
        assert "Patientensuche" in first["markdown_content"]

        unchanged = update_training_content_markdown(
            session,
            "du-diagnost-basic",
            first["markdown_content"],
        )
        assert unchanged is not None
        history = list_training_content_history(session, "du-diagnost-basic")
        assert history is not None
        assert len(history) == 1

        second = update_training_content_markdown(
            session,
            "du-diagnost-basic",
            "## Grundlagen\n\n- Anmeldung\n- Patientensuche\n- Viewer",
        )
        assert second is not None
        history = list_training_content_history(session, "du-diagnost-basic")
        assert history is not None
        assert len(history) == 2
        oldest_revision_id = history[-1]["id"]

        restored = restore_training_content_revision(session, "du-diagnost-basic", oldest_revision_id)
        assert restored is not None
        assert restored["markdown_content"] == first["markdown_content"]

        history_after_restore = list_training_content_history(session, "du-diagnost-basic")
        assert history_after_restore is not None
        assert len(history_after_restore) == 3
        assert history_after_restore[0]["change_type"] == "restored"



def test_markdown_history_keeps_only_five_latest_revisions():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        for index in range(1, 8):
            updated = update_training_content_markdown(
                session,
                "du-diagnost-basic",
                f"## Version {index}\n\n- Punkt {index}",
            )
            assert updated is not None

        history = list_training_content_history(session, "du-diagnost-basic", limit=99)
        assert history is not None
        assert len(history) == TRAINING_CONTENT_HISTORY_LIMIT == 5
        assert "Version 7" in history[0]["markdown_content"]
        assert "Version 3" in history[-1]["markdown_content"]

        stored = session.scalars(
            select(TrainingContentRevisionRecord).where(
                TrainingContentRevisionRecord.content_id == "du-diagnost-basic"
            )
        ).all()
        assert len(stored) == 5


def test_existing_history_is_pruned_to_five_revisions_on_cleanup():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        session.add_all([
            TrainingContentRevisionRecord(
                content_id="du-diagnost-basic",
                markdown_content=f"## Altbestand {index}",
                change_type="saved",
            )
            for index in range(1, 8)
        ])
        session.commit()

        prune_training_content_history(session)

        stored = session.scalars(
            select(TrainingContentRevisionRecord).where(
                TrainingContentRevisionRecord.content_id == "du-diagnost-basic"
            )
        ).all()
        assert len(stored) == TRAINING_CONTENT_HISTORY_LIMIT == 5

def test_existing_training_contents_table_gets_markdown_column(monkeypatch):
    legacy_engine = create_engine("sqlite+pysqlite:///:memory:")
    with legacy_engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE training_contents (
                id VARCHAR(120) PRIMARY KEY,
                product_id VARCHAR(120) NOT NULL,
                title VARCHAR(240) NOT NULL,
                target_group TEXT NOT NULL DEFAULT '',
                duration_minutes INTEGER NOT NULL DEFAULT 60,
                goals TEXT NOT NULL DEFAULT '',
                requirements TEXT NOT NULL DEFAULT '',
                preparation TEXT NOT NULL DEFAULT '',
                special_notes TEXT NOT NULL DEFAULT '',
                source_file VARCHAR(240) NOT NULL DEFAULT ''
            )
        """))
    monkeypatch.setattr(content_db, "engine", legacy_engine)
    content_db.ensure_training_content_columns()
    columns = {column["name"] for column in inspect(legacy_engine).get_columns("training_contents")}
    assert "markdown_content" in columns
    assert "split_enabled" in columns


def test_docx_import_save_is_marked_in_history():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        updated = update_training_content_markdown(
            session,
            "du-diagnost-basic",
            "## Importiert\n\n- Punkt",
            change_type="docx_imported",
        )
        assert updated is not None
        history = list_training_content_history(session, "du-diagnost-basic")
        assert history is not None
        assert history[0]["change_type"] == "docx_imported"
