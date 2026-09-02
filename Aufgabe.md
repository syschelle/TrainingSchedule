# Projekt: Schulungsplantool

Erstelle eine vollständige, produktionsfähige Webanwendung mit dem Projektnamen **„Schulungsplantool“**.

  
Diese Datei muss vor jeder Verarbeitung von Prompts in diesem Chat verarbeitet werden. Gibt es Änderungen, Anpassungen oder Neuerungen so muss das in dieser Datei dokumentiert werden.

## 1. Ziel der Anwendung

Die Anwendung soll aus bereitgestellten Excel-Dateien und bestehenden Schulungsplänen im PDF-Format automatisch einen strukturierten Schulungsplan erstellen.

Die **Excel-Datei dient als Eingabegrundlage** für die zu planenden Schulungen, Teilnehmer, Themen, Zeiten oder sonstigen dort enthaltenen Planungsinformationen.

Die bereitgestellten **PDF-Dateien mit bestehenden Schulungsplänen dienen als fachliche und strukturelle Referenz**. Analysiere deren Aufbau, Inhalte, Reihenfolge der Schulungsthemen, typische Dauer der Schulungsblöcke und Darstellungsform.

Die Anwendung soll daraus einen neuen Schulungsplan erzeugen, der anschließend im Browser vollständig angepasst werden kann.

---

# 2. Datenschutz / Dateiverarbeitung

Sehr wichtig:

- Es dürfen **keine hochgeladenen Excel- oder PDF-Dateien dauerhaft gespeichert werden**.
- Dateien dürfen ausschließlich temporär bzw. im Arbeitsspeicher verarbeitet werden.
- Nach Abschluss der Verarbeitung oder spätestens beim Beenden der Session müssen die temporären Daten gelöscht werden.
- Keine Speicherung der Originaldateien in einer Datenbank.
- Keine Speicherung in Cloud-Diensten.
- Keine Übertragung der Dateien an externe Dienste.
- Die Anwendung muss vollständig lokal bzw. innerhalb der eigenen Docker-Umgebung funktionieren.
- Auch die fachliche Analyse der Dateien soll lokal erfolgen.
- Falls temporäre Dateien technisch notwendig sind, müssen sie nach der Verarbeitung zuverlässig gelöscht werden.

---

# 3. Deployment

Die komplette Anwendung muss über **Docker** betrieben werden können.

Bereitzustellen sind mindestens:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- README mit Installations- und Startanleitung
- Healthcheck
- persistente Speicherung ausschließlich für notwendige Anwendungseinstellungen, sofern überhaupt erforderlich

Die hochgeladenen Schulungsdateien dürfen ausdrücklich **nicht in Docker-Volumes persistiert werden**.

Die Anwendung soll beispielsweise mit folgendem Befehl startbar sein:

```bash
docker compose up -d
```

---

# 4. Moderne Weboberfläche

Erstelle eine moderne, übersichtliche und responsive Weboberfläche.

Die Oberfläche soll für Desktop-Bildschirme optimiert sein, aber auch auf Tablets sinnvoll funktionieren.

Das Design soll professionell und klar sein, beispielsweise:

- moderne Karten
- klare Typografie
- dezente Farben
- übersichtliche Navigation
- verständliche Icons
- Drag-and-Drop, wo sinnvoll
- sofort sichtbare Validierungsfehler
- keine technisch wirkende Administrationsoberfläche

Die Anwendung soll mindestens folgende Bereiche besitzen:

1. **Dateien einlesen**
2. **Grunddaten**
3. **Schulungsthemen**
4. **Automatische Planung**
5. **Schulungsplan bearbeiten**
6. **Vorschau**
7. **Export**

---

# 5. Excel-Import

Analysiere die bereitgestellte Excel-Datei und verwende deren tatsächliche Struktur.

Keine festen Spaltennamen erfinden, wenn diese aus der bereitgestellten Excel-Datei ermittelt werden können.

Beim Import:

- Tabellenblätter erkennen
- Spalten erkennen
- relevante Schulungsinformationen übernehmen
- leere oder ungültige Zeilen erkennen
- Datums- und Zeitangaben korrekt interpretieren
- Dubletten möglichst erkennen
- Importergebnis vor der Übernahme anzeigen

Der Anwender soll anschließend Daten korrigieren oder ergänzen können.

---

# 6. PDF-Schulungspläne als Vorlage

Analysiere die bereitgestellten PDF-Schulungspläne.

Ermittle daraus insbesondere:

- typische Struktur eines Schulungstages
- Schulungsthemen
- Reihenfolge der Themen
- typische Dauer einzelner Themen
- Gruppierung zusammengehörender Themen
- Pausenzeiten
- Mittagspause
- Beginn und Ende eines Schulungstages
- Besonderheiten am Anreise- und Abreisetag
- Aufbau und Layout des fertigen Schulungsplans

Die PDFs dienen als **fachliche Referenz**.

Die Anwendung soll daraus sinnvolle Standardwerte ableiten.

---

# 7. Planungszeitraum

Schulungen finden grundsätzlich statt:

**Montag bis Donnerstag**

Freitag, Samstag und Sonntag dürfen standardmäßig nicht für Schulungen eingeplant werden.

Die Anwendung soll einen Schulungszeitraum auswählen können.

Beispiel:

- Montag, 07.09.2026
- Dienstag, 08.09.2026
- Mittwoch, 09.09.2026
- Donnerstag, 10.09.2026

---

# 8. Kernarbeitszeit

Die reguläre Kernzeit eines Schulungstages ist:

**08:30 Uhr bis 17:00 Uhr**

Innerhalb dieses Zeitraums müssen Schulungseinheiten, Pausen und Mittagspause geplant werden.

Die Kernarbeitszeiten sollen als Standardeinstellung vorbelegt sein, aber in den Einstellungen konfigurierbar bleiben.

Standard:

```text
Tagesbeginn: 08:30
Tagesende:   17:00
```

---

# 9. Montag: definierbares Anreisefenster

Für Montag muss ein **Anreisefenster** definierbar sein.

Beispielsweise:

```text
Anreise Montag:
08:30 - 10:00 Uhr
```

In diesem Zeitraum dürfen keine normalen Schulungsblöcke eingeplant werden.

Das Anreisefenster soll im fertigen Plan als eigener Block dargestellt werden können.

Bezeichnung beispielsweise:

**Anreise / Eintreffen der Teilnehmer**

Start- und Endzeit müssen vom Benutzer frei eingestellt werden können.

---

# 10. Donnerstag: definierbares Abreisefenster

Für Donnerstag muss ein **Abreisefenster** definierbar sein.

Beispielsweise:

```text
Abreise Donnerstag:
15:00 - 17:00 Uhr
```

