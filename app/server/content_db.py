from __future__ import annotations

import os
import re
import json
from datetime import datetime, timezone
from collections.abc import Iterator

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:")
TRAINING_CONTENT_HISTORY_LIMIT = 5


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
    master_data_blocks: Mapped[list[MasterDataBlockRecord]] = relationship(
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
    split_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dependency_content_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    participant_group_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    background_color: Mapped[str] = mapped_column(String(20), default="#eaf8f2", nullable=False)
    goals: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requirements: Mapped[str] = mapped_column(Text, default="", nullable=False)
    preparation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    special_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_file: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, default="", nullable=False)

    product: Mapped[ProductRecord] = relationship(back_populates="contents")
    revisions: Mapped[list[TrainingContentRevisionRecord]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
    )


class MasterDataBlockRecord(Base):
    __tablename__ = "master_data_blocks"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    background_color: Mapped[str] = mapped_column(String(20), default="#eef6ff", nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    answer_options: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    resource_links: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    product: Mapped[ProductRecord] = relationship(back_populates="master_data_blocks")


class TrainingContentRevisionRecord(Base):
    __tablename__ = "training_content_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("training_contents.id"), index=True, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    change_type: Mapped[str] = mapped_column(String(30), default="saved", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    content: Mapped[TrainingContentRecord] = relationship(back_populates="revisions")


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


DEFAULT_MASTER_DATA_BLOCKS = [
    {"id": 'uebersicht-installation-deepunity-client', "product_id": "deepunity-pacs", "sort_order": 1, "title": 'Übersicht Installation DeepUnity Client', "active": True, "background_color": "#eef6ff", "markdown_content": '- Vorstellung der DeepUnity Client Versionen und Lizenzierung\n- Das Konzept zur Verteilung der DeepUnity Software über den DU Webdeployer wurde erläutert.\n- Die Dokumente „DeepUnity Webdeployer – Gebrauchsanweisung“ und DeepUnity Webdeployer-Ordnerstruktur wurde an den Kunden übergeben und besprochen.'},
    {"id": 'rechte-und-rollenkonzept', "product_id": "deepunity-pacs", "sort_order": 2, "title": 'Rechte- und Rollenkonzept', "active": True, "background_color": "#eef6ff", "markdown_content": '- Die Standard-Rollen und deren zugehörigen Berechtigungen wurden anhand des Dokumentes „DeepUnity_Rollen_und_Berechtigungen“ vorgestellt und gemeinsam auf die Anforderungen des Hauses abgestimmt.\n- Die notwendigen Anpassungen für das Haus sind detailliert im Dokument „DeepUnity_Rollen_und_Berechtigungen“ notiert. Die Anpassungen umfassen folgende Punkte: Bitte Thema/Beschreibung eingeben\n- Offen sind folgende Punkte: Bitte Thema/Beschreibung eingeben'},
    {"id": 'authentifizierung-deepunity-software', "product_id": "deepunity-pacs", "sort_order": 3, "title": 'Authentifizierung DeepUnity-Software', "active": True, "background_color": "#eef6ff", "markdown_content": '- Die unterschiedlichen Möglichkeiten der Authentifizierung werden vorgestellt: unter anderem DeepUnity Server, LDAP-Authentifizierung bei Microsoft Active Directory Services oder Authentifizierung über die Orbis-Datenbank\n- Das Dokument „DeepUnity Fragebogen Benutzerauthentifizierung“ wurde erläutert.\n- Die Authentifizierung wird über bitte ausfüllen erfolgen.'},
    {"id": 'einrichtung-deepunity-viewer', "product_id": "deepunity-pacs", "sort_order": 4, "title": 'Einrichtung DeepUnity Viewer', "active": True, "background_color": "#eef6ff", "markdown_content": '- Die grundlegenden Funktionalitäten des DeepUnity Viewers wurden erklärt. Weiterhin sind die Möglichkeiten des Aufrufs des DeepUnity Viewers aus führenden Systemen (Parameter StudyInstanceUID, Auftragsnummer, Patienten-ID) geklärt.\n- Der Einsatz einer DeepUnity RL.exe ist vorgeschrieben und wurde erklärt.\n- Die Suchfunktionalität des DUViewers wurde beschrieben und soll folgendermaßen eingerichtet werden: bitte ausfüllen\n- Das Haus verwendet Citrix für Orbis und DUViewer: bitte ausfüllen\n- Offen sind folgende Punkte: Bitte Thema/Beschreibung eingeben'},
    {"id": 'einrichtung-von-arbeitslisten', "product_id": "deepunity-pacs", "sort_order": 5, "title": 'Einrichtung von Arbeitslisten', "active": True, "background_color": "#eef6ff", "markdown_content": '- Das Konzept der unterschiedlichen Arbeitslisten (geplante Arbeitslisten, Standard Arbeitslisten, Benutzer-Arbeitslisten) wurde erklärt.\n- Für die Erstellung der Arbeitslisten für Bild-Demonstrationen sind folgende Informationen pro Arbeitsliste notwendig: Frequenz, Startzeitpunkt, automatische/manuelle Befüllung, durch automatische Befüllung enthaltene Bilddaten (Fachabteilungen, Stationen, Modalitäten), Rollenzuordnung\n- Auflistung der anzulegenden Arbeitslisten: bitte ausfüllen\n- Offen sind folgende Punkte: Bitte Thema/Beschreibung eingeben'},
    {"id": 'zentrale-konfiguration-deepunity-clients', "product_id": "deepunity-pacs", "sort_order": 6, "title": 'Zentrale Konfiguration des DeepUnity Clients', "active": True, "background_color": "#eef6ff", "markdown_content": '- Benennung des Ansprechpartners für die Client-Konfiguration: bitte ausfüllen\n- Layout des Clients, Arbeitslisten, Sendeziele und Kommunikation mit Fremdsystemen'},
    {"id": 'definition-von-fensterwerten', "product_id": "deepunity-pacs", "sort_order": 7, "title": 'Definition von Fensterwerten', "active": True, "background_color": "#eef6ff", "markdown_content": '- Zur Verwendung der Standard-Fensterwerte können F-Tasten mit Fensterwerten belegt werden.\n- Standard Werte für Window und Level sind enthalten und können über die F-Tasten abgerufen werden.\n- Anpassung der Fensterwerte auf folgende Werte: bitte ausfüllen\n- Offen sind folgende Punkte: Bitte Thema/Beschreibung eingeben'},
    {"id": 'export-und-importmoeglichkeiten', "product_id": "deepunity-pacs", "sort_order": 8, "title": 'Export- und Importmöglichkeiten', "active": True, "background_color": "#eef6ff", "markdown_content": '- Die Möglichkeiten zum Import und Export von Daten mit der DeepUnity-Software wurden erläutert.\n- Die Berechtigungen für den Import und Export wurden entsprechend gesetzt.\n- Die Arbeitsplätze, die für den Import und Export verwendet werden sollen, sind definiert.'},
    {"id": 'deepunity-media-creator', "product_id": "deepunity-pacs", "sort_order": 9, "title": 'DeepUnity Media Creator (falls vorhanden)', "active": True, "background_color": "#eef6ff", "markdown_content": '- Labelgestaltung definiert? (Link zum Dokument: 32238723)'},
    {"id": 'import-mit-worklist', "product_id": "deepunity-pacs", "sort_order": 10, "title": 'Import mit Worklist (falls vorhanden)', "active": True, "background_color": "#eef6ff", "markdown_content": '- Definition der Rechner und des verwendeten Softwaremoduls (DeepUnity XChange oder DeepUnity Client)'},
    {"id": 'anpassung-ris-leistungsbaum', "product_id": "deepunity-pacs", "sort_order": 11, "title": 'Anpassung RIS-Leistungsbaum', "active": True, "background_color": "#eef6ff", "markdown_content": '- Für Import und Export sollen folgenden Leistungen angelegt werden. Die Leistungen werden durch bitte ausfüllen angelegt.'},
    {"id": 'software-abnahme-konstanzpruefung', "product_id": "deepunity-pacs", "sort_order": 12, "title": 'Software zur Abnahme- und Konstanzprüfung an Bildschirmwiedergabegeräten', "active": True, "background_color": "#eef6ff", "markdown_content": '- Definition der BWG für Monitorabnahme\n- Leuchtdichtemessgerät vorhanden?\n- Definition des Mitarbeiters (Kunde) für Konstanzprüfung (Einweisung planen!)'},
    {"id": 'hectec-medicad', "product_id": "deepunity-pacs", "sort_order": 13, "title": 'HecTec mediCAD (falls vorhanden)', "active": True, "background_color": "#eef6ff", "markdown_content": '- Clientlizenz: Rechner, auf denen mediCAD installiert werden müssen definiert werden\n- MediCAD muss min. 6.xxx als Version haben.\n- Netzwerklizenz: Festlegung Lizenzserver'},
    {"id": 'zusaetzliche-plugins', "product_id": "deepunity-pacs", "sort_order": 14, "title": 'Zusätzliche Plugins (falls vorhanden)', "active": True, "background_color": "#eef6ff", "markdown_content": '- Zusätzliche Plugins, die gekauft wurden: bitte ausfüllen\n- Bei DU Clinical Applications ist die Installation eines zusätzlichen Moduls am Rechner erforderlich. An folgenden Rechner wird das Modul eingesetzt.\n- Folgende Anwender sollen zu folgendem Zeitpunkt im Plugin geschult werden: bitte ausfüllen'},
    {"id": 'schulungsplanung', "product_id": "deepunity-pacs", "sort_order": 15, "title": 'Schulungsplanung', "active": True, "background_color": "#eef6ff", "markdown_content": '- Schulungen können als Onlineschulungen oder als Präsenzschulung durchgeführt werden. Was wird bevorzugt? bitte ausfüllen\n- Eine Anpassung der Schulungsplanung nach Abstimmung der Berechtigungen ist nicht notwendig/ notwendig: bitte ausfüllen\n- Die Schulungsplanung ist abgeschlossen, Die KeyUser aus der Radiologie sind benannt. Folgende Fragen zu den Schulungen konnten geklärt werden.\n- Definition des KeyUsers erfolgt? (Beispiel: Konfiguration von Bildbeschriftungen, Hanging-Protokollen, Werkzeuge)'},
    {"id": 'bedingungen-remotekonfiguration', "product_id": "deepunity-pacs", "sort_order": 16, "title": 'Bedingungen für Remotekonfiguration des Systems', "active": True, "background_color": "#eef6ff", "markdown_content": 'Remoteserver min. WindowsServer16 -> TLS 1.0 wird sonst nicht unterstützt'},
    {"id": 'fragen-und-offene-punkte', "product_id": "deepunity-pacs", "sort_order": 17, "title": 'Fragen und Offene Punkte', "active": True, "background_color": "#eef6ff", "markdown_content": 'Anwenderfragen'},
]


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def db_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def init_database() -> None:
    Base.metadata.create_all(engine)
    ensure_training_content_columns()
    ensure_master_data_block_columns()
    with SessionLocal() as session:
        seed_database(session)
        prune_training_content_history(session)


def ensure_training_content_columns() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("training_contents")}
    with engine.begin() as connection:
        if "max_participants" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN max_participants INTEGER"))
        if "split_enabled" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN split_enabled BOOLEAN DEFAULT FALSE NOT NULL"))
        if "dependency_content_id" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN dependency_content_id VARCHAR(120)"))
        if "participant_group_ids" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN participant_group_ids TEXT DEFAULT '[]' NOT NULL"))
        if "background_color" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN background_color VARCHAR(20) DEFAULT '#eaf8f2' NOT NULL"))
        if "markdown_content" not in columns:
            connection.execute(text("ALTER TABLE training_contents ADD COLUMN markdown_content TEXT DEFAULT '' NOT NULL"))


