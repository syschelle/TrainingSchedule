# Schulungsplantool

Aktuelle Version: **v0.2.47**

## Aenderungen v0.2.47

- Schulungsinhalte koennen ueber `Schulungsblock teilen` fuer die automatische Halbierung aktiviert oder deaktiviert werden.
- Bei aktivierter Option teilt `Plan erstellen` jede benoetigte Schulungssitzung in zwei moeglichst gleich grosse Teile; die Gesamtdauer bleibt erhalten.
- Teil 2 bleibt beim selben Trainer und wird erst nach Teil 1 eingeplant. Passt die zweite Haelfte nicht mehr sinnvoll in den Tag, kann sie an einem folgenden Schulungstag liegen.
- Automatisch erzeugte Teilnehmergruppen werden weiterhin korrekt behandelt: Jede `Gruppe x/y` erhaelt beide Haelften des Schulungsinhalts.
- Die Option wird in PostgreSQL gespeichert. Beim Start wird die neue Spalte `split_enabled` automatisch und rueckwaertskompatibel angelegt; kein manueller SQL-Schritt ist notwendig.

## Aenderungen v0.2.46

- Kalenderkacheln verwenden fuer Schulungsbloecke jetzt eine klare Zeilenstruktur: Zeile 1 = Schulungsinhalt-Titel, Zeile 2 = nur bei Aufteilung `Gruppe x/y`, Zeile 3 = Start-/Endzeit und Gesamtdauer in Stunden.
- Die Teilnehmergruppenbezeichnung bleibt weiterhin ausgeblendet; nur die automatisch erzeugte Gruppennummer wird separat dargestellt.
- Der Schulungsinhalt-Titel wird ueber die `topic_id` aus den hinterlegten Schulungsinhalten ermittelt, damit die erste Zeile nicht aus einem zusammengesetzten Blocktitel abgeleitet werden muss.
- Kalender-Vorschau und PDF-Kalenderseiten verwenden dieselbe Titel-/Gruppen-/Zeitstruktur; strukturierte Projekt- und XLSX-Daten bleiben unveraendert.
- Keine Datenbankmigration erforderlich.

## Aenderungen v0.2.45

- Kalenderkacheln blenden die allgemeine Teilnehmergruppenbezeichnung aus dem sichtbaren Schulungstitel aus.
- Von der automatischen Planung erzeugte Aufteilungen bleiben als `Gruppe 1/2`, `Gruppe 2/2` usw. sichtbar.
- Beispiel: `DU Viewer - Webviewer Gruppe 4/6` wird im Kalender als `DU Viewer - Gruppe 4/6` dargestellt.
- Der intern gespeicherte Blocktitel sowie Planungs-/Validierungsdaten bleiben unveraendert; Kalender-Vorschau und PDF-Kalenderseiten verwenden die kompakte Anzeige.

## Aenderungen v0.2.44

- Titel- und Zeit-/Dauer-Schrift in Kalenderkacheln skalieren jetzt stufenlos mit der Kachelhoehe.
- Beim Ziehen der oberen oder unteren Resize-Kante wird die Typografie live mit der Hoehe aktualisiert.
- Der abrupte Schriftgroessenwechsel beim Uebergang von kurzen zu groesseren Bloecken entfaellt.
- Die kompakte Bedienung kurzer 15-/30-Minuten-Bloecke und das Viertelstundenraster bleiben erhalten.

## Aenderungen v0.2.43

- Schulungsbloecke koennen jetzt direkt im Kalender an Ober- und Unterkante in 15-Minuten-Schritten skaliert werden.
- Beim Ziehen werden Start-/Endzeit und Kachelhoehe live aktualisiert; danach laeuft die bestehende Planungsvalidierung.
- Die Kachel-Metazeile zeigt statt des technischen Blocktyps `training` jetzt die Dauer in Stunden, z. B. `08:30-10:30 · 2,0 h`.
- Auch kompakte 15-/30-Minuten-Kacheln zeigen die Zeit-/Dauerzeile in verkleinerter Form.
- Verschieben kompletter Bloecke zwischen Zeit, Tag, Woche und Trainer bleibt unveraendert verfuegbar.

## Aenderungen v0.2.42