Ab Beginn dieses Fensters dürfen keine weiteren normalen Schulungsblöcke eingeplant werden.

Das Abreisefenster soll als eigener Block im Schulungsplan erscheinen können.

Bezeichnung beispielsweise:

**Abreise**

Start- und Endzeit müssen frei definierbar sein.

---

# 11. Schulungsblöcke

Ein Schulungstag kann aus mehreren unterschiedlichen Schulungsthemen bestehen.

Beispiel:

```text
08:30 - 10:00   Einführung
10:00 - 10:25   Pause
10:25 - 11:45   Systemübersicht
11:45 - 12:10   Pause
12:10 - 12:55   Administration
12:55 - 13:40   Mittagspause
13:40 - 15:10   Praktische Übungen
15:10 - 15:35   Pause
15:35 - 17:00   Fehleranalyse
```

Es darf ausdrücklich **mehr als ein Schulungsthema pro Tag** geben.

Ein Schulungsthema muss mindestens folgende Eigenschaften besitzen:

- Titel
- optionale Beschreibung
- Dauer
- Priorität
- optional gewünschter Tag
- optional gewünschte Reihenfolge
- optional Abhängigkeit von einem anderen Thema
- optional Trainer
- optional Raum
- optional Hinweise

Die Dauer soll z. B. in Minuten angegeben werden können.

---

# 12. Pausenregel

Zwischen zwei größeren Schulungsblöcken soll grundsätzlich eine Pause eingeplant werden.

Die Pausen sollen:

**mindestens 20 Minuten und maximal 30 Minuten dauern.**

Standardwert:

**25 Minuten**

Die Anwendung soll automatisch sinnvolle Pausen einplanen.

Der Anwender muss die Pausen später manuell verändern können.

Die automatische Planung muss jedoch sicherstellen, dass eine Pause standardmäßig im Bereich von 20–30 Minuten liegt.

---

# 13. Mittagspause

Pro vollständigem Schulungstag muss eine Mittagspause von:

**45 Minuten**

eingeplant werden.

Standardmäßig sollte die Mittagspause sinnvoll ungefähr im Bereich zwischen 12:00 und 14:00 Uhr liegen.

Die genaue Lage kann vom Algorithmus abhängig von den Schulungsblöcken gewählt werden.

Die Mittagspause muss in der Oberfläche manuell verschiebbar sein.

Standarddauer:

```text
45 Minuten
```

---

# 14. Automatische Planung

Die Anwendung benötigt einen automatischen Planungsalgorithmus.

Dieser soll aus den vorhandenen Schulungsthemen einen möglichst sinnvollen Plan von Montag bis Donnerstag erstellen.

Dabei gelten folgende Regeln:

 1. Schulungen nur Montag bis Donnerstag.
 2. Kernarbeitszeit grundsätzlich 08:30–17:00 Uhr.
 3. Montags das konfigurierte Anreisefenster berücksichtigen.
 4. Donnerstags das konfigurierte Abreisefenster berücksichtigen.
 5. Zwischen Schulungsblöcken Pausen von 20–30 Minuten einplanen.
 6. Eine Mittagspause von 45 Minuten vorsehen.
 7. Mehrere unterschiedliche Schulungsthemen dürfen an einem Tag stattfinden.
 8. Themen dürfen nicht zeitlich überlappen.
 9. Prioritäten und gewünschte Reihenfolgen berücksichtigen.
10. Abhängigkeiten zwischen Themen berücksichtigen.
11. Die verfügbare Zeit möglichst sinnvoll ausnutzen.
12. Möglichst keine sehr kurzen Restzeiten erzeugen.
13. Zusammengehörige Themen möglichst sinnvoll gruppieren.
14. Der Plan muss jederzeit manuell korrigierbar sein.

Wenn nicht alle Schulungsthemen in den verfügbaren Zeitraum passen, darf die Anwendung diese nicht einfach abschneiden.

Stattdessen muss deutlich angezeigt werden:

```text
Nicht eingeplante Schulungszeit: 120 Minuten
```

und welche Themen davon betroffen sind.

---

# 15. Interaktive Bearbeitung

Nach der automatischen Erstellung muss der komplette Plan online im Browser bearbeitet werden können.

Gewünscht ist möglichst eine visuelle Wochenansicht.

Beispielsweise Spalten:

```text
Montag | Dienstag | Mittwoch | Donnerstag
```

und darunter eine vertikale Zeitachse.

Schulungsblöcke sollen möglichst per Drag-and-Drop:

- verschoben
- einem anderen Tag zugeordnet
- in der Reihenfolge verändert

werden können.

Außerdem sollen Zeiten und Inhalte über einen Bearbeitungsdialog geändert werden können.

Der Anwender soll:

- neue Blöcke hinzufügen
- Blöcke löschen
- Blöcke duplizieren
- Schulungsthema ändern
- Startzeit ändern
- Endzeit ändern
- Dauer ändern
- Pause hinzufügen
- Pause entfernen
- Mittagspause verschieben
- Anreise verschieben
- Abreise verschieben

können.

---

# 16. Live-Validierung

Bei jeder Änderung muss der Plan automatisch validiert werden.

Warnungen beispielsweise bei:

- zeitlichen Überschneidungen
- Schulungen außerhalb der Kernarbeitszeit
- fehlender Mittagspause
- Mittagspause kürzer als 45 Minuten
- Pausen unter 20 Minuten
- Pausen über 30 Minuten
- Schulungen innerhalb des Anreisefensters
- Schulungen innerhalb des Abreisefensters
- ungeplanten Schulungsthemen
- verletzten Abhängigkeiten
- überschrittener Tagesarbeitszeit

Fehler sollen direkt beim betroffenen Tag bzw. Schulungsblock sichtbar sein.

---

# 17. Planungsübersicht

Zusätzlich zur Wochenansicht soll eine Zusammenfassung angezeigt werden.

Beispielsweise:

```text
Gesamte Schulungszeit:      21 h 30 min
Pausen:                      3 h 15 min
Mittagspausen:               3 h 00 min
Anreise:                     1 h 30 min
Abreise:                     2 h 00 min
Nicht eingeplant:            0 h
```

Zusätzlich pro Schulungsthema:

```text
Thema                     geplant       benötigt
-------------------------------------------------
Systemübersicht           180 min       180 min
Administration            120 min       120 min
Praktische Übungen        240 min       240 min
```

---

# 18. Einstellungen

Folgende Werte sollen konfigurierbar sein:

### Allgemein

- Schulungsbezeichnung
- Standort
- Trainer
- Teilnehmer / Teilnehmergruppe
- Startdatum
- Enddatum

### Arbeitszeiten

- Tagesbeginn
- Tagesende

Standard:

```text
08:30 - 17:00
```