def ensure_master_data_block_columns() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("master_data_blocks")}
    with engine.begin() as connection:
        if "answer_type" not in columns:
            connection.execute(text("ALTER TABLE master_data_blocks ADD COLUMN answer_type VARCHAR(20) DEFAULT 'none' NOT NULL"))
        if "answer_options" not in columns:
            connection.execute(text("ALTER TABLE master_data_blocks ADD COLUMN answer_options TEXT DEFAULT '[]' NOT NULL"))
        if "resource_links" not in columns:
            connection.execute(text("ALTER TABLE master_data_blocks ADD COLUMN resource_links TEXT DEFAULT '[]' NOT NULL"))


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

    for item in DEFAULT_MASTER_DATA_BLOCKS:
        existing = session.get(MasterDataBlockRecord, item["id"])
        if not existing:
            session.add(MasterDataBlockRecord(**item))
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
        split_enabled=False,
        dependency_content_id=None,
        participant_group_ids="[]",
        background_color="#eaf8f2",
        goals="",
        requirements="",
        preparation="",
        special_notes="",
        source_file="",
        markdown_content="",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return training_content_to_dict(record)


def list_master_data_blocks(session: Session, product_id: str | None = None, include_inactive: bool = True) -> list[dict]:
    statement = select(MasterDataBlockRecord).order_by(
        MasterDataBlockRecord.product_id, MasterDataBlockRecord.sort_order, MasterDataBlockRecord.title
    )
    if product_id:
        statement = statement.where(MasterDataBlockRecord.product_id == product_id)
    if not include_inactive:
        statement = statement.where(MasterDataBlockRecord.active.is_(True))
    return [master_data_block_to_dict(item) for item in session.scalars(statement).all()]


