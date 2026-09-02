# Changelog

## v0.2.39 - 2026-09-02

### Korrekte deutsche Beschriftung im Schulungsplan

- Der Button `Woche hinzufuegen` wurde in der Schulungsplan-Ansicht in `Woche hinzufügen` umbenannt.
- Die Funktion zum manuellen Hinzufuegen einer Kalenderwoche bleibt unveraendert.
- Auf der ersten Vorschau- und PDF-Uebersichtsseite werden rechts im Kopf jetzt wie auf den folgenden Kalenderseiten `Kunde` und `Standort` angezeigt.
- Die technische Kopfzeile `Seite 1 · Uebersicht` wurde entfernt.

## v0.2.38 - 2026-09-02

### Kompaktere Trainerverwaltung

- Die Trainerverwaltung in den Grunddaten verwendet jetzt kompakte, nebeneinander umbrechende Eingabefelder statt einer vollbreiten Zeile pro Trainer.
- Hinzufuegen und Entfernen sind direkt an der kompakten Trainerliste erreichbar.
- `Enter` speichert den aktuellen Namen und oeffnet direkt das Eingabefeld fuer den naechsten Trainer.
- Neue Trainerfelder werden automatisch fokussiert, damit mehrere Namen schnell hintereinander erfasst werden koennen.
- Auf schmalen Displays bricht die Liste responsiv um, ohne die Lesbarkeit zu verlieren.

## v0.2.37 - 2026-09-02

### Uebersichtsseite, eindeutige Projektdateien und zustandsbehaftete Navigation

- Die PDF-Vorschau beginnt jetzt mit einer eigenen Uebersichtsseite vor den Kalenderseiten.
- Der PDF-Export erzeugt dieselbe Uebersicht als erste A4-Querformat-Seite.
- Kunde und Standort werden in der Planuebersicht, auf der Vorschau-Uebersicht und auf den Kalender-Vorschauseiten explizit angezeigt.
- Auch die Kalenderseiten im PDF weisen Kunde und Standort getrennt aus.
- `Planung exportieren` verwendet einen Dateinamen nach dem Schema `kunde_standort_produkt_datum_uhrzeit.json`.
- Dateinamensbestandteile werden fuer plattformuebergreifende Verwendung bereinigt; Datum und Uhrzeit werden beim Browserdownload lokal erzeugt.
- In `Eingabe` gibt es einen direkten Wechsel zum vorhandenen `Schulungsplan`.
- Der Wechsel zwischen `Eingabe` und `Schulungsplan` ruft die automatische Planung nicht auf und veraendert bestehende Kalenderbloecke nicht.
- Ein neuer Plan wird weiterhin ausschliesslich ueber `Plan erstellen` berechnet.

## v0.2.36 - 2026-09-02

### Eingebetteter Kalenderblock-Editor

- Die Bearbeitung von Kalenderbloecken verwendet keine Browser-`prompt`-Fenster mehr.
- Ein eigener eingebetteter Blockeditor oeffnet sich innerhalb der Webanwendung.
- In einem Fenster koennen Schulungsinhalt, Titel, Blocktyp, Kalenderwoche, Wochentag, Trainer, Startzeit, Endzeit, Dauer, Farbe, Raum, Beschreibung und Hinweise bearbeitet werden.
- Bei Auswahl eines hinterlegten Schulungsinhalts koennen dessen Titel, Beschreibung, Standarddauer, Raum, Hinweise und Farbe direkt in den Editor uebernommen werden.
- Startzeiten werden weiterhin auf das verbindliche 15-Minuten-Raster normalisiert.
- Ungueltige Eingaben werden innerhalb des Editors angezeigt und loesen keine Browser-Dialoge aus.
- Abbrechen schliesst den Editor ohne Aenderung des Kalenderblocks.
- Nach dem Speichern wird die bestehende Live-Validierung ausgefuehrt und die getrennte Planungspruefung aktualisiert.

## v0.2.35 - 2026-09-02

### Separate Planungspruefung

- Validierungshinweise werden nicht mehr oberhalb der Kalenderansicht dargestellt.
- Neue eigene Seite `Planungspruefung` in der Navigation zeigt alle aktuellen Konflikte und Hinweise.
- Die Navigation zeigt bei vorhandenen Hinweisen deren Anzahl an, ohne die Kalenderflaeche zu veraendern.
- Bei Drag-and-Drop und anderen Kalenderaenderungen bleibt die Kalenderposition stabil, weil wachsende Warnlisten nicht mehr Bestandteil der Planungsseite sind.
- Die bestehende Live-Validierung bleibt unveraendert aktiv; nur die Darstellung wurde getrennt.
- Eine konfliktfreie Planung zeigt auf der Pruefungsseite einen kompakten `Keine Konflikte`-Status.

## v0.2.34 - 2026-09-02

### Planungsimport und Viertelstundenraster

- `Planung importieren` wurde aus der Schulungsplan-Anzeige in den Bereich `Eingabe` / `Grunddaten` verschoben.
- `Planung exportieren` bleibt beim Schulungsplan, da dort der aktuell bearbeitete Stand ausgegeben wird.
- automatisch erzeugte Block-Startzeiten werden konsequent auf das 15-Minuten-Raster ausgerichtet.
- nach Schulungen oder 20-30-Minuten-Pausen wird der naechste Block bei Bedarf auf den naechsten Viertelstunden-Slot verschoben.
- Drag-and-Drop und Ausschneiden/Einfuegen bleiben auf dem bestehenden 15-Minuten-Raster.
- manuell eingegebene Block-Startzeiten werden auf die naechste Viertelstunde normalisiert.
- importierte Projektdateien mit aelteren Startzeiten wie `15:05` werden beim Laden auf das Viertelstundenraster normalisiert; die Blockdauer bleibt dabei erhalten.
- die Validierung meldet verbleibende Startzeiten ausserhalb des 15-Minuten-Rasters.