### Pausen

- minimale Pausenzeit: 20 Minuten
- maximale Pausenzeit: 30 Minuten
- bevorzugte Pausenzeit: 25 Minuten

### Mittag

- Mittagspause: 45 Minuten
- bevorzugtes Zeitfenster

### Montag

- Anreisefenster aktivieren/deaktivieren
- Beginn
- Ende
- Bezeichnung

### Donnerstag

- Abreisefenster aktivieren/deaktivieren
- Beginn
- Ende
- Bezeichnung

---

# 19. Vorschau des fertigen Schulungsplans

Vor dem Export muss eine Druckvorschau vorhanden sein.

Der fertige Schulungsplan soll professionell aufgebaut sein.

Beispiel:

# Schulungsplan

**Schulung:** [Name]  
**Zeitraum:** 07.09.2026 – 10.09.2026  
**Trainer:** [Name]  
**Standort:** [Standort]

## Montag, 07.09.2026

| Zeit        | Inhalt             |
|-------------|--------------------|
| 08:30–10:00 | Anreise            |
| 10:00–11:30 | Einführung         |
| 11:30–11:55 | Pause              |
| 11:55–12:55 | Systemübersicht    |
| 12:55–13:40 | Mittagspause       |
| 13:40–15:10 | Administration     |
| 15:10–15:35 | Pause              |
| 15:35–17:00 | Praktische Übungen |

Analog für Dienstag, Mittwoch und Donnerstag.

---

# 20. Export

Der fertige Plan soll mindestens exportiert werden können als:

- PDF
- Excel/XLSX

Optional zusätzlich:

- Druckansicht
- CSV

Der Export muss vollständig lokal innerhalb der Anwendung erzeugt werden.

Für die PDF-Ausgabe soll möglichst das Design bzw. die Struktur der bereitgestellten bestehenden Schulungsplan-PDFs berücksichtigt werden.

---

# 21. Sitzung und Datenspeicherung

Da keine hochgeladenen Dateien gespeichert werden dürfen, soll die Anwendung grundsätzlich sessionbasiert arbeiten.

Innerhalb einer aktiven Browsersitzung dürfen die bearbeiteten Daten gehalten werden.

Optional kann angeboten werden:

**Projektdatei herunterladen**

Dabei soll eine eigene lokale Projektdatei erzeugt werden, die der Benutzer selbst auf seinem Rechner speichern kann.

Später könnte diese Projektdatei wieder in die Anwendung geladen werden.

Die Anwendung selbst speichert sie jedoch nicht.

---

# 22. Technische Architektur

Verwende eine moderne und langfristig wartbare Architektur.

Bevorzugt beispielsweise:

### Frontend

- React
- TypeScript
- Vite
- moderne Komponentenbibliothek
- responsive CSS
- Drag-and-Drop-Unterstützung

### Backend

Geeignete Technologie auswählen, z. B.:

- Node.js/TypeScript

oder

- Python/FastAPI

Wichtig ist eine saubere API-Struktur.

Für Excel-Verarbeitung geeignete Bibliotheken verwenden.

Für PDF-Analyse geeignete lokale Bibliotheken verwenden.

Für PDF-Erzeugung ebenfalls eine lokale serverseitige oder clientseitige Lösung verwenden.

Keine externen Cloud-APIs verwenden.

---

# 23. Datenmodell

Entwickle ein sauberes Datenmodell, mindestens für:

- TrainingProject
- TrainingDay
- TrainingTopic
- TrainingBlock
- BreakBlock
- LunchBreak
- ArrivalWindow
- DepartureWindow
- Trainer
- ParticipantGroup
- PlanningSettings

Schulungs-, Pausen-, Anreise- und Abreiseblöcke sollten technisch möglichst über ein gemeinsames Blockmodell abbildbar sein.

Beispielsweise:

```typescript
type ScheduleBlockType =
  | "training"
  | "break"
  | "lunch"
  | "arrival"
  | "departure";
```

---

# 24. Planung muss deterministisch und nachvollziehbar sein

Der Planungsalgorithmus darf keine „Black Box“ sein.

Die Planung soll nachvollziehbare Regeln verwenden.

Im Code müssen die Regeln sauber getrennt und testbar implementiert werden.

Beispielsweise:

```text
1. Verfügbare Zeitfenster erzeugen
2. Anreise-/Abreisezeiten blockieren
3. Mittagspause reservieren
4. Themen nach Priorität/Abhängigkeit sortieren
5. Themen auf freie Zeitfenster verteilen
6. Pausen ergänzen
7. Restzeiten optimieren
8. Ergebnis validieren
```

---

# 25. Tests

Erstelle automatisierte Tests insbesondere für den Planungsalgorithmus.

Mindestens folgende Fälle testen:

- normaler Montag–Donnerstag-Plan
- Montag mit Anreise
- Donnerstag mit Abreise
- mehrere Themen an einem Tag
- Thema passt nicht mehr in den Tag
- Thema wird auf Folgetag verschoben
- Pausen von 20–30 Minuten
- 45 Minuten Mittagspause
- Überschneidungen
- zu viele Schulungsstunden
- leere Excel-Datei
- ungültige Excel-Datei
- ungültiges PDF
- Löschen temporärer Dateien

---

# 26. Sicherheit

Berücksichtige:

- sichere Dateiuploads
- maximale Dateigröße
- nur erlaubte Dateitypen
- keine Ausführung hochgeladener Inhalte
- sichere Dateinamen
- Schutz gegen Path Traversal
- sichere Verarbeitung von ZIP/XML-basierten XLSX-Dateien
- keine externen Requests aufgrund von Dateiinhalten
- keine persistente Speicherung hochgeladener Dateien

---

# 27. Benutzerführung

Die Bedienung soll möglichst einfach sein.

Gewünschter Ablauf:

```text
1. Excel-Datei auswählen
        ↓
2. PDF-Vorlagen auswählen
        ↓
3. Import prüfen
        ↓
4. Schulungsparameter einstellen
        ↓
5. „Schulungsplan erstellen“
        ↓
6. Automatisch erzeugten Plan prüfen
        ↓
7. Online per Drag-and-Drop / Dialog bearbeiten
        ↓
8. Validierung
        ↓
9. Vorschau
        ↓
10. PDF oder Excel herunterladen
```

---

# 28. Entwicklungsanforderungen

Arbeite nicht nur einen Prototypen aus.

Erstelle eine tatsächlich ausführbare vollständige Anwendung.

Wichtig:

- keine Mock-Funktionen im finalen Stand
- keine nicht implementierten Buttons
- keine TODO-Platzhalter für Kernfunktionen
- saubere Fehlerbehandlung
- strukturierter Quellcode
- verständliche Logs
- sinnvolle Kommentare
- TypeScript strict mode, falls TypeScript verwendet wird
- automatisierte Tests
- Docker-Healthcheck
- reproduzierbarer Build