def get_master_data_block(session: Session, block_id: str) -> dict | None:
    record = session.get(MasterDataBlockRecord, block_id)
    return master_data_block_to_dict(record) if record else None


def create_master_data_block(session: Session, product_id: str, title: str) -> dict:
    if not session.get(ProductRecord, product_id):
        raise ValueError("product_not_found")
    current = session.scalars(
        select(MasterDataBlockRecord).where(MasterDataBlockRecord.product_id == product_id)
    ).all()
    record = MasterDataBlockRecord(
        id=unique_master_data_block_id(session, slugify(title)),
        product_id=product_id,
        sort_order=len(current) + 1,
        title=title.strip(),
        active=True,
        background_color="#eef6ff",
        markdown_content="",
        answer_type="none",
        answer_options="[]",
        resource_links="[]",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return master_data_block_to_dict(record)


def update_master_data_block(session: Session, block_id: str, values: dict) -> dict | None:
    record = session.get(MasterDataBlockRecord, block_id)
    if not record:
        return None
    product_id = record.product_id
    record.title = str(values.get("title", record.title)).strip() or record.title
    record.active = bool(values.get("active", record.active))
    record.background_color = clean_master_data_color(values.get("background_color"))
    record.markdown_content = str(values.get("markdown_content", record.markdown_content) or "")
    record.answer_type = clean_master_data_answer_type(values.get("answer_type", record.answer_type))
    record.answer_options = json.dumps(clean_master_data_answer_options(values.get("answer_options", parse_answer_options(record.answer_options))), ensure_ascii=False)
    record.resource_links = json.dumps(clean_master_data_resource_links(values.get("resource_links", parse_master_data_resource_links(record.resource_links))), ensure_ascii=False)
    requested_order = max(1, int(values.get("sort_order", record.sort_order)))
    records = list(session.scalars(
        select(MasterDataBlockRecord)
        .where(MasterDataBlockRecord.product_id == product_id)
        .order_by(MasterDataBlockRecord.sort_order, MasterDataBlockRecord.title)
    ).all())
    records = [item for item in records if item.id != record.id]
    records.insert(min(requested_order - 1, len(records)), record)
    for index, item in enumerate(records, start=1):
        item.sort_order = index
    session.commit()
    session.refresh(record)
    return master_data_block_to_dict(record)


def delete_master_data_block(session: Session, block_id: str) -> bool:
    record = session.get(MasterDataBlockRecord, block_id)
    if not record:
        return False
    product_id = record.product_id
    session.delete(record)
    session.flush()
    records = session.scalars(
        select(MasterDataBlockRecord)
        .where(MasterDataBlockRecord.product_id == product_id)
        .order_by(MasterDataBlockRecord.sort_order, MasterDataBlockRecord.title)
    ).all()
    for index, item in enumerate(records, start=1):
        item.sort_order = index
    session.commit()
    return True


def master_data_block_to_dict(item: MasterDataBlockRecord) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "sort_order": item.sort_order,
        "title": item.title,
        "active": bool(item.active),
        "background_color": item.background_color or "#eef6ff",
        "markdown_content": item.markdown_content or "",
        "answer_type": clean_master_data_answer_type(item.answer_type),
        "answer_options": parse_answer_options(item.answer_options),
        "resource_links": parse_master_data_resource_links(item.resource_links),
    }


