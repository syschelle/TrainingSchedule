from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.server.content_db import (
    Base,
    DEFAULT_PRODUCTS,
    DEFAULT_TRAINING_CONTENTS,
    create_product,
    create_training_content,
    seed_database,
    update_training_content,
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