---

# 29. Vorgehen mit den bereitgestellten Dateien

Bevor mit der eigentlichen Implementierung begonnen wird:

1. Analysiere zuerst die bereitgestellte Excel-Datei vollständig.
2. Beschreibe ihre Tabellenblätter, Spalten und die für die Planung relevanten Daten.
3. Analysiere anschließend alle bereitgestellten PDF-Schulungspläne.
4. Ermittle Gemeinsamkeiten und Unterschiede der PDF-Pläne.
5. Leite daraus das benötigte Datenmodell ab.
6. Leite daraus sinnvolle Standard-Schulungszeiten und Themenstrukturen ab.
7. Beschreibe anschließend die geplante Softwarearchitektur.
8. Implementiere danach die Anwendung.

Keine Struktur der Excel-Datei oder der PDFs erfinden, wenn diese Informationen aus den bereitgestellten Dateien ausgelesen werden können.

Der Ordner Aufgabe darf nicht im deployment auftauchen.

Lege bitte ein lokales repo mit Versionierung an und erstelle ein Testsystem über einen freien Port auf diesem System im Docker.

Erstelle auch eine Installationsaleitung für das Installieren auf einem Produktivsystem.

---

# 30. Wichtigste fachliche Regeln

Diese Regeln haben höchste Priorität:

```text
Schulungstage:        Montag bis Donnerstag
Kernzeit:             08:30–17:00 Uhr
Pause:                20–30 Minuten
Mittagspause:         exakt 45 Minuten
Montag:               definierbares Anreisefenster
Donnerstag:           definierbares Abreisefenster
Themen pro Tag:       mehrere möglich
Nachbearbeitung:      vollständig im Browser
Dateispeicherung:     keine hochgeladenen Dateien dauerhaft speichern
Betrieb:              vollständig über Docker
Export:               mindestens PDF und Excel
```

Entwickle die Anwendung so, dass diese Regeln zentral konfiguriert und vom Planungsalgorithmus sowie der Validierung gemeinsam verwendet werden.

Ziel ist ein **einfach bedienbares, modernes Schulungsplanungssystem**, das die manuelle Erstellung von mehrtägigen Schulungsplänen weitgehend automatisiert, aber dem Benutzer jederzeit die vollständige Kontrolle über das Endergebnis gibt.

---

# 31. Umsetzungsnotiz 2026-08-31

Die erste lauffähige Testsystem-Version wurde als lokale Docker-Webanwendung umgesetzt.

- Architektur: Python/FastAPI Backend mit statischem Browser-Frontend.
- Upload-Verarbeitung: Excel/PDF-Dateien werden im Request-Speicher verarbeitet und nicht dauerhaft gespeichert.
- Deployment: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example` und README wurden erstellt.
- Analyse: Die Auswertung der bereitgestellten XLSM/PDF-Beispiele wurde in `docs/ANALYSE.md` dokumentiert.
- Planung: Zentrale Regeln, deterministischer Planungsalgorithmus und Validierung wurden serverseitig umgesetzt.
- UI: Import, Grunddaten, Themen, automatische Planung, Wochenansicht, Vorschau und Export sind im Browser nutzbar.
- Export: PDF und XLSX werden lokal generiert.
- Testsystem: Docker-Port `18083` wurde fuer die Testinstanz verwendet.

---

# 32. Anpassungsnotiz 2026-08-31

Nach Rueckmeldung soll das UI-Layout aus `authproxycaller-main.zip` uebernommen werden und es soll vorerst keinen sichtbaren Import-Workflow geben.

- Referenz-Layout aus `Aufgabe/authproxycaller-main.zip` wurde gesichtet.
- UI-Richtung: dunkle Topbar, zweispaltige Arbeitsflaeche, kompakte Karten, Formular links und Sticky-Ergebnisbereich rechts.
- Dateiimport wird aus der Benutzeroberflaeche entfernt.
- Die Anwendung startet stattdessen mit aus den Beispieldateien abgeleiteten Standard-Schulungsthemen, die manuell bearbeitet und automatisch geplant werden koennen.

---

# 33. Anpassungsnotiz 2026-08-31

Die Versionsnummern werden im Bereich `v0.2.X` fortlaufend hochgezaehlt. Fuer diese Anpassung wurde auf `v0.2.1` erhoeht.

- Der Einstieg der Anwendung beginnt mit Projektdaten: Kunde, Standort, Trainer, Produkt und Teilnehmergruppen.
- Fuer DeepUnity PACS sind Teilnehmergruppen wie Radiologen, Radiologen Keyuser, MFA, Kliniker, Webviewer und Administratoren vorbelegt.
- Das Datenmodell wurde um Produktlinien und Teilnehmergruppen erweitert, damit spaeter weitere Produkte mit eigenen Gruppen und Themen ergaenzt werden koennen.

---

# 34. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.2` erhoeht.

- Die Eingabe ist nun auf Seite 1 gebuendelt: Projektdaten, Planungsregeln und Schulungsthemen.
- Der Schulungsplan erscheint erst auf Seite 2 nach dem Erstellen der Planung.
- Es wurde ein Verwendungszweck ergaenzt: Schulungsplanung mit Kundendaten oder Dienstleistungskalkulation ohne Kundendaten.
- Im Modus Dienstleistungskalkulation werden Kundendaten in der UI und im Export nicht benoetigt.

---

# 35. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.3` erhoeht.

- Die Eingabeseite wird nun mittig und breit dargestellt statt links an der Seite zu kleben.
- Die Seite `4 Schulungsplan` ist vor dem Klick auf `Plan erstellen` wirklich ausgeblendet.
- Die Seitentrennung wurde per CSS robuster gemacht, damit ausgeblendete Seiten nicht durch das Workspace-Layout sichtbar bleiben.

---

# 36. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.4` erhoeht.

- PostgreSQL wurde als Docker-Service fuer strukturierte Schulungsinhalte ergaenzt.
- Das Datenbankschema ist produktbezogen aufgebaut, damit neben DeepUnity PACS spaeter weitere Produkte mit eigenen Schulungsinhalten ergaenzt werden koennen.
- Die vorhandenen PACS-PDFs wurden fuer den Schulungsinhalte-Katalog ausgewertet, jedoch ohne den Abschnitt Schulungsverlauf.
- Hinterlegt werden Ziele, Zielgruppe, Dauer, Voraussetzungen, Vorbereitung, Hinweise und Quelldatei.
- Die UI zeigt die hinterlegten Schulungsinhalte auf der Eingabeseite im Bereich Schulungsthemen an.

---

# 37. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.5` erhoeht.