def get_training_content(session: Session, content_id: str) -> dict | None:
    record = session.get(TrainingContentRecord, content_id)
    return training_content_to_dict(record) if record else None


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
    for key in ["title", "target_group", "duration_minutes", "max_participants", "split_enabled", "dependency_content_id", "goals", "requirements", "preparation", "special_notes"]:
        if key in values:
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
        "split_enabled": bool(item.split_enabled),
        "dependency_content_id": item.dependency_content_id,
        "participant_group_ids": parse_group_ids(item.participant_group_ids),
        "background_color": item.background_color,
        "goals": item.goals,
        "requirements": item.requirements,
        "preparation": item.preparation,
        "special_notes": item.special_notes,
        "markdown_content": item.markdown_content or "",
    }


def _prune_training_content_history_for_content(
    session: Session,
    content_id: str,
    keep: int = TRAINING_CONTENT_HISTORY_LIMIT,
) -> None:
    session.flush()
    statement = (
        select(TrainingContentRevisionRecord)
        .where(TrainingContentRevisionRecord.content_id == content_id)
        .order_by(TrainingContentRevisionRecord.created_at.desc(), TrainingContentRevisionRecord.id.desc())
        .offset(max(0, keep))
    )
    for revision in session.scalars(statement).all():
        session.delete(revision)


