# Changelog

## v0.2.23 - 2026-09-02

### GHCR Multi-Arch Deployment

- GitHub-Release-Workflow fuer Container-Images hinzugefuegt
- Release-Tags `vX.Y.Z` bauen und veroeffentlichen automatisch `linux/amd64` und `linux/arm64`
- Images werden nach `ghcr.io/syschelle/schulungsplantool` gepusht
- Release-Image erhaelt den Versions-Tag sowie `latest`
- Workflow validiert, dass Git-Tag und `VERSION` uebereinstimmen
- Docker Buildx und QEMU fuer Multi-Arch-Builds integriert
- SBOM und Build-Provenance fuer Release-Images aktiviert
- `docker-compose.yml` verwendet standardmaessig das fertige GHCR-Image statt eines lokalen Builds
- Installation und Updates verwenden `docker compose pull`
- x86_64/amd64- und arm64-Systeme verwenden dieselbe Compose-Datei
- Version auf v0.2.23 angehoben

## v0.2.22 - 2026-09-02

### Deployment und Git-Repository

- vorhandenen Stand v0.2.21 als Grundlage uebernommen
- Repository von lokalen Entwicklungsartefakten bereinigt
- Docker-Deployment fuer eine einfache Installation gehaertet
- PostgreSQL bleibt der einzige persistente Anwendungsdienst
- Anwendungscontainer laeuft als unprivilegierter Benutzer
- explizite Healthchecks fuer Anwendung und PostgreSQL
- `.env.example` um Bind-Adresse, Zeitzone und sichere Produktionshinweise erweitert
- Installationsskript `scripts/install.sh` mit automatischer Erzeugung eines zufaelligen Datenbankpassworts hinzugefuegt
- Update-Skript `scripts/update.sh` hinzugefuegt
- PostgreSQL-Backupskript `scripts/backup-db.sh` hinzugefuegt
- GitHub-CI fuer Tests, Compose-Validierung und Docker-Build hinzugefuegt
- `Aufgabe/`, Upload-Ausgangsmaterial, lokale `.env`, Caches und `node_modules` sind nicht Teil des Docker-Images
- Version auf v0.2.22 angehoben

## v0.2.21 - 2026-09-02

- Hamburger-Menuebutton links im Header angeordnet
- Produkt-/Titelblock direkt rechts daneben positioniert
- aktuelle Produkt- und Planungskontexte im Header beibehalten