- Der PDF-Quelldatei-Hinweis wurde aus den sichtbaren Schulungsinhalten entfernt.
- Die Texte der Schulungsinhalte sind nun direkt in der UI editierbar.
- Aenderungen an Schulungsinhalten werden ueber die API in PostgreSQL gespeichert.
- Die Initialbefuellung der Datenbank ueberschreibt vorhandene Schulungsinhalte nicht mehr, damit manuelle Anpassungen nach einem Neustart erhalten bleiben.

---

# 38. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.6` erhoeht.

- Die hinterlegten Schulungsinhalte wurden aus der Haupt-Eingabeseite herausgenommen.
- Es gibt nun ein linkes Hamburger-Menue mit getrennten Bereichen fuer Produkte und Schulungsinhalte.
- Das aktive Produkt wird im Menue ausgewaehlt.
- Neue Produkte koennen im Menue angelegt und in PostgreSQL gespeichert werden.
- Die Hauptseite bleibt dadurch auf Projektdaten, Planungsregeln und konkrete Schulungsthemen fokussiert.

---

# 39. Anpassungsnotiz 2026-08-31

Die Version wurde auf `v0.2.7` erhoeht.

- Die linke Seite dient nun nur noch als Navigation mit Links zu Eingabe, Produkte, Schulungsinhalte und Schulungsplan.
- Die Inhalte der ausgewaehlten Seite werden im Hauptbereich angezeigt.
- Produktverwaltung und Schulungsinhalte sind eigene Hauptseiten statt Inhalt im linken Menue.
- Auf mobilen Ansichten kann die linke Navigation ueber das Hamburger-Symbol ein- und ausgeblendet werden.

---

# 40. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.8` erhoeht.

- Die Seite Schulungsinhalte zeigt neben der Hauptnavigation nun eine Linkliste der Inhalte des aktiven Produkts.
- Es werden nicht mehr alle Schulungsinhalte gleichzeitig als grosse Formularliste angezeigt.
- Beim Klick auf einen Schulungsinhalt wird nur dieser einzelne Inhalt im Hauptbereich editierbar angezeigt.
- Die Bearbeitung und Speicherung der einzelnen Inhalte bleibt ueber PostgreSQL angebunden.

---

# 41. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.9` erhoeht.

- Der Katalog-Ladevorgang fuer Schulungsinhalte wurde robuster gemacht.
- Die App setzt nun Cache-Control fuer HTML, JavaScript und CSS, damit Browser keine alten UI-Dateien mit neuen Dateien mischen.
- CSS und JavaScript werden mit Versionsparameter ausgeliefert.
- Die Schulungsinhalte-Ansicht kann auch bei einem alten HTML-Zwischenstand die neue Linkliste und Detailansicht nachrendern.

---

# 42. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.10` erhoeht.

- Die Navigation ist nicht mehr dauerhaft sichtbar.
- Das linke Navigationsmenue wird nur nach Klick auf das Hamburger-Symbol eingeblendet.
- Nach Auswahl eines Navigationslinks schliesst sich das Menue wieder.
- Die Seiteninhalte bleiben im Hauptbereich sichtbar und werden nicht in der Navigation angezeigt.

---

# 43. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.11` erhoeht.

- Produktdaten und Teilnehmergruppen wurden wieder auf die Eingabeseite verschoben.
- Die linke Navigation enthaelt nun nur noch Links zu Eingabe, Schulungsinhalte und Schulungsplan.
- Die separate Produktseite wurde entfernt.
- Neue Produkte koennen weiterhin in der Eingabe angelegt und als aktives Produkt genutzt werden.

---

# 44. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.12` erhoeht.

- Produktdaten und Teilnehmergruppen sind in der Eingabe nun wieder deutlich als eigener Kartenbereich sichtbar.
- Der Bereich liegt direkt nach den Grunddaten, damit aktives Produkt, Produktanlage und Teilnehmergruppen nicht in den Grunddaten untergehen.
- Die linke Navigation bleibt weiterhin ein reines Hamburger-Menue mit Links und enthaelt keine Eingabeformulare.

---

# 45. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.13` erhoeht.

- Die Wochenansicht des Schulungsplans wurde zu einer Kalenderansicht mit Zeitachse umgebaut.
- Jeder Tag zeigt nun eine eigene Zeitsaeule von Tagesbeginn bis Tagesende.
- Schulungsbloecke koennen per Drag-and-Drop innerhalb eines Tages zeitlich verschoben werden.
- Schulungsbloecke koennen per Drag-and-Drop auch in andere Wochentage verschoben werden.
- Die neue Startzeit rastet in 15-Minuten-Schritten ein; Dauer und Validierung bleiben erhalten.

---

# 46. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.14` erhoeht.

- Die Kalender-Zeitachse zeigt nun Viertelstunden statt nur Stunden.
- Die Tagesflaechen haben sichtbare Viertelstunden-Linien.
- Die Snap-Funktion richtet verschobene Schulungsbloecke an diesen Viertelstunden aus.
- Beim Ziehen wird der Abstand zwischen Mauszeiger und Block-Oberkante beruecksichtigt, damit Bloecke auch exakt am Arbeitsbeginn abgelegt werden koennen.
- Normale Pausen und Mittagspause bleiben in der Planung berechnet, werden in der Kalenderansicht aber nicht als Kacheln angezeigt.

---

# 47. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.15` erhoeht.

- Produktdaten und Teilnehmergruppen wurden wieder als eigene Seite ueber das Hamburger-Menue erreichbar gemacht.
- Die Eingabeseite bleibt auf Grunddaten, Planungsregeln und konkrete Schulungsthemen fokussiert.
- Die Kalenderansicht zeigt die Zeiten nun in jedem Tag direkt an.
- Freitag wird im Kalender immer angezeigt und kann in den Planungsregeln optional als Schulungstag aktiviert werden.
- Wenn die Planung mehrere Wochen benoetigt, werden die Wochen im Schulungsplan untereinander dargestellt.
- Schulungsinhalte koennen eine maximale Teilnehmerzahl speichern.
- Schulungsinhalte koennen eine Abhaengigkeit zu einer anderen Schulung desselben Produkts speichern.
- Abhaengige Schulungen muessen bei der Planung mindestens einen Tag nach der Voraussetzung liegen.

---

# 48. Anpassungsnotiz 2026-09-01

Die Version wurde auf `v0.2.16` erhoeht.

