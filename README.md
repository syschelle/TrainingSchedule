# Schulungsplantool

Aktuelle Version: **v0.2.24**

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

Nach dem Klonen des Repositorys reicht fuer das Produktivsystem:

```bash
cd Schulungsplantool
./install.sh
```

Das Root-Skript startet `scripts/install.sh`. Standardmaessig verwendet die Installation **`docker-compose.images.yml`** und zieht das bereits veroeffentlichte Multi-Arch-Image aus GHCR. Ein lokaler Build ist auf dem Produktivsystem nicht erforderlich.

Das Installationsskript:

1. prueft Docker und Docker Compose v2,
2. erzeugt bei der Erstinstallation `.env`,
3. erzeugt ein zufaelliges PostgreSQL-Passwort,
4. validiert `docker-compose.images.yml`,
5. zieht Anwendungs- und PostgreSQL-Image,
6. startet beide Container.

Standardmaessig ist die Webanwendung erreichbar unter:

```text
http://SERVER-IP:18083
```

### Netzwerk/Sicherheit

**Nur die Webanwendung wird auf dem Docker-Host veroeffentlicht.**

```text
Host/LAN -> APP_PORT:8000 -> Schulungsplantool -> postgres:5432
                                             private Docker network
```

PostgreSQL hat bewusst **kein `ports:`-Mapping**. Port 5432 ist deshalb nicht am Docker-Host/LAN veroeffentlicht. Die Anwendung erreicht PostgreSQL ausschliesslich intern ueber den Servicenamen `postgres` im Compose-Netz `schulungsplantool_backend`.

## Compose-Dateien

### Produktion / fertige Images

```text
docker-compose.images.yml
```

Verwendet standardmaessig:

```text
ghcr.io/syschelle/schulungsplantool:0.2.24
```

Das Release-Image enthaelt `linux/amd64` und `linux/arm64`; Docker waehlt automatisch die passende Architektur.

Manueller Produktionsstart:

```bash
docker compose -f docker-compose.images.yml pull
docker compose -f docker-compose.images.yml up -d
```

### Lokaler Build / Entwicklung

```text
docker-compose.yml
```

Diese Compose-Datei baut die Anwendung lokal aus dem `Dockerfile`:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

Auch hier wird PostgreSQL nicht auf dem Host veroeffentlicht.

## Konfiguration

Wichtige Werte in `.env`:

| Variable | Standard | Bedeutung |
|---|---|---|
| `APP_BIND` | `0.0.0.0` | Bind-Adresse des einzigen veroeffentlichten Webports |
| `APP_PORT` | `18083` | Webport des Schulungsplantools |
| `TZ` | `Europe/Berlin` | Zeitzone |
| `MAX_UPLOAD_MB` | `25` | maximale Uploadgroesse pro Datei |
| `POSTGRES_DB` | `schulungsplantool` | interner Datenbankname |
| `POSTGRES_USER` | `schulungsplantool` | interner Datenbankbenutzer |
| `POSTGRES_PASSWORD` | zufaellig durch Installer | Datenbankpasswort; nicht committen |
| `DATABASE_URL` | intern auf `postgres:5432` | Verbindung der App zur Datenbank |

Wenn die Webapp nur lokal bzw. hinter einem Reverse Proxy erreichbar sein soll:

```text
APP_BIND=127.0.0.1
```

## Update

```bash
./update.sh
```

Das Skript fuehrt bei einer Git-Installation `git pull --ff-only` aus, zieht anschliessend die Images aus `docker-compose.images.yml` und startet die Container neu. Das PostgreSQL-Volume bleibt erhalten.

Alternativ manuell:

```bash
git pull --ff-only
docker compose -f docker-compose.images.yml pull
docker compose -f docker-compose.images.yml up -d --remove-orphans
```

**Nicht** `docker compose down -v` verwenden, wenn die gespeicherten Schulungsinhalte erhalten bleiben sollen.

## Datenbank sichern

```bash
./scripts/backup-db.sh
```

Die Sicherung wird lokal unter `backups/` als komprimierter SQL-Dump abgelegt. Dabei wird ebenfalls standardmaessig `docker-compose.images.yml` verwendet.

## Status und Logs

```bash
docker compose -f docker-compose.images.yml ps
docker compose -f docker-compose.images.yml logs -f schulungsplantool
docker compose -f docker-compose.images.yml logs -f postgres
```

Healthcheck:

```bash
curl http://127.0.0.1:18083/api/health
```

Erwartet:

```json
{"status":"ok","version":"0.2.24"}
```

## GitHub Container Registry

Bei einem Release-Tag wie `v0.2.24` baut `.github/workflows/release-image.yml` nach erfolgreichem Test automatisch:

- `linux/amd64`
- `linux/arm64`

und veroeffentlicht:

```text
ghcr.io/syschelle/schulungsplantool:0.2.24
ghcr.io/syschelle/schulungsplantool:latest
```

Damit eine Installation ohne `docker login ghcr.io` moeglich ist, muss das GHCR-Package oeffentlich sein.

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

Bei einem Release-Tag wie `v0.2.24` baut der Workflow `.github/workflows/release-image.yml` zusaetzlich ein Multi-Arch-Image fuer:

- `linux/amd64` (x86_64)
- `linux/arm64` (z. B. Raspberry Pi 5)

und veroeffentlicht es als:

```text
ghcr.io/syschelle/schulungsplantool:0.2.24
ghcr.io/syschelle/schulungsplantool:latest
```

Damit das Image ohne `docker login` installiert werden kann, muss das GHCR-Package oeffentlich sein. Bei einem privaten Package ist vor `docker compose pull` eine Anmeldung an `ghcr.io` erforderlich.

## Repository-Struktur

```text
.
├── app/                    # FastAPI-Backend und statisches Browser-Frontend
├── docs/                   # technische Analyse/Dokumentation
├── scripts/                # Installation, Update und Datenbank-Backup
├── tests/                  # automatisierte Tests
├── .github/workflows/      # CI
├── Dockerfile
├── docker-compose.yml          # lokaler Build/Test
├── docker-compose.images.yml   # Produktion mit GHCR-Image
├── install.sh                  # einfacher Produktions-Installer
├── update.sh                   # einfacher Produktions-Updater
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
