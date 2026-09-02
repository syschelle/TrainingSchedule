# Changelog

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