- Teilnehmergruppen wurden aus den Produktdaten entfernt und als eigener Eingabebereich auf die Eingabeseite verschoben.
- Die Produktdaten-Seite enthaelt nur noch aktives Produkt, Produktname, Produkt-ID, Beschreibung und Produktanlage.
- Schulungsinhalte koennen nun mehrere Teilnehmergruppen des aktiven Produkts per Mehrfachauswahl speichern.
- Die Planung nutzt die zugeordneten Teilnehmergruppen und teilt Schulungen bei Ueberschreitung der maximalen Teilnehmerzahl je Gruppe auf.
- Die Kalenderansicht wurde so angepasst, dass Anfang und Ende des Arbeitstages voll sichtbar bleiben.

---

# 49. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.17` erhoeht.

- Im Schulungsplan kann ueber `Woche hinzufuegen` manuell eine weitere Woche angelegt werden.
- Manuell hinzugefuegte Wochen bleiben im Projektmodell erhalten und werden auch fuer Vorschau/Export beruecksichtigt.
- Schulungsbloecke koennen in der Kalenderansicht ausgeschnitten werden.
- Ein ausgeschnittener Block kann in einem beliebigen Tag einer beliebigen Woche eingefuegt werden.
- Beim Einfuegen wird der naechste freie Viertelstunden-Slot des Zieltags verwendet; die Dauer des Blocks bleibt erhalten.

---

# 50. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.18` erhoeht.

- Schulungsinhalte koennen nun direkt im Katalog neu angelegt werden.
- Neue Schulungsinhalte werden produktbezogen in PostgreSQL gespeichert.
- Jeder Schulungsinhalt hat eine editierbare Hintergrundfarbe.
- Die Hintergrundfarbe wird in die geplanten Schulungsbloecke uebernommen und im Kalender als Kachelhintergrund angezeigt.
- Die Aktionsbuttons in den Kalenderkacheln behalten ihre eigene Button-Optik und werden nicht durch die Kachelfarbe eingefaerbt.

---

# 51. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.19` erhoeht.

- Die Aktionsbuttons in Kalender-Schulungskacheln werden dauerhaft oben rechts angezeigt.
- Die vier Kachelbuttons sind als 2x2-Raster angeordnet.
- Die Button-Flaechen behalten ihre eigene Hintergrundfarbe, unabhaengig von der Schulungskachelfarbe.
- Der Header zeigt nun direkt das aktuell aktive Produkt an.
- Der Header-Kontext wird dynamisch aus Schulungsbezeichnung und allgemeinem Planungstext aufgebaut.

---

# 52. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.20` erhoeht.

- Die Kalenderkachel-Buttons wurden verkleinert, damit die 2x2-Anordnung auch in niedrigen Schulungskacheln sichtbar bleibt.
- Die Button-Anordnung sitzt fest oben rechts in der Schulungskachel.
- Die Kachel reserviert rechts weniger Platz fuer die Buttonleiste, damit der Inhalt weiterhin lesbar bleibt.
- Der Header wurde umsortiert: Aktives Produkt, Schulungsplantool und Unterzeile stehen direkt links neben dem Hamburger-Menuebutton.
- Die Header-Unterzeile bleibt dynamisch und zeigt die aktuelle Schulungsbezeichnung mit Planungstext.

---

# 53. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.21` erhoeht.

- Der Hamburger-Menuebutton steht nun links im Header.
- Aktives Produkt, Schulungsplantool und Unterzeile stehen direkt rechts neben dem Hamburger-Menuebutton.

---

# 54. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.22` erhoeht.

- Der vorhandene Anwendungsstand wurde als installierbares Git-/Docker-Projekt aufbereitet.
- Lokale Entwicklungsartefakte wie `node_modules`, `.pytest_cache`, `__pycache__` und `.env` sind nicht Bestandteil des Repository-Pakets.
- Das Docker-Deployment verwendet weiterhin PostgreSQL als einzigen persistenten Anwendungsdienst.
- Der Anwendungscontainer laeuft als unprivilegierter Benutzer und besitzt einen expliziten Healthcheck.
- `docker-compose.yml` enthaelt Healthchecks fuer Anwendung und PostgreSQL und erwartet die produktionsrelevanten Zugangsdaten aus `.env`.
- Mit `scripts/install.sh` kann eine Erstinstallation durchgefuehrt werden; dabei wird bei fehlender `.env` ein zufaelliges PostgreSQL-Passwort erzeugt.
- Mit `scripts/update.sh` kann ein Git-basierter Produktionsstand aktualisiert werden, ohne das PostgreSQL-Volume zu loeschen.
- Mit `scripts/backup-db.sh` kann vor Updates ein lokaler PostgreSQL-Dump erzeugt werden.
- GitHub Actions prueft Tests, Compose-Konfiguration und Docker-Build.
- `Aufgabe/`, `Aufgabe.md`, Tests, Dokumentation und lokale Entwicklungsdateien werden nicht in das Produktionsimage kopiert.
- Die Installations- und Produktionshinweise wurden in `README.md` und `docs/INSTALLATION.md` dokumentiert.

---

# 55. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.24` erhoeht.

- Ein eigener GitHub-Actions-Workflow veroeffentlicht bei Release-Tags automatisch das Anwendungsimage in GitHub Container Registry.
- Das Release-Image wird als Multi-Arch-Image fuer `linux/amd64` und `linux/arm64` gebaut.
- Ziel-Repository fuer Container-Images ist `ghcr.io/syschelle/schulungsplantool`.
- Der Workflow prueft vor dem Build, dass der Release-Tag zur Datei `VERSION` passt.
- Docker Buildx/QEMU, Build-Cache, SBOM und Provenance werden fuer Release-Images verwendet.
- `docker-compose.yml` verwendet standardmaessig das fertig veroeffentlichte GHCR-Image und baut auf Produktivsystemen nicht mehr lokal.
- `scripts/install.sh` und `scripts/update.sh` verwenden `docker compose pull` vor dem Start der Container.
- Docker waehlt aus demselben Multi-Arch-Image automatisch die passende Architektur fuer x86_64/amd64 oder arm64.

---

# 56. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.24` erhoeht.

- Fuer den produktiven Image-Betrieb wurde `docker-compose.images.yml` hinzugefuegt.
- `docker-compose.yml` dient wieder als lokaler Build-/Entwicklungsmodus mit dem vorhandenen Dockerfile.
- `./install.sh` installiert standardmaessig ueber das veroeffentlichte GHCR-Multi-Arch-Image.
- `./update.sh` zieht spaetere Image-Versionen und startet die Container neu, ohne das PostgreSQL-Volume zu entfernen.
- PostgreSQL besitzt weder im lokalen noch im Image-Compose ein `ports`-Mapping und ist damit nicht ueber einen Host-Port erreichbar.
- Ausschliesslich der Webport des Schulungsplantools wird auf dem Docker-Host publiziert.
- Anwendung und PostgreSQL kommunizieren ueber das dedizierte Compose-Netz `schulungsplantool_backend`.
- CI und Release-Workflow validieren beide Compose-Dateien.