## v0.2.33 - 2026-09-02

### Security

- Entwicklungsabhaengigkeit `pytest` von 9.0.2 auf 9.1.1 aktualisiert.
- Behebt den Dependabot-Hinweis `pytest has vulnerable tmpdir handling` (CVE-2025-71176 / GHSA-6w46-j5rx-g56g); betroffen sind pytest-Versionen kleiner 9.0.3.
- Regressionstest fuer den sicheren pytest-Pin in `requirements-dev.txt` ergaenzt.
- Keine Aenderung an Runtime-Abhaengigkeiten, Datenbankschema oder Anwendungsfunktion.

## v0.2.32 - 2026-09-02

### Security

- `python-multipart` von 0.0.21 auf 0.0.32 aktualisiert.
- `pypdf` von 6.4.1 auf 6.16.2 aktualisiert.
- `requirements-dev.txt` enthaelt Runtime-Abhaengigkeiten nicht mehr indirekt; CI installiert Runtime- und Dev-Abhaengigkeiten getrennt, damit Dependabot-Funde nicht doppelt aus beiden Dateien entstehen.
- Drei CodeQL-High-Funde (`Polynomial regular expression used on uncontrolled data`) im DOCX-Export behoben. Die Erkennung von Markdown-Ueberschriften, Aufzaehlungen und nummerierten Listen verwendet nun deterministische Zeichenanalyse statt regulaerer Ausdruecke.
- Weitere regulaere Ausdruecke im DOCX-Roundtrip wurden aus dem unkontrollierten Markdown-Pfad entfernt, um neue ReDoS-Funde vorzubeugen.
- Regressionstests fuer sehr lange, unkontrollierte Markdown-Zeilen und fehlerhafte Markdown-Marker ergaenzt.

## v0.2.31 - 2026-09-02

### Mehrtrainer-Kalender, Kalender-PDF und Planungsdatei

- mehrere gleichberechtigte Trainer koennen pro Projekt gepflegt werden
- automatische Planung verteilt Schulungen auf verfuegbare Trainer und kann parallele Schulungen einplanen
- jeder Trainer erhaelt pro Kalenderwoche eine eigene Wochenansicht
- Kalenderwochen bleiben chronologisch gruppiert; innerhalb jeder Woche werden die Traineransichten zusammen dargestellt
- Schulungsbloecke koennen per Drag-and-Drop zwischen Trainern, Tagen und Wochen verschoben werden
- Ueberlappungsvalidierung erfolgt trainerbezogen, sodass parallele Schulungen verschiedener Trainer zulaessig sind
- PDF-Export auf A4-Querformat umgestellt
- PDF bildet die Kalenderstruktur mit Zeitachse, Datumswerten, Feiertagshinweisen und farbigen sichtbaren Bloecken ab
- PDF-Seiten werden chronologisch nach Kalenderwoche und Trainer erzeugt
- neue lokale Projektdatei exportiert den vollstaendigen aktuellen Planungsstand als JSON
- Projektdateien koennen wieder importiert werden und stellen den gespeicherten Planungsstand wieder her
- Projektdateien werden nicht dauerhaft serverseitig gespeichert
- bestehendes Feld `trainer` bleibt fuer Abwaertskompatibilitaet erhalten; neue Projekte verwenden zusaetzlich `trainers`
- Version auf v0.2.31 angehoben

---

## v0.2.30 - 2026-09-02

### Dienstleistungstage in der Planuebersicht

- die Planuebersicht zeigt keine separaten Summen mehr fuer Pausen, Mittagspause, Anreise und Abreise
- neu angezeigt werden `Dienstleistungstage`
- als Dienstleistungstag wird jeder Tag genau einmal gezaehlt, an dem mindestens ein Schulungsblock vom Typ `training` geplant ist
- mehrere Schulungsbloecke am selben Tag zaehlen weiterhin nur als ein Dienstleistungstag
- reine Anreise-, Abreise- oder Pausentage werden nicht als Dienstleistungstage gezaehlt
- Schulungszeit und nicht eingeplante Schulungszeit bleiben in der Uebersicht sichtbar
- Regressionstest fuer die neue Uebersichtslogik hinzugefuegt
- Version auf v0.2.30 angehoben

## v0.2.29 - 2026-09-02

### Leere Kundendaten, Kalenderdatum und DACH-Feiertagshinweise

- die Demo-Vorbelegung fuer Kunde und Standort wurde entfernt
- der vorbelegte Trainer wurde entfernt
- Kundendaten und Trainer starten bei neuen bzw. zurueckgesetzten Projekten leer
- bei gesetztem Startdatum zeigt jeder Kalendertag sein konkretes Datum an
- mehrere Kalenderwochen berechnen ihre Datumswerte automatisch aus dem Startdatum
- die Wochenueberschrift zeigt den Datumsbereich Montag bis Freitag
- landesweite Feiertage fuer Deutschland und Oesterreich werden direkt am betreffenden Kalendertag angezeigt
- fuer die Schweiz wird die bundesweit einheitliche Bundesfeier angezeigt
- regionale Feiertage werden bewusst nicht ohne Bundesland-/Kantonsauswahl als sicherer Feiertag markiert
- die Feiertagsberechnung erfolgt vollstaendig lokal im Browser und benoetigt keine externe API
- Version auf v0.2.29 angehoben

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
