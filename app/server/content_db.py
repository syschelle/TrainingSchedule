from __future__ import annotations

import os
import re
import json
from collections.abc import Iterator

from sqlalchemy import ForeignKey, Integer, String, Text, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:")


class Base(DeclarativeBase):
    pass


class ProductRecord(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    contents: Mapped[list[TrainingContentRecord]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class TrainingContentRecord(Base):
    __tablename__ = "training_contents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    target_group: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=60, nullable=False)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dependency_content_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    participant_group_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    background_color: Mapped[str] = mapped_column(String(20), default="#eaf8f2", nullable=False)
    goals: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requirements: Mapped[str] = mapped_column(Text, default="", nullable=False)
    preparation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    special_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_file: Mapped[str] = mapped_column(String(240), default="", nullable=False)

    product: Mapped[ProductRecord] = relationship(back_populates="contents")


DEFAULT_PRODUCTS = [
    {
        "id": "deepunity-pacs",
        "name": "DeepUnity PACS",
        "description": "PACS-Schulungen fuer Radiologie, Keyuser, MFA, Kliniker, Webviewer und Administration.",
    }
]


DEFAULT_TRAINING_CONTENTS = [
    {
        "id": "pacs-administration",
        "product_id": "deepunity-pacs",
        "title": "PACS-Administration",
        "target_group": "PACS-Administratoren, IT-Personal und Abteilungsadministratoren.",
        "duration_minutes": 360,
        "max_participants": 6,
        "dependency_content_id": None,
        "participant_group_ids": ["administratoren"],
        "background_color": "#e9f2ff",
        "goals": "Aufbau des DeepUnity Systems, Client-Installation, Rechte/Rollen, Konfiguration, Hilfefunktionen, Webinterface und Support-Meldungen.",
        "requirements": "Installierter PACS-Client am Arbeitsplatz jedes Teilnehmers, Remote-Zugriff fuer Trainer, geeignete Schulungsumgebung ohne Aufzeichnung.",
        "preparation": "Lernvideos und Unterlagen bereitstellen, technische Voraussetzungen klaeren, Kundensystem pruefen, Technik-Check und Vorbereitungsfragen einplanen.",
        "special_notes": "KUNDENSYSTEM/DEDALUSSYSTEM und projektspezifische Unterlagen vorab abstimmen.",
        "source_file": "PACS-Administration.pdf",
    },
    {
        "id": "du-diagnost-basic",
        "product_id": "deepunity-pacs",
        "title": "DU Diagnost Basic",
        "target_group": "Radiologen, Nuklearmediziner und weitere Mitarbeiter, die Befunde erstellen.",
        "duration_minutes": 90,
        "max_participants": 8,
        "dependency_content_id": None,
        "participant_group_ids": ["radiologen", "radiologen-keyuser"],
        "background_color": "#eaf8f2",
        "goals": "Grundlagen und sichere Bedienung der DeepUnity DIAGNOST Anwendung.",
        "requirements": "DeepUnity DIAGNOST Client, Trainerzugriff, geeignete Beispielstudien und keine Aufzeichnung.",
        "preparation": "Schulungsunterlagen bereitstellen, Testzugang pruefen und technische Teilnahmevoraussetzungen sicherstellen.",
        "special_notes": "Als Basis fuer weiterfuehrende DIAGNOST-Schulungen vorsehen.",
        "source_file": "DU Diagnost Basic.pdf",
    },
    {
        "id": "du-diagnost-erweitert",
        "product_id": "deepunity-pacs",
        "title": "DU Diagnost erweitert",
        "target_group": "Befundende Anwender mit vorhandenen DIAGNOST-Grundlagen.",
        "duration_minutes": 120,
        "max_participants": 8,
        "dependency_content_id": "du-diagnost-basic",
        "participant_group_ids": ["radiologen", "radiologen-keyuser"],
        "background_color": "#fff5e8",
        "goals": "Erweiterte Funktionen der DeepUnity DIAGNOST Befundungsworkstation.",
        "requirements": "Absolvierte Basic-Schulung, Schulungsaccounts, Teststudien und Zugriff auf relevante Client-Funktionen.",
        "preparation": "Teilnehmerkreis mit Basic-Vorkenntnissen planen, Beispielstudien und Konten pruefen.",
        "special_notes": "Abhaengig von DU Diagnost Basic einplanen.",
        "source_file": "DU Diagnost erweitert.pdf",
    },
    {
        "id": "du-diagnost-keyuser",
        "product_id": "deepunity-pacs",
        "title": "DU Diagnost KeyUser",
        "target_group": "Radiologie-Keyuser und IT-nahe DeepUnity Client Administratoren.",
        "duration_minutes": 180,
        "max_participants": 4,
        "dependency_content_id": "du-diagnost-erweitert",
        "participant_group_ids": ["radiologen-keyuser"],
        "background_color": "#f3e8ff",
        "goals": "Konfigurationsoberflaeche, praktische Uebungen und Verteilung der Client Software.",
        "requirements": "Absolvierte Basic- und Erweiterungsschulung, Schulungsaccounts, Teststudien und Administrationsrechte in der Schulungsumgebung.",
        "preparation": "Keyuser benennen, administrative Testberechtigungen klaeren und Client-Verteilungswege vorbereiten.",
        "special_notes": "Nach DU Diagnost Basic und DU Diagnost erweitert einplanen.",
        "source_file": "DU Diagnost KeyUser.pdf",
    },
    {
        "id": "du-review-kliniker",
        "product_id": "deepunity-pacs",
        "title": "DU Review Kliniker",
        "target_group": "Kliniker mit Zugriff auf Bilddaten und Archivfunktionen.",
        "duration_minutes": 60,
        "max_participants": 12,
        "dependency_content_id": None,
        "participant_group_ids": ["kliniker"],
        "background_color": "#edf1ff",
        "goals": "Grundlagen der DeepUnity REVIEW Betrachtungsworkstation.",
        "requirements": "Review-Zugriff, passende Arbeitsplatzumgebung und Trainerzugriff.",
        "preparation": "Teilnehmerzugriffe pruefen und typische klinische Anwendungsfaelle vorbereiten.",
        "special_notes": "Fokus auf klinischen Betrachtungsworkflow ohne Befundungsadministration.",
        "source_file": "DU Review Kliniker.pdf",
    },
    {
        "id": "du-viewer",
        "product_id": "deepunity-pacs",
        "title": "DU Viewer",
        "target_group": "Klinische Anwender und Nutzer der hausweiten Bildverteilung.",
        "duration_minutes": 45,
        "max_participants": 20,
        "dependency_content_id": None,
        "participant_group_ids": ["webviewer", "kliniker"],
        "background_color": "#e8faf5",
        "goals": "Grundwissen und sicherer Umgang mit dem DeepUnity Viewer.",
        "requirements": "Aktueller Edge- oder Chrome-Browser, Trainerzugriff und geeignete Bildbeispiele.",
        "preparation": "Browserzugriff, Benutzerrechte und Beispielpatienten pruefen.",
        "special_notes": "Kurzformat fuer breite Anwendergruppen geeignet.",
        "source_file": "DU Viewer.pdf",
    },
    {
        "id": "du-xchange",
        "product_id": "deepunity-pacs",
        "title": "DU XChange",
        "target_group": "Klinische Mitarbeiter, MTRA sowie Sekretariate oder Anmeldungen mit Import-/Export-Aufgaben.",
        "duration_minutes": 60,
        "max_participants": 8,
        "dependency_content_id": None,
        "participant_group_ids": ["mfa"],
        "background_color": "#fff0ee",
        "goals": "Import und Export von Patientenstudien mit DeepUnity XChange.",
        "requirements": "XChange-Zugriff, Beispielstudien, passende Berechtigungen und Trainerzugriff.",
        "preparation": "Import-/Export-Szenarien abstimmen und Testdaten vorbereiten.",
        "special_notes": "Kann zusammen mit Review-Workflows fuer MTRA geplant werden.",
        "source_file": "DU XChange.pdf",
    },
    {
        "id": "review-mtra",
        "product_id": "deepunity-pacs",
        "title": "Review MTRA",
        "target_group": "Radiologie-Mitarbeiter ohne Befundungsschwerpunkt, insbesondere MTRA.",
        "duration_minutes": 60,
        "max_participants": 8,
        "dependency_content_id": "du-xchange",
        "participant_group_ids": ["mfa"],
        "background_color": "#f8fafc",
        "goals": "Review- und XChange-Funktionen fuer MTRA-Arbeitsplaetze.",
        "requirements": "Review/XChange-Zugriff, passende Beispielstudien und funktionierende Arbeitsplatzumgebung.",
        "preparation": "MTRA-relevante Workflows und Berechtigungen vorbereiten.",
        "special_notes": "Praxisnah fuer nicht-befundende Radiologie-Workflows.",
        "source_file": "Review MTRA.pdf",
    },
]


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def db_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def init_database() -> None:
    Base.metadata.create_all(engine)
    ensure_training_content_columns()
    with SessionLocal() as session:
        seed_database(session)


def ensure_training_content_columns() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("training_contents")}
    with engine.begin() as connection:
        if "max_participants" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN max_participants INTEGER"))
        if "dependency_content_id" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN dependency_content_id VARCHAR(120)"))
        if "participant_group_ids" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN participant_group_ids TEXT DEFAULT '[]' NOT NULL"))
        if "background_color" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN background_color VARCHAR(20) DEFAULT '#eaf8f2' NOT NULL"))


def seed_database(session: Session) -> None:
    for item in DEFAULT_PRODUCTS:
        existing = session.get(ProductRecord, item["id"])
        if existing:
            existing.name = item["name"]
            existing.description = item["description"]
        else:
            session.add(ProductRecord(**item))

    for item in DEFAULT_TRAINING_CONTENTS:
        existing = session.get(TrainingContentRecord, item["id"])
        if existing:
            if existing.max_participants is None:
                existing.max_participants = item.get("max_participants")
            if existing.dependency_content_id is None:
                existing.dependency_content_id = item.get("dependency_content_id")
            if not parse_group_ids(existing.participant_group_ids):
                existing.participant_group_ids = json.dumps(item.get("participant_group_ids", []))
            if not existing.background_color:
                existing.background_color = item.get("background_color", "#eaf8f2")
        else:
            record_values = {**item, "participant_group_ids": json.dumps(item.get("participant_group_ids", []))}
            session.add(TrainingContentRecord(**record_values))
    session.commit()


def list_products(session: Session) -> list[dict]:
    records = session.scalars(select(ProductRecord).order_by(ProductRecord.name)).all()
    return [{"id": item.id, "name": item.name, "description": item.description} for item in records]


def create_product(session: Session, name: str, description: str = "") -> dict:
    product_id = unique_product_id(session, slugify(name))
    record = ProductRecord(id=product_id, name=name.strip(), description=description.strip())
    session.add(record)
    session.commit()
    session.refresh(record)
    return {"id": record.id, "name": record.name, "description": record.description}


def create_training_content(session: Session, product_id: str, title: str) -> dict:
    if not session.get(ProductRecord, product_id):
        raise ValueError("product_not_found")
    record = TrainingContentRecord(
        id=unique_content_id(session, slugify(title)),
        product_id=product_id,
        title=title.strip(),
        target_group="",
        duration_minutes=60,
        max_participants=None,
        dependency_content_id=None,
        participant_group_ids="[]",
        background_color="#eaf8f2",
        goals="",
        requirements="",
        preparation="",
        special_notes="",
        source_file="",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return training_content_to_dict(record)


def list_training_contents(session: Session, product_id: str | None = None) -> list[dict]:
    statement = select(TrainingContentRecord).order_by(TrainingContentRecord.product_id, TrainingContentRecord.title)
    if product_id:
        statement = statement.where(TrainingContentRecord.product_id == product_id)
    records = session.scalars(statement).all()
    return [
        training_content_to_dict(item)
        for item in records
    ]


def update_training_content(session: Session, content_id: str, values: dict) -> dict | None:
    record = session.get(TrainingContentRecord, content_id)
    if not record:
        return None
    for key in ["title", "target_group", "duration_minutes", "max_participants", "dependency_content_id", "goals", "requirements", "preparation", "special_notes"]:
        setattr(record, key, values[key])
    record.background_color = clean_color(values.get("background_color"))
    record.participant_group_ids = json.dumps(values.get("participant_group_ids", []))
    session.commit()
    session.refresh(record)
    return training_content_to_dict(record)


def training_content_to_dict(item: TrainingContentRecord) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "title": item.title,
        "target_group": item.target_group,
        "duration_minutes": item.duration_minutes,
        "max_participants": item.max_participants,
        "dependency_content_id": item.dependency_content_id,
        "participant_group_ids": parse_group_ids(item.participant_group_ids),
        "background_color": item.background_color,
        "goals": item.goals,
        "requirements": item.requirements,
        "preparation": item.preparation,
        "special_notes": item.special_notes,
    }


def parse_group_ids(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "produkt"


def clean_color(value: str | None) -> str:
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()):
        return value.strip().lower()
    return "#eaf8f2"


def unique_product_id(session: Session, base_id: str) -> str:
    candidate = base_id
    counter = 2
    while session.get(ProductRecord, candidate):
        candidate = f"{base_id}-{counter}"
        counter += 1
    return candidate


def unique_content_id(session: Session, base_id: str) -> str:
    candidate = base_id
    counter = 2
    while session.get(TrainingContentRecord, candidate):
        candidate = f"{base_id}-{counter}"
        counter += 1
    return candidate