---

# 57. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.25` erhoeht.

- Die Weboberflaeche ist nun fuer den Betrieb hinter einem Reverse Proxy unter einem URL-Unterpfad wie `/trainingschedule/` ausgelegt.
- CSS und JavaScript werden mit relativen Pfaden geladen, damit Traefik `StripPrefix` korrekt verwendet werden kann.
- Browserseitige API-Aufrufe verwenden relative `api/...`-Pfade statt absoluter `/api/...`-Pfade.
- Der direkte Betrieb am Webroot bleibt weiterhin moeglich.
- Regressionstests verhindern, dass absolute Frontend-/API-Pfade versehentlich wieder eingefuehrt werden.
- `docker-compose.images.yml` verwendet standardmaessig `ghcr.io/syschelle/schulungsplantool:latest`.

---

# 58. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.26` erhoeht.

- Beim gewaehlten Eintrag unter `Hinterlegte Schulungsinhalte` gibt es nun den Button `Schulungspunkte bearbeiten`.
- Der Button oeffnet einen lokalen Markdown-Editor mit dem aktuell in PostgreSQL gespeicherten Inhalt.
- Der Editor bietet einfache Formatierungswerkzeuge fuer Ueberschriften, Fett/Kursiv, Aufzaehlungen und Nummerierungen sowie eine Live-Vorschau.
- Die Markdown-Schulungspunkte werden als eigenes Textfeld am Schulungsinhalt gespeichert.
- Pro Schulungsinhalt wird eine persistente Aenderungshistorie in PostgreSQL gefuehrt.
- Gespeicherte Versionen koennen aus der Historie wiederhergestellt werden; Wiederherstellungen werden ebenfalls protokolliert.
- Der Editor benoetigt keine externe CDN- oder Cloud-Verbindung.
- Der Hinweis `Keine sichtbaren Bloecke.` wurde aus leeren Kalenderbereichen entfernt.

---

# 59. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.27` erhoeht.

- Der Markdown-Editor fuer Schulungspunkte besitzt nun `DOCX exportieren` und `DOCX importieren`.
- Der DOCX-Export erzeugt eine lokal erstellte Word-kompatible Datei mit dem aktuell im Editor angezeigten Inhalt.
- Im exportierten DOCX steht ein sichtbarer Hinweis, welche Formatierungen fuer einen spaeteren Re-Import zulaessig bzw. nicht zulaessig sind.
- Fuer den Re-Import zugelassen sind Ueberschriften Ebene 1-3, normaler Text, Fett/Kursiv, Aufzaehlungen und Nummerierungen.
- Bilder und Screenshots duerfen ausdruecklich nicht importiert werden. Enthält das DOCX Medien/Grafiken, wird der gesamte Import abgelehnt und nichts gespeichert.
- Ebenfalls abgelehnt werden Formen/Textfelder, Tabellen, Diagramme/SmartArt, eingebettete Dateien/Objekte, Hyperlinks, Fuss-/Endnoten und offene nachverfolgte Aenderungen.
- Erfolgreiche DOCX-Importe werden zuerst nur in den Editor geladen und muessen vor dem Speichern kontrolliert werden.
- Nach dem Speichern wird die Aenderungshistorie mit dem Typ `DOCX importiert` fortgeschrieben.
- DOCX-Dateien werden nicht persistent gespeichert und nicht an externe Dienste uebertragen.
- Die DOCX-Verarbeitung und OOXML-Sicherheitspruefung erfolgen vollstaendig lokal im Anwendungscontainer.

---

# 60. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.28` erhoeht.

- Pro Schulungsinhalt werden dauerhaft maximal 5 Eintraege der Markdown-Aenderungshistorie gespeichert.
- Beim Speichern oder Wiederherstellen eines sechsten Standes wird automatisch der jeweils aelteste Historieneintrag geloescht.
- Bereits vorhandene Historien mit mehr als 5 Eintraegen werden beim Start der Anwendung automatisch auf die 5 neuesten Staende reduziert.
- Die Historienanzeige weist auf die maximale Anzahl von 5 gespeicherten Staenden hin.
- In der Markdown-Live-Vorschau werden Ueberschriften der Ebene 2 und Ebene 3 mit unterschiedlichen Farben dargestellt, damit die Gliederung schneller erkennbar ist.

---

# 61. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.29` erhoeht.

- Die Vorbelegung fuer Kunde und Standort wurde entfernt.
- Der vorbelegte Trainer wurde entfernt.
- Bei gesetztem Startdatum zeigt die Kalenderansicht pro Wochentag das konkrete Datum an.
- Mehrwoechige Plaene berechnen den Datumsbereich jeder weiteren Woche automatisch.
- Direkt am Kalendertag werden lokale DACH-Feiertagshinweise angezeigt.
- Beruecksichtigt werden landesweite Feiertage fuer Deutschland und Oesterreich sowie die Schweizer Bundesfeier.
- Regionale Feiertage werden ohne Bundesland-/Kantonsauswahl nicht als sicher geltend dargestellt.
- Die Feiertagsberechnung benoetigt keine externe API oder Cloud-Verbindung.

---

# 62. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.30` erhoeht.

- In der Planuebersicht werden die Summenkarten fuer Pausen, Mittagspause, Anreise und Abreise nicht mehr angezeigt.
- Stattdessen zeigt die Uebersicht die Anzahl der `Dienstleistungstage`.
- Als Dienstleistungstag zaehlt jeder Tag einer Schulungswoche, an dem mindestens ein Schulungsblock vom Typ `training` geplant ist.
- Mehrere Schulungen am gleichen Tag werden nur als ein Dienstleistungstag gezaehlt.
- Tage mit ausschliesslich Anreise, Abreise oder Pausen werden nicht als Dienstleistungstage gezaehlt.
- Die Kennzahlen fuer gesamte Schulungszeit und nicht eingeplante Schulungszeit bleiben erhalten.


---

# 63. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.31` erhoeht.

