# Schulungsplantool

Aktuelle Version: **v0.2.22**

Lokale Webanwendung zur Erstellung, Bearbeitung, Validierung und zum Export mehrtaegiger Schulungsplaene. Die Anwendung laeuft vollstaendig in Docker und verwendet PostgreSQL fuer den strukturierten Schulungsinhalte-Katalog.

## Funktionen

- Projektdaten, Planungsregeln und konkrete Schulungsthemen
- Produktverwaltung und produktbezogener Schulungsinhalte-Katalog
- Teilnehmergruppen, maximale Teilnehmerzahl und Abhaengigkeiten zwischen Schulungen
- automatische Planung fuer Montag bis Donnerstag, optional Freitag
- mehrere Schulungswochen
- Kernarbeitszeiten, Anreise-, Abreise-, Pausen- und Mittagspausenregeln
- Kalenderansicht mit Viertelstundenraster
- Drag-and-Drop von Schulungsbloecken zwischen Zeiten, Tagen und Wochen
- Ausschneiden und Einfuegen von Bloecken
- Live-Validierung
- Druckvorschau
- Export als PDF und XLSX
- lokale Projektdatei fuer den Benutzer
- PostgreSQL-Katalog fuer dauerhaft gepflegte Schulungsinhalte

## Datenschutz

Hochgeladene Excel- oder PDF-Dateien werden nicht in PostgreSQL oder Docker-Volumes abgelegt. Die vorhandene Import-API verarbeitet Uploads nur im Request-Speicher. Der Quellordner `Aufgabe/`, lokale Quelldokumente sowie `Aufgabe.md` werden durch `.dockerignore` nicht in das Anwendungsimage uebernommen.

Persistiert wird ausschliesslich das PostgreSQL-Volume fuer strukturierte Produkt- und Schulungsinhalte.

## Voraussetzungen

Auf dem Zielsystem werden benoetigt:

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Git, wenn die Installation direkt aus dem Repository erfolgen soll

## Schnellinstallation

Nach dem Klonen des Repositorys:

```bash
cd Schulungsplantool
./scripts/install.sh
```

Das Installationsskript:

1. prueft Docker und Docker Compose,
2. erzeugt bei der Erstinstallation automatisch eine lokale `.env`,
3. erzeugt ein zufaelliges PostgreSQL-Passwort,
4. validiert die Compose-Konfiguration,
5. baut das Anwendungsimage,
6. startet PostgreSQL und Schulungsplantool.

Standardmaessig ist die Anwendung erreichbar unter:

```text
http://SERVER-IP:18083
```

Der Port kann in `.env` ueber `APP_PORT` geaendert werden.

## Manuelle Installation

```bash
cp .env.example .env
```

Vor dem Produktionsstart in `.env` mindestens `POSTGRES_PASSWORD` und den gleichen Wert innerhalb von `DATABASE_URL` ersetzen.

Anschliessend:

```bash
docker compose up -d --build
```

Status anzeigen:

```bash
docker compose ps
```

Healthcheck testen:

```bash
curl http://127.0.0.1:18083/api/health
```

Erwartete Antwort:

```json
{"status":"ok","version":"0.2.22"}
```

## Konfiguration

Wichtige Werte in `.env`:

| Variable | Standard | Bedeutung |
|---|---|---|
| `APP_BIND` | `0.0.0.0` | Host-Adresse, an die der Webport gebunden wird |
| `APP_PORT` | `18083` | Webport des Schulungsplantools |
| `TZ` | `Europe/Berlin` | Zeitzone |
| `MAX_UPLOAD_MB` | `25` | maximale Uploadgroesse pro Datei |
| `POSTGRES_DB` | `schulungsplantool` | Datenbankname |
| `POSTGRES_USER` | `schulungsplantool` | Datenbankbenutzer |
| `POSTGRES_PASSWORD` | kein sicherer Default | Datenbankpasswort |
| `DATABASE_URL` | siehe `.env.example` | interne Verbindung der Anwendung zu PostgreSQL |

Wenn ein Reverse Proxy auf demselben Docker-Host verwendet wird und der Port nicht im LAN erreichbar sein soll, kann beispielsweise gesetzt werden:

```text
APP_BIND=127.0.0.1
```

## Update

Wenn das Projekt aus Git installiert wurde:

```bash
./scripts/update.sh
```

Das Skript fuehrt einen Fast-Forward-Pull aus, baut das Image mit aktuellen Basisimages neu und aktualisiert die laufenden Container ohne das PostgreSQL-Volume zu loeschen.

Manuell entspricht das im Wesentlichen:

```bash
git pull --ff-only
docker compose build --pull
docker compose up -d --remove-orphans
```

**Nicht** `docker compose down -v` verwenden, wenn die gespeicherten Produkt- und Schulungsinhalte erhalten bleiben sollen.

## Datenbank sichern

```bash
./scripts/backup-db.sh
```

Die Sicherung wird lokal unter `backups/` als komprimierter SQL-Dump abgelegt. Der Ordner ist von Git ausgeschlossen.

## Stoppen und neu starten

```bash
docker compose stop
docker compose start
```

Komplett neu erzeugen, ohne die Datenbankdaten zu loeschen:

```bash
docker compose up -d --build --force-recreate
```

## Logs

```bash
docker compose logs -f schulungsplantool
```

PostgreSQL:

```bash
docker compose logs -f postgres
```

## Entwicklung und Tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.server.main:app --reload
```

GitHub Actions prueft bei Pushes und Pull Requests automatisch:

- Python-Tests
- Docker-Compose-Konfiguration
- Docker-Image-Build

## Repository-Struktur

```text
.
├── app/                    # FastAPI-Backend und statisches Browser-Frontend
├── docs/                   # technische Analyse/Dokumentation
├── scripts/                # Installation, Update und Datenbank-Backup
├── tests/                  # automatisierte Tests
├── .github/workflows/      # CI
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── CHANGELOG.md
└── README.md
```

## Persistente Daten

Das Compose-Projekt verwendet genau ein persistentes Volume:

```text
schulungsplantool_pgdata
```

Es enthaelt ausschliesslich die PostgreSQL-Datenbank. Originale Upload-Dateien werden dort nicht gespeichert.