Kurze Kalenderbloecke (15/30 Minuten) verwenden jetzt eine kompakte Darstellung. Die vier Aktionsbuttons werden verkleinert und passen vollstaendig in die Kachel; der Titel kann bis zu zwei Zeilen nutzen. Die zusaetzliche Zeit-/Typ-Zeile wird bei kurzen interaktiven Kacheln ausgeblendet, damit nichts abgeschnitten wird. Der vollstaendige Titel sowie Start- und Endzeit bleiben als Tooltip am Block verfuegbar. Die zeitliche Hoehe des Blocks wird nicht vergroessert, damit die Kalenderachse weiterhin korrekt bleibt.

## Aenderungen v0.2.41

Kalender- und Vorschauwochen werden jetzt nur noch dann angezeigt, wenn sie mindestens einen echten Schulungsblock enthalten. Werden durch Drag-and-Drop, Ausschneiden/Einfuegen, Blockbearbeitung oder Loeschen alle Schulungsbloecke aus einer Woche entfernt, verschwindet diese Woche automatisch aus Kalender, Vorschau und PDF-/XLSX-Export. Eine ueber `Woche hinzufügen` neu angelegte leere Woche bleibt waehrend der aktuellen Bearbeitung sichtbar, damit dort neue Bloecke angelegt werden koennen.

## Aenderungen v0.2.40

In Kalenderkacheln wird der Anreiseblock jetzt kompakt als `Anreise` angezeigt. Der intern gespeicherte Titel `Anreise / Eintreffen der Teilnehmer`, die Planungslogik, Validierung und Exportdaten bleiben unveraendert.

## Aenderungen v0.2.39

Im Schulungsplan wurde die Beschriftung des Buttons zum manuellen Anlegen einer weiteren Woche sprachlich korrigiert: `Woche hinzufügen` ersetzt `Woche hinzufuegen`. Die Funktion selbst bleibt unveraendert. Auf der ersten Vorschau- und PDF-Uebersichtsseite zeigt der rechte Kopfbereich jetzt wie auf den folgenden Kalenderseiten `Kunde` und `Standort`; die technische Anzeige `Seite 1 · Uebersicht` entfällt.

## Aenderungen v0.2.38

Die Trainerverwaltung in den Grunddaten ist jetzt deutlich kompakter: vorhandene Trainer stehen in kleinen, nebeneinander umbrechenden Eingabefeldern, der Entfernen-Button sitzt direkt am jeweiligen Namen und ein kompakter `+ Trainer`-Button fuegt weitere Trainer hinzu. Mit `Enter` kann ein Name gespeichert und sofort das naechste Trainerfeld geoeffnet werden. Die Darstellung bleibt auf kleinen Displays responsiv.

## Aenderungen v0.2.37

Die Schulungsplan-Vorschau beginnt jetzt mit einer eigenen Uebersichtsseite; der PDF-Export verwendet dieselbe Reihenfolge und erzeugt die Uebersicht ebenfalls als erste Seite. Kunde und Standort werden sowohl in der Planuebersicht als auch in der Vorschau und im PDF explizit angezeigt. Projektdateien erhalten beim Export einen zuordenbaren Namen nach dem Schema `kunde_standort_produkt_datum_uhrzeit.json`. Zwischen `Eingabe` und `Schulungsplan` kann direkt gewechselt werden, ohne die automatische Planung erneut aufzurufen. Ein neuer Plan wird ausschliesslich durch `Plan erstellen` erzeugt.

## Aenderungen v0.2.36

Kalenderbloecke werden jetzt in einem eingebetteten Bearbeitungsfenster innerhalb der Anwendung bearbeitet. Die bisherigen Browser-`prompt`-Dialoge fuer Titel, Zeit und Trainer entfallen. Im neuen Editor koennen Schulungsinhalt, Titel, Blocktyp, Kalenderwoche, Wochentag, Trainer, Start, Ende, Dauer, Farbe, Raum, Beschreibung und Hinweise gemeinsam angepasst werden. Startzeiten bleiben auf dem 15-Minuten-Raster. Fehler bei der Eingabe werden direkt im Fenster angezeigt und erzeugen keine Browser-Dialoge.

## Aenderungen v0.2.35

Validierungshinweise befinden sich jetzt auf der eigenen Seite `Planungspruefung` und nicht mehr oberhalb der Kalenderansicht. Dadurch veraendert eine wachsende Konfliktliste beim Drag-and-Drop nicht mehr die Hoehe der Planungsseite und die Kalenderposition bleibt stabil. Die Navigation zeigt die aktuelle Anzahl der Hinweise an.