- Ein Projekt kann nun mehrere gleichberechtigte Trainer enthalten; alle Trainer koennen alle Schulungsinhalte uebernehmen.
- Die automatische Planung verteilt Schulungsbloecke auf die verfuegbaren Trainer und kann dadurch Schulungen parallel am selben Kalendertag planen.
- Fuer jede Kalenderwoche wird pro Trainer eine eigene Wochenansicht angezeigt.
- Die Trainerwochen werden innerhalb der jeweiligen Kalenderwoche zusammengefasst, damit Woche 1 aller Trainer vor Woche 2 aller Trainer erscheint.
- Schulungsbloecke koennen per Drag-and-Drop zwischen den Trainerwochen verschoben werden; dabei wird die Trainerzuordnung des Blocks geaendert.
- Die Ueberlappungsvalidierung erfolgt je Trainer, sodass parallele Schulungsbloecke unterschiedlicher Trainer keine falsche Ueberlappungswarnung erzeugen.
- Der PDF-Export wird als A4-Querformat ausgegeben und bildet die Kalenderansicht mit Zeitachse, Wochentagen, Datumswerten, Feiertagshinweisen und farbigen sichtbaren Bloecken ab.
- Pro Trainer und Kalenderwoche wird eine PDF-Kalenderseite erzeugt; die Seiten werden chronologisch nach Woche und danach Trainer angeordnet.
- Ueber `Planung exportieren` kann der komplette aktuelle Projekt-/Planungsstand als lokale JSON-Projektdatei heruntergeladen werden.
- Ueber `Planung importieren` kann eine zuvor exportierte Projektdatei validiert und wiederhergestellt werden, sodass Trainer, Themen, Wochen, Bloecke, Zeiten, Farben, Teilnehmerdaten und weitere Projekteinstellungen erneut angezeigt werden.
- Die Projektdatei wird beim Import nur im Request verarbeitet und nicht dauerhaft serverseitig gespeichert.

---

# 64. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.32` erhoeht.

- Security-Maintenance-Release fuer Dependabot- und CodeQL-Funde.
- `python-multipart` wurde auf `0.0.32` aktualisiert.
- `pypdf` wurde auf `6.16.2` aktualisiert.
- Runtime-Abhaengigkeiten werden nicht mehr ueber `requirements-dev.txt` gespiegelt, damit Dependabot-Funde nicht doppelt fuer beide Requirements-Dateien entstehen.
- Die drei CodeQL-High-Funde zu polynomialen regulaeren Ausdruecken in `app/server/docx_content.py` wurden ohne Suppression behoben.
- Markdown-Ueberschriften, Aufzaehlungen und Nummerierungen werden beim DOCX-Export nun mit deterministischer Zeichenanalyse statt regulaeren Ausdruecken erkannt.
- Auch die Inline-Markdown-Verarbeitung und die Erkennung von Word-Ueberschriftenstilen im DOCX-Pfad wurden ohne regulaere Ausdruecke umgesetzt.
- Regressionstests decken sehr lange unkontrollierte Markdown-Zeilen und fehlerhafte Markdown-Marker ab.

---

# Anpassungsnotiz 2026-09-02 - v0.2.33

- Die Version wurde auf `v0.2.33` erhoeht.
- Die Entwicklungsabhaengigkeit `pytest` wurde von `9.0.2` auf `9.1.1` aktualisiert.
- Damit wird der Dependabot-Hinweis `pytest has vulnerable tmpdir handling` (CVE-2025-71176 / GHSA-6w46-j5rx-g56g) behoben; betroffen sind pytest-Versionen kleiner `9.0.3`.
- Ein Regressionstest prueft den sicheren pytest-Pin in `requirements-dev.txt`.
- Runtime-Abhaengigkeiten, Datenbankschema und Anwendungsfunktionen bleiben unveraendert.


---

# 66. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.34` erhoeht.

- Der Button `Planung importieren` befindet sich nun auf der Seite `Eingabe` im Bereich `Grunddaten` und nicht mehr in der Schulungsplan-Anzeige.
- `Planung exportieren` bleibt in der Schulungsplan-Anzeige.
- Startzeiten von Kalenderbloecken muessen immer auf einem 15-Minuten-Raster liegen (`:00`, `:15`, `:30`, `:45`).
- Die automatische Planung richtet jeden neuen Schulungs-, Pausen- und Mittagspausenstart auf einen Viertelstunden-Slot aus.
- Bei Pausen mit z. B. 25 Minuten wird der folgende Schulungsstart bei Bedarf auf den naechsten freien Viertelstunden-Slot geschoben.
- Manuell bearbeitete Startzeiten werden auf das Viertelstundenraster normalisiert.
- Beim Import aelterer Planungsdateien werden nicht passende Block-Startzeiten auf das Viertelstundenraster normalisiert, ohne die gespeicherte Blockdauer zu veraendern.

---

# 67. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.35` erhoeht.

- Die Validierungs- und Konfliktmeldungen werden nicht mehr direkt in der Schulungsplan-Seite oberhalb der Kalenderansicht angezeigt.
- Es gibt eine eigene Navigationsseite `Planungspruefung` fuer alle aktuellen Warnungen und Konflikte.
- Die Navigation zeigt die Anzahl der vorhandenen Validierungshinweise an.
- Die Live-Validierung bleibt nach Drag-and-Drop, manuellen Aenderungen und anderen Planungsaktionen aktiv.
- Durch die getrennte Darstellung veraendert die Warnliste nicht mehr die Hoehe der Kalenderseite; Scroll- und Kalenderposition bleiben beim Verschieben von Bloecken stabil.
- Bei einer konfliktfreien Planung zeigt die Pruefungsseite einen kompakten Status ohne Warnliste.


---

# 68. Anpassungsnotiz 2026-09-02

Die Version wurde auf `v0.2.36` erhoeht.

- Das Bearbeiten von Schulungs- und Kalenderbloecken erfolgt nicht mehr ueber mehrere Browser-`prompt`-Fenster.
- Ein eingebetteter Blockeditor innerhalb der Anwendung zeigt alle relevanten Eigenschaften gemeinsam an.
- Bearbeitbar sind Schulungsinhalt, Titel, Blocktyp, Kalenderwoche, Wochentag, Trainer, Start, Ende, Dauer, Farbe, Raum, Beschreibung und Hinweise.
- Die Auswahl eines hinterlegten Schulungsinhalts kann dessen Stammdaten in den Blockeditor uebernehmen.
- Startzeiten bleiben auf dem 15-Minuten-Raster und werden beim Speichern normalisiert.
- Eingabefehler erscheinen direkt im Blockeditor; der Kalender wird nicht durch Browser-Dialoge unterbrochen.
- Abbrechen verwirft die Editor-Eingaben. Nach erfolgreichem Speichern laeuft die bestehende Live-Validierung weiter.


## Erweiterung v0.2.37 - Uebersicht, Exportname und Navigation

- Vorschau und PDF beginnen mit einer Planuebersicht als erster Seite.
- Kunde und Standort werden in Uebersicht und Vorschau explizit ausgegeben.
- Planungsdateien werden als `kunde_standort_produkt_datum_uhrzeit.json` heruntergeladen.
- Eingabe und bestehender Schulungsplan koennen direkt gewechselt werden, ohne eine Neuberechnung zu starten.
- Nur der explizite Button `Plan erstellen` darf `/api/plan` aufrufen und einen neuen automatischen Plan erzeugen.
- Version auf `v0.2.37` erhoeht.
