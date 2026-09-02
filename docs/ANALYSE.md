# Analyse der Beispieldateien

## Excel-Datei

Die Datei `Aufgabe/Schulungsplan.xlsm` enthaelt zwei Arbeitsblaetter:

- `20.09.23 PACS`: 49 Zeilen, 14 Spalten
- `25.09.23 PACS`: 46 Zeilen, 14 Spalten

Erkannte fachliche Bereiche:

- Kopfbereich mit Projektname, Projektnummer, Kundenname, Projektleiter, Berater und Startdatum.
- Zeitraster im Tagesbereich von 08:00 bis 17:00 Uhr.
- Tabellenbereich ab Zeile 12 mit `Schulungen`, `Teilnehmer je Schulung`, `Schulungsdauer [in h]` und `Teilnehmer Gesamt`.
- Zusammenfassung fuer Zielgruppen wie Diagnost, Review und MTRA.

Die Anwendung liest diese Struktur dynamisch aus und zeigt dem Anwender die gefundenen Blaetter, Spalten und Beispielzeilen vor der Uebernahme an.

## PDF-Vorlagen

Gesichtete PDF-Vorlagen:

- `PACS-Administration.pdf`: ca. 6 Stunden
- `DU Diagnost Basic.pdf`: ca. 1,5 Stunden
- `DU Diagnost erweitert.pdf`: ca. 2 Stunden
- `DU Diagnost KeyUser.pdf`: ca. 3 Stunden
- `DU Review Kliniker.pdf`: ca. 1 Stunde
- `DU Viewer.pdf`: ca. 0,75 Stunden
- `Review MTRA.pdf`: ca. 1 Stunde
- `DU XChange.pdf`: ca. 1 Stunde

Gemeinsamer Aufbau:

- Allgemeine Informationen
- Ziele der Schulung
- Zielgruppe
- Ort
- Dauer
- Voraussetzungen
- Vorbereitung mindestens 7 Tage im Voraus
- Besonderheiten
- Schulungsverlauf mit Uhrzeit, Dauer, Thema, Inhalt und Material

Typische Standardbausteine:

- Check-In und Agenda
- Uebersicht Aufbau DeepUnity System
- Client-, Viewer-, Review-, XChange- oder PACS-spezifische Arbeitsschritte
- Praktische Uebungen und fachliche Vertiefung

## PACS-Schulungsinhalte ohne Schulungsverlauf

Fuer den neuen Schulungsinhalte-Katalog wurden die PACS-PDFs ohne den Abschnitt `Schulungsverlauf` ausgewertet. Hinterlegt werden je Inhalt nur fachliche Stammdaten:

- `PACS-Administration`: PACS-Administratoren, IT und Abteilungsadministratoren; 360 Minuten; Aufbau DeepUnity System, Client-Installation, Rechte/Rollen, Konfiguration, Hilfefunktionen, Webinterface und Support-Meldungen.
- `DU Diagnost Basic`: Radiologen, Nuklearmediziner und weitere Befunder; 90 Minuten; Grundlagen und sichere Bedienung von DeepUnity DIAGNOST.
- `DU Diagnost erweitert`: Befunder mit DIAGNOST-Grundlagen; 120 Minuten; erweiterte Funktionen der Befundungsworkstation.
- `DU Diagnost KeyUser`: Radiologie-Keyuser und IT-nahe Client-Administratoren; 180 Minuten; Konfigurationsoberflaeche, praktische Uebungen und Client-Verteilung.
- `DU Review Kliniker`: Kliniker mit Bilddaten-/Archivzugriff; 60 Minuten; Grundlagen der REVIEW Betrachtungsworkstation.
- `DU Viewer`: klinische Anwender der hausweiten Bildverteilung; 45 Minuten; Grundwissen und sicherer Umgang mit dem Viewer.
- `DU XChange`: klinische Mitarbeiter, MTRA, Sekretariate und Anmeldungen mit Import-/Export-Aufgaben; 60 Minuten; Import und Export von Patientenstudien.
- `Review MTRA`: Radiologie-Mitarbeiter ohne Befundungsschwerpunkt; 60 Minuten; Review- und XChange-Funktionen fuer MTRA-Arbeitsplaetze.

Das Katalogmodell ist produktbezogen. Aktuell ist nur `DeepUnity PACS` befuellt, weitere Produkte koennen spaeter mit eigenen Inhalten ergaenzt werden.

## Architekturentscheidung

Die Testversion ist als lokale FastAPI-Anwendung mit statischem Browser-Frontend umgesetzt. Das vermeidet externe Dienste, haelt Uploads ausschliesslich im Request-Speicher und laesst sich kompakt in Docker betreiben. Der Planungsalgorithmus und die Validierung liegen serverseitig zentral, damit automatische Planung, manuelle Bearbeitung und Export dieselben Regeln verwenden.

Ab `v0.2.4` wird PostgreSQL als lokaler Docker-Service fuer strukturierte Schulungsinhalte genutzt. Originaldateien bleiben weiterhin ausserhalb der Datenbank.