### Enthaltene Aenderungen aus v0.2.34

`Planung importieren` befindet sich bei `Eingabe` / `Grunddaten`. Die Planungsansicht enthaelt weiterhin den Export des aktuellen Standes, aber keinen Import-Button mehr.

Alle Kalenderblock-Startzeiten werden auf ein festes 15-Minuten-Raster normalisiert (`:00`, `:15`, `:30`, `:45`). Das gilt fuer die automatische Planung, Drag-and-Drop, manuelle Blockbearbeitung sowie fuer wieder eingelesene Projektdateien. Beim Import wird die vorhandene Blockdauer beibehalten.

## Security-Hinweis v0.2.33

Die Entwicklungsabhaengigkeit `pytest` ist auf `9.1.1` aktualisiert. Damit liegt sie oberhalb der fuer CVE-2025-71176 / GHSA-6w46-j5rx-g56g gepatchten Mindestversion `9.0.3`. Die Aenderung betrifft ausschliesslich Tests und CI; das Produktionsimage erhaelt dadurch keine zusaetzliche Runtime-Abhaengigkeit.

## Security-Hinweis v0.2.32

Dieser Stand aktualisiert die direkt verwendeten Pakete `python-multipart` auf `0.0.32` und `pypdf` auf `6.16.2`. Die von CodeQL gemeldeten polynomialen regulaeren Ausdruecke im DOCX-Export wurden durch deterministische Parser fuer Markdown-Ueberschriften, Listen und Inline-Formatierung ersetzt. `requirements-dev.txt` referenziert die Runtime-Abhaengigkeiten nicht mehr; CI installiert `requirements.txt` und `requirements-dev.txt` separat.

Lokale Webanwendung zur Erstellung, Bearbeitung, Validierung und zum Export mehrtaegiger Schulungsplaene. Die Anwendung laeuft vollstaendig in Docker und verwendet PostgreSQL fuer den strukturierten Schulungsinhalte-Katalog.

## Funktionen

- Projektdaten, Planungsregeln, mehrere gleichberechtigte Trainer und konkrete Schulungsthemen
- Produktverwaltung und produktbezogener Schulungsinhalte-Katalog
- Teilnehmergruppen, maximale Teilnehmerzahl und Abhaengigkeiten zwischen Schulungen
- automatische Planung fuer Montag bis Donnerstag, optional Freitag
- mehrere Schulungswochen
- Kernarbeitszeiten, Anreise-, Abreise-, Pausen- und Mittagspausenregeln
- Kalenderansicht mit Viertelstundenraster, konkreten Datumswerten und eigener Wochenansicht je Trainer
- lokale DACH-Feiertagshinweise direkt am Kalendertag (DE/AT landesweit, CH Bundesfeier)
- Drag-and-Drop von Schulungsbloecken zwischen Zeiten, Tagen, Wochen und Trainern
- Ausschneiden und Einfuegen von Bloecken
- Live-Validierung
- Planuebersicht mit Schulungszeit, nicht eingeplanter Zeit und Dienstleistungstagen
- Kalender-Druckvorschau
- PDF-Export im A4-Querformat als Kalenderansicht sowie XLSX-Export
- exportier- und wieder importierbare Projektdatei fuer einen exakten Planungsstand
- PostgreSQL-Katalog fuer dauerhaft gepflegte Schulungsinhalte
- Markdown-Editor fuer detaillierte Schulungspunkte je Schulungsinhalt
- persistente Aenderungshistorie mit Wiederherstellung gespeicherter Markdown-Staende
- DOCX-Export und -Import fuer Schulungspunkte mit strengem Inhaltsfilter

## Datenschutz

Hochgeladene Excel-, PDF- oder DOCX-Dateien werden nicht in PostgreSQL oder Docker-Volumes abgelegt. Die Import-APIs verarbeiten Uploads nur im Request-Speicher. Der Quellordner `Aufgabe/`, lokale Quelldokumente sowie `Aufgabe.md` werden durch `.dockerignore` nicht in das Anwendungsimage uebernommen.

