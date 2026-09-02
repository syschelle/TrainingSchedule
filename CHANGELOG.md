# Changelog

## v0.2.28 - 2026-09-02

### Begrenzte Markdown-Historie und verbesserte Vorschau

- pro Schulungsinhalt werden dauerhaft maximal 5 Markdown-Historienstaende gespeichert
- beim Speichern oder Wiederherstellen einer sechsten Version wird automatisch der aelteste Historieneintrag entfernt
- vorhandene Datenbanken mit mehr als 5 Historieneintraegen pro Schulungsinhalt werden beim Start automatisch auf die 5 neuesten Staende bereinigt
- die Historienanzeige weist sichtbar auf das Maximum von 5 gespeicherten Staenden hin
- Markdown-Ueberschriften der Ebene 2 werden in der Live-Vorschau in der Primaerfarbe dargestellt
- Markdown-Ueberschriften der Ebene 3 werden in der Live-Vorschau in einer davon abweichenden Erfolgsfarbe dargestellt
- automatisierte Regressionstests fuer Historienlimit, Altbestandsbereinigung und Vorschauformatierung hinzugefuegt
- Version auf v0.2.28 angehoben

## v0.2.27 - 2026-09-02

### DOCX Import/Export fuer Schulungspunkte

- Markdown-Schulungspunkte koennen direkt aus dem Editor als Word-kompatible `.docx` exportiert werden
- exportierte DOCX-Dateien enthalten einen sichtbaren Hinweis zu erlaubten und nicht erlaubten Inhalten fuer den Re-Import
- DOCX-Import konvertiert Ueberschriften, normalen Text, Fett/Kursiv, Aufzaehlungen und Nummerierungen zurueck in Markdown
- der DOCX-Import speichert nicht automatisch; der Inhalt wird zuerst zur Kontrolle in den Editor geladen
- nach bestaetigtem Speichern wird der Historieneintrag als `DOCX importiert` gekennzeichnet
- jedes eingebettete Bild bzw. jeder Screenshot fuehrt zur vollstaendigen Ablehnung des Imports
- ebenfalls abgelehnt werden Grafiken/Formen/Textfelder, Tabellen, Diagramme/SmartArt, eingebettete Objekte, Hyperlinks, Fuss-/Endnoten und offene nachverfolgte Aenderungen
- DOCX-Dateien werden ausschliesslich im Request-Speicher verarbeitet und nicht persistent gespeichert
- ZIP-/OOXML-Paketpruefungen begrenzen interne Dateianzahl und entpackte Groesse und verhindern unzulaessige Pfade
- `python-docx` wird lokal im Anwendungscontainer verwendet; es gibt keine Cloud- oder Office-365-Abhaengigkeit
- automatisierte DOCX-Regressionstests hinzugefuegt
- Version auf v0.2.27 angehoben

## v0.2.26 - 2026-09-02

### Markdown-Schulungspunkte und Aenderungshistorie

- beim gewaehlten Schulungsinhalt gibt es den Button `Schulungspunkte bearbeiten`
- integrierter lokaler Markdown-Editor mit Toolbar und Live-Vorschau
- Markdown-Schulungspunkte werden produktbezogen in PostgreSQL gespeichert
- pro Schulungsinhalt wird eine persistente Aenderungshistorie gefuehrt
- gespeicherte Historienstaende koennen direkt im Editor wiederhergestellt werden
- Wiederherstellungen werden selbst als neuer Historieneintrag protokolliert
- bestehende Datenbanken werden beim Start automatisch um das Markdown-Feld erweitert
- der Kalender-Hinweis `Keine sichtbaren Bloecke.` wurde entfernt; leere Kalenderbereiche bleiben leer
- keine externe CDN- oder Cloud-Abhaengigkeit fuer den Editor
- Version auf v0.2.26 angehoben

## v0.2.25 - 2026-09-02

### Traefik Subpath Deployment

- Frontend-Assets verwenden relative URLs und funktionieren damit sowohl am Webroot als auch unter `/trainingschedule/`
- API-Aufrufe im Browser verwenden relative URLs und bleiben hinter Traefik `StripPrefix` innerhalb des konfigurierten Subpaths
- Regressionstests pruefen, dass keine absoluten `/styles.css`, `/app.js` oder `/api/...`-Pfade wieder eingefuehrt werden
- `docker-compose.images.yml` verwendet fuer den Produktivbetrieb standardmaessig `ghcr.io/syschelle/schulungsplantool:latest`
- Version auf v0.2.25 angehoben

## v0.2.24 - 2026-09-02

### Image-Compose und isolierte PostgreSQL-Datenbank

- separates `docker-compose.images.yml` fuer den produktiven Betrieb mit GHCR-Image hinzugefuegt
- `docker-compose.yml` bleibt als lokaler Build-/Entwicklungsmodus erhalten
- Produktionsinstallation verwendet standardmaessig `docker-compose.images.yml`
- PostgreSQL besitzt in beiden Compose-Dateien bewusst keinerlei Host-Port-Mapping
- nur der Webport der FastAPI-Anwendung wird auf dem Docker-Host veroeffentlicht
- eigenes privates Compose-Netz `schulungsplantool_backend` fuer App und PostgreSQL definiert
- Root-Skripte `./install.sh` und `./update.sh` als einfache Einstiegspunkte hinzugefuegt
- Install-, Update- und Backup-Skripte verwenden standardmaessig `docker-compose.images.yml`
- CI und Release-Workflow validieren nun beide Compose-Dateien
- Version auf v0.2.24 angehoben

## v0.2.24 - 2026-09-02

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
- Version auf v0.2.24 angehoben

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