def prune_training_content_history(session: Session) -> None:
    content_ids = session.scalars(select(TrainingContentRevisionRecord.content_id).distinct()).all()
    for content_id in content_ids:
        _prune_training_content_history_for_content(session, content_id)
    session.commit()


def update_training_content_markdown(session: Session, content_id: str, markdown_content: str, change_type: str = "saved") -> dict | None:
    record = session.get(TrainingContentRecord, content_id)
    if not record:
        return None
    markdown_content = markdown_content or ""
    if markdown_content != (record.markdown_content or ""):
        record.markdown_content = markdown_content
        session.add(TrainingContentRevisionRecord(
            content_id=content_id,
            markdown_content=markdown_content,
            change_type=change_type,
        ))
        _prune_training_content_history_for_content(session, content_id)
        session.commit()
        session.refresh(record)
    return training_content_to_dict(record)


def list_training_content_history(
    session: Session,
    content_id: str,
    limit: int = TRAINING_CONTENT_HISTORY_LIMIT,
) -> list[dict] | None:
    if not session.get(TrainingContentRecord, content_id):
        return None
    statement = (
        select(TrainingContentRevisionRecord)
        .where(TrainingContentRevisionRecord.content_id == content_id)
        .order_by(TrainingContentRevisionRecord.created_at.desc(), TrainingContentRevisionRecord.id.desc())
        .limit(max(1, min(limit, TRAINING_CONTENT_HISTORY_LIMIT)))
    )
    records = session.scalars(statement).all()
    return [training_content_revision_to_dict(item) for item in records]


def restore_training_content_revision(session: Session, content_id: str, revision_id: int) -> dict | None:
    record = session.get(TrainingContentRecord, content_id)
    revision = session.get(TrainingContentRevisionRecord, revision_id)
    if not record or not revision or revision.content_id != content_id:
        return None
    record.markdown_content = revision.markdown_content
    session.add(TrainingContentRevisionRecord(
        content_id=content_id,
        markdown_content=revision.markdown_content,
        change_type="restored",
    ))
    _prune_training_content_history_for_content(session, content_id)
    session.commit()
    session.refresh(record)
    return training_content_to_dict(record)


def training_content_revision_to_dict(item: TrainingContentRevisionRecord) -> dict:
    created_at = item.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "id": item.id,
        "content_id": item.content_id,
        "markdown_content": item.markdown_content,
        "change_type": item.change_type,
        "created_at": created_at.isoformat(),
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


MASTER_DATA_ANSWER_TYPES = {"none", "text", "select", "checkboxes", "yes_no"}


def clean_master_data_answer_type(value: object) -> str:
    answer_type = str(value or "none").strip().lower()
    return answer_type if answer_type in MASTER_DATA_ANSWER_TYPES else "none"


def clean_master_data_answer_options(values: object) -> list[str]:
    if isinstance(values, str):
        try:
            decoded = json.loads(values)
            if isinstance(decoded, list):
                values = decoded
            else:
                values = values.splitlines()
        except (json.JSONDecodeError, TypeError):
            values = values.splitlines()
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        option = str(value).strip()
        if option and option not in cleaned:
            cleaned.append(option)
    return cleaned


def parse_answer_options(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return clean_master_data_answer_options(value)
    return clean_master_data_answer_options(decoded)


def clean_master_data_resource_links(values: object) -> list[dict[str, str]]:
    if isinstance(values, str):
        try:
            decoded = json.loads(values)
            values = decoded if isinstance(decoded, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(values, list):
        return []
    cleaned: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        if not isinstance(value, dict):
            continue
        url = str(value.get("url", "")).strip()
        if not url.lower().startswith(("http://", "https://")):
            continue
        title = str(value.get("title", "")).strip() or url
        description = str(value.get("description", "")).strip()
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"title": title, "url": url, "description": description})
    return cleaned


def parse_master_data_resource_links(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
    return clean_master_data_resource_links(decoded)


def clean_master_data_color(value: str | None) -> str:
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()):
        return value.strip().lower()
    return "#eef6ff"


def unique_master_data_block_id(session: Session, base_id: str) -> str:
    base_id = f"master-{base_id}" if not base_id.startswith("master-") else base_id
    candidate = base_id
    counter = 2
    while session.get(MasterDataBlockRecord, candidate):
        candidate = f"{base_id}-{counter}"
        counter += 1
    return candidate