Persistiert wird ausschliesslich das PostgreSQL-Volume fuer strukturierte Produkt- und Schulungsinhalte. Dazu gehoeren auch die Markdown-Schulungspunkte und deren Aenderungshistorie.

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
ghcr.io/syschelle/schulungsplantool:latest
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
{"status":"ok","version":"0.2.42"}
```

## GitHub Container Registry

Bei einem Release-Tag wie `v0.2.47` baut `.github/workflows/release-image.yml` nach erfolgreichem Test automatisch:

- `linux/amd64`
- `linux/arm64`

und veroeffentlicht:

```text
ghcr.io/syschelle/schulungsplantool:0.2.47
ghcr.io/syschelle/schulungsplantool:latest
```

Damit eine Installation ohne `docker login ghcr.io` moeglich ist, muss das GHCR-Package oeffentlich sein.

## Entwicklung und Tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
uvicorn app.server.main:app --reload
```

GitHub Actions prueft bei Pushes und Pull Requests automatisch:

- Python-Tests
- Docker-Compose-Konfiguration
- Docker-Image-Build

Bei einem Release-Tag wie `v0.2.47` baut der Workflow `.github/workflows/release-image.yml` zusaetzlich ein Multi-Arch-Image fuer:

- `linux/amd64` (x86_64)
- `linux/arm64` (z. B. Raspberry Pi 5)

und veroeffentlicht es als:

```text
ghcr.io/syschelle/schulungsplantool:0.2.47
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

## Traefik / Betrieb unter einem URL-Unterpfad

Ab v0.2.25 kann die Weboberflaeche sowohl direkt unter `/` als auch hinter einem Reverse Proxy unter einem Unterpfad wie `/trainingschedule/` betrieben werden. Frontend-Assets und Browser-API-Aufrufe verwenden relative URLs. Bei Traefik kann der Prefix daher mit `StripPrefix` entfernt werden, bevor die Anfrage an den Container-Port `8000` weitergeleitet wird.

Das Produktions-Compose verwendet standardmaessig `ghcr.io/syschelle/schulungsplantool:latest`. Mit `APP_IMAGE` in `.env` kann bei Bedarf weiterhin gezielt eine feste Image-Version gesetzt werden.


## Kalenderdatum und DACH-Feiertagshinweise

Sobald ein Startdatum gesetzt ist, zeigt die Kalenderansicht neben jedem Wochentag das konkrete Datum an. Weitere manuell oder automatisch angelegte Wochen werden jeweils um sieben Tage fortgeschrieben. Das Startdatum wird wie im Export der zugehoerigen Kalenderwoche zugeordnet; die Kalenderansicht beginnt dabei am Montag dieser Woche.

Direkt am betroffenen Kalendertag koennen Feiertagshinweise erscheinen. Die Berechnung erfolgt vollstaendig lokal im Browser und benoetigt keine externe Feiertags-API. Beruecksichtigt werden die landesweit geltenden Feiertage fuer Deutschland und Oesterreich sowie die Schweizer Bundesfeier. Regionale Feiertage sind ohne Auswahl von Bundesland bzw. Kanton nicht eindeutig und werden deshalb derzeit bewusst nicht als sicher geltender Feiertag angezeigt.

## Markdown-Schulungspunkte

Unter `Schulungsinhalte` kann beim ausgewaehlten Inhalt ueber `Schulungspunkte bearbeiten` ein lokaler Markdown-Editor geoeffnet werden. Der Editor zeigt den aktuell gespeicherten Inhalt, bietet eine Live-Vorschau und speichert den Markdown-Quelltext direkt in PostgreSQL.

Bei jeder inhaltlichen Aenderung wird ein neuer Historienstand gespeichert. Pro Schulungsinhalt werden dauerhaft maximal 5 Historienstaende vorgehalten; beim Speichern einer sechsten Version wird automatisch der aelteste Stand entfernt. Bereits vorhandene Historien mit mehr als 5 Eintraegen werden beim Anwendungsstart auf die 5 neuesten Staende reduziert. Die gespeicherten Versionen koennen im Editor wiederhergestellt werden. Wiederherstellungen werden ebenfalls als neuer Historieneintrag protokolliert und unterliegen derselben 5-Versionen-Grenze. In der Live-Vorschau werden Markdown-Ueberschriften der Ebenen 2 und 3 zur besseren visuellen Unterscheidung unterschiedlich farbig dargestellt. Der Editor verwendet keine externe CDN- oder Cloud-Verbindung.


### DOCX Import und Export fuer Schulungspunkte

Im Markdown-Editor kann der aktuell angezeigte Schulungsinhalt als `.docx` exportiert und spaeter wieder importiert werden. Der Export enthaelt einen sichtbaren Bearbeitungshinweis mit den fuer den Re-Import erlaubten und nicht erlaubten Word-Inhalten.

Zulaessig fuer den Re-Import sind:

- Ueberschriften Ebene 1-3
- normaler Text
- Fett und Kursiv
- Aufzaehlungen
- Nummerierungen

Nicht zulaessig sind insbesondere:

- Bilder und Screenshots
- Grafiken, Formen und Textfelder
- Tabellen
- Diagramme und SmartArt
- eingebettete Dateien/Objekte
- Hyperlinks
- Fuss- und Endnoten
- nicht angenommene nachverfolgte Aenderungen

**Bilder und Screenshots werden nicht stillschweigend entfernt.** Enthält das DOCX ein Bild bzw. eine Grafik, wird der gesamte Import mit einer klaren Fehlermeldung abgelehnt und der vorhandene Schulungsinhalt bleibt unveraendert.

Ein erfolgreicher DOCX-Import wird zuerst nur in den Markdown-Editor geladen. Erst nach Sichtpruefung und Klick auf `Schulungspunkte speichern` wird der Inhalt in PostgreSQL uebernommen. Dieser Speichervorgang erscheint in der Aenderungshistorie als `DOCX importiert`. Die hochgeladene DOCX-Datei selbst wird nicht gespeichert.
## Dienstleistungstage in der Planuebersicht

Die Planuebersicht zeigt keine separaten Summen mehr fuer normale Pausen, Mittagspause, Anreise oder Abreise. Stattdessen wird die Anzahl der `Dienstleistungstage` ausgewiesen. Gezaehlt wird jeder Tag einer Schulungswoche genau einmal, an dem mindestens ein Block vom Typ `training` geplant ist. Mehrere Schulungsbloecke am selben Tag erhoehen die Anzahl der Dienstleistungstage daher nicht. Tage, die ausschliesslich Anreise, Abreise oder Pausen enthalten, werden nicht als Dienstleistungstag gezaehlt.



## Mehrere Trainer

Ein Projekt kann mehrere Trainer enthalten. Alle Trainer gelten fachlich als gleichberechtigt und koennen deshalb jeden Schulungsinhalt uebernehmen. Die automatische Planung verteilt Schulungsbloecke auf die verfuegbaren Trainer und kann Schulungen parallel auf demselben Kalendertag einplanen.

In der Kalenderansicht wird jede Kalenderwoche chronologisch gruppiert. Innerhalb einer Kalenderwoche besitzt jeder Trainer eine eigene Montag-bis-Freitag-Wochenansicht mit denselben Datumswerten. Schulungsbloecke koennen per Drag-and-Drop zwischen den Traineransichten verschoben werden; beim Ablegen wird die Trainerzuordnung des Blocks aktualisiert.

## Planungsstand exportieren und importieren

Ueber `Planung exportieren` wird der komplette aktuelle Projektzustand als lokale `*.schulungsplan.json`-Datei ausgegeben. Enthalten sind unter anderem Projektdaten, Trainer, Teilnehmergruppen, Planungsregeln, Themen, manuelle Wochen, alle Kalenderbloecke, Trainerzuordnungen, nicht eingeplante Themen und Warnungen.

`Planung importieren` steht auf der Seite `Eingabe` im Bereich `Grunddaten`, validiert eine zuvor exportierte Projektdatei und stellt diesen Planungsstand wieder her. Die Datei wird nur fuer den Request verarbeitet und nicht dauerhaft auf dem Server gespeichert. Der PostgreSQL-Schulungsinhalte-Katalog ist davon unabhaengig und wird nicht in die Projektdatei kopiert.

## PDF-Kalenderexport

Der PDF-Export wird ab v0.2.32 als A4-Querformat erzeugt. Die Seiten folgen derselben chronologischen Struktur wie die Kalender-/Druckvorschau: zuerst Kalenderwoche, darin je Trainer eine eigene Wochenansicht. Bei mehreren Trainern und mehreren Wochen entstehen die PDF-Seiten in der Reihenfolge `Woche 1 / Trainer 1`, `Woche 1 / Trainer 2`, danach `Woche 2 / Trainer 1` usw.

Der PDF-Kalender zeigt dieselbe Montag-bis-Freitag-Zeitachse, Datumswerte, DACH-Feiertagshinweise sowie die farbigen sichtbaren Schulungs-, Anreise- und Abreisebloecke. Normale Pausen und Mittagspausen bleiben wie in der Browser-Kalenderansicht ausgeblendet.
