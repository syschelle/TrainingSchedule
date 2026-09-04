# Changelog

## v0.4.1 - 2026-09-04

### Kundenpaket auf eine einzelne HTML-Datei vereinfacht

- `Kundenplanung exportieren` erzeugt weiterhin ein ZIP, damit HTML-Dateien nicht direkt als E-Mail-Anhang versendet werden muessen.
- Das ZIP enthaelt jetzt ausschliesslich `index.html`.
- Stylesheet, JavaScript, signierte Projektdaten und das Dedalus-Logo werden direkt in `index.html` eingebettet.
- Es gibt keine separaten `data.js`, `app.js`, `style.css`, PNG- oder README-Dateien mehr im Kunden-ZIP.
- Die Offline-Funktion, eingeschraenkte Drag-and-drop-Bedienung und JSON-Rueckgabe bleiben unveraendert.
- Inline-Projektdaten werden script-sicher escaped, damit Projektnamen oder Kundentexte keine eingebetteten Script-Tags beenden koennen.
- Keine PostgreSQL-Migration erforderlich.

## v0.4.0 - 2026-09-04

### Offline-Kundenplanung und XLSX-Export entfernt

- Neuer Button `Kundenplanung exportieren`: erzeugt ein eigenstaendiges Offline-ZIP mit `index.html`, CSS, JavaScript, Projektdaten und Dedalus-Logo.
- Die Kundenseite erlaubt nur Drag-and-drop vorhandener Schulungsbloecke innerhalb bereits vorhandener Wochen und Trainer. Es gibt keine Funktionen zum Loeschen/Hinzufuegen von Wochen, Bearbeiten/Loeschen/Duplizieren von Bloecken oder Resize der Blockdauer.
- Die Blockdauer bleibt beim Verschieben immer unveraendert; die Position rastet im 15-Minuten-Raster ein.
- Die Kundenseite kann eine JSON-Rueckgabedatei mit den Positionsaenderungen erzeugen.
- Neuer Import `Kundenplanung importieren` prueft die signierte Ausgangsplanung und akzeptiert ausschliesslich erlaubte Positionsaenderungen.
- Signierte Ausgangsplanung erlaubt den Rueckimport auch nach einem Browser-/App-Neustart, ohne serverseitige Projektdateien zu speichern.
- Der XLSX-Export wurde aus Frontend, API, Exporter und Runtime-Abhaengigkeiten entfernt. Der Excel-Import fuer Quelldateien bleibt erhalten.
- Keine PostgreSQL-Migration erforderlich.


## v0.3.11 - 2026-09-04

### Schulungsthemen kompakter dargestellt

- Die Terminliste nutzt eine kompakte, linksbuendige Spaltenbreite.
- `Gruppe` und `Teilnehmer` stehen dadurch deutlich naeher am Schulungsinhalt und nicht mehr am rechten Rand der Ansicht.
- Die Reihenfolge `Datum | Anfang | Ende | Dauer | Schulungsinhalt | Gruppe | Teilnehmer` bleibt unveraendert.
- Vorschau und PDF wurden auf dieselbe kompakte Darstellung angepasst.
- Keine PostgreSQL-Migration erforderlich.


## v0.3.10 - 2026-09-04

### Zeitspalten in Schulungsthemen neu angeordnet

- Die Spalten `Anfang`, `Ende` und `Dauer` stehen jetzt direkt nach `Datum`.
- Neue Reihenfolge: `Datum | Anfang | Ende | Dauer | Schulungsinhalt | Gruppe | Teilnehmer`.
- Vorschau und PDF verwenden dieselbe Reihenfolge.
- Keine PostgreSQL-Migration erforderlich.


## v0.3.9 - 2026-09-04

### Schulungstermine nach Trainer gruppiert

- Die Seite `Schulungsthemen` gruppiert Termine nach Trainer; innerhalb eines Trainerbereichs bleibt die Reihenfolge chronologisch.
- Das Datum wird mit kurzem Wochentag dargestellt, z. B. `Mo, 28.09.2026`.
- Neue Spalte `Teilnehmer` mit der fuer den jeweiligen Termin relevanten Teilnehmerzahl. Bei automatisch erzeugten `Gruppe x/y`-Sitzungen wird die Belegung anhand der Gruppengroesse und der maximalen Teilnehmer pro Sitzung berechnet.
- Vorschau und PDF verwenden dieselbe Trainer-Gruppierung, Datumsdarstellung und Teilnehmer-Spalte.
- Die Termininformationen bleiben direkt aus den aktuellen Kalenderbloecken abgeleitet und reagieren damit weiterhin auf Drag-and-drop, Resize, Trainerwechsel und Loeschen.
- Keine PostgreSQL-Migration erforderlich.


## v0.3.8 - 2026-09-04

### Bedienung von Trainer-Wochen und Zeitbloecken verbessert

- Jede Trainer-Woche besitzt einen Button `Woche löschen`. Er ist nur aktiv, wenn in dieser Trainer-Woche keine echten Schulungsbloecke mehr vorhanden sind.
- Anreise, Abreise, Pausen und Mittag verhindern das Loeschen nicht. Beim Loeschen werden diese organisatorischen Restbloecke der Trainer-Woche entfernt.
- Trainer-Wochen ohne sichtbare Bloecke werden anschliessend auch in Vorschau, PDF und XLSX nicht mehr ausgegeben.
- Trainer-Namen werden bereits waehrend der Eingabe in den Projektzustand uebernommen. Ein zweiter Klick auf `＋ Trainer` ist nicht mehr notwendig; der Button legt nur noch ein weiteres Trainerfeld an.
- Anreise und Abreise besitzen im Kalender jetzt ebenfalls obere und untere Resize-Griffe und koennen live im 15-Minuten-Raster in Start- und Endzeit veraendert werden.
- Regressionstests fuer Trainer-Eingabe, Loeschen leerer Trainer-Wochen, Resize von An-/Abreise und PDF-Ausblendung leerer Trainer-Wochen ergaenzt.
- Keine PostgreSQL-Migration erforderlich.


## v0.3.7 - 2026-09-04

### Chronologische Schulungstermine und Vorschau erweitert

- Die Seite `Schulungsthemen` listet jetzt jeden einzelnen Trainingsblock chronologisch auf.
- Jeder Termin zeigt Datum, Schulungsinhalt, optionale Gruppennummer, Trainer, Anfang, Ende und Dauer.
- Die Terminliste basiert direkt auf den aktuellen Kalenderbloecken und bleibt nach Drag-and-drop, Resize, Bearbeiten oder Loeschen synchron.
- Die Vorschau enthaelt direkt nach der Planuebersicht eine eigene Schulungsthemen-/Terminseite; umfangreiche Terminlisten werden in lesbare Folgeseiten geteilt.
- Der PDF-Export verwendet dieselbe Reihenfolge und enthaelt die chronologische Terminliste ebenfalls direkt nach der Uebersicht.
- `Planung öffnen` wurde im Eingabe-Workflow in `Planung importieren` umbenannt.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.6 - 2026-09-04

### Daueranzeige in der Schulungsuebersicht vereinfacht

- Schulungsthemen zeigen die projektspezifische Dauer nur noch einmal als Minutenwert, z. B. `DU Diagnost Basic 90 min`.
- Die doppelte Darstellung `90 / 90 min` entfaellt.
- Die zwischenzeitliche Stundenanzeige in der Web-Uebersicht wurde wieder auf Minuten umgestellt.
- PDF- und XLSX-Uebersicht verwenden dieselbe einfache Minutenangabe.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.5 - 2026-09-04

### Schulungsplan-Uebersicht und Terminuebersicht verbessert

- Doppelte Zeitangaben wie `90 / 90 min` aus der Schulungsthemenliste entfernt; die projektspezifische Dauer wird kompakt einmal in Stunden angezeigt.
- Produktzusammenfassung zeigt nur noch das aktuell geplante Produkt und nur Teilnehmergruppen mit einer Teilnehmerzahl groesser als 0.
- Neue Schulungsplan-Seite `Schulungsthemen` direkt nach `Uebersicht`.
- Pro Schulungsinhalt werden Anzahl der aktuellen Kalendertermine und der Zeitraum vom ersten Start bis zum letzten Ende angezeigt.
- Termin- und Zeitraumdaten werden aus den aktuellen Kalenderbloecken berechnet und aktualisieren sich nach Drag-and-drop, Resize, Loeschen oder Bearbeiten automatisch.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.4 - 2026-09-03

### XLSX-Export an PDF-Kalenderstruktur angepasst

- Der Excel-Export beginnt jetzt mit dem Arbeitsblatt `Übersicht` und erzeugt danach je tatsaechlich geplanter Woche ein eigenes Blatt `Woche 1`, `Woche 2` usw.
- Das Uebersichtsblatt uebernimmt die wesentlichen Inhalte und die visuelle Gliederung der PDF-Planuebersicht: Kunde, Standort, Produkt, Startdatum, Trainer, Schulungszeit, Dienstleistungstage, nicht eingeplante Zeit, Teilnehmergruppen und Schulungsthemen.
- Wochenblaetter zeigen Montag bis Freitag als Kalender mit Viertelstundenraster und farbigen Terminbloecken.
- Bei mehreren Trainern werden deren Kalender innerhalb desselben Wochenblatts untereinander dargestellt; Druckseiten werden zwischen Trainern getrennt.
- Kalenderbloecke verwenden dieselbe kompakte Anzeige wie PDF/Vorschau: Schulungsinhalt, optionale `Gruppe x/y`, Zeitbereich und Dauer. Pausen und Mittag bleiben ausgeblendet.
- Nicht geplante/leere Wochen erzeugen weiterhin kein Excel-Arbeitsblatt.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.3 - 2026-09-03

### Planungsstand-Meldung vereinfacht

- Nach dem Import einer Planung zeigt die Statusmeldung nur noch `Planungsstand geladen.`
- Die in einer aelteren Projektdatei gespeicherte App-Version wird nicht mehr in der Benutzeroberflaeche angezeigt.
- Importformat und Rueckwaertskompatibilitaet bleiben unveraendert.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.2 - 2026-09-03

### Planungsworkflow und automatische Verteilung verbessert

- Die missverstaendliche Dauer-Summenkennzahl wurde aus Schulungsauswahl und Pruefansicht entfernt.
- `Planungspruefung` wurde aus Seitenmenue und Benutzeroberflaeche entfernt; die interne Validierung bleibt bestehen.
- Dienstleistungstage werden als eindeutige Kombination aus Kalenderwoche, Tag und Trainer berechnet und damit bei Paralleltrainern korrekt gezaehlt.
- Wiederholte Teilnehmer-Sitzungen verschiedener Schulungsinhalte werden fairer proportional und gleichmaessiger gemischt. Dadurch entstehen weniger Tage, die unnoetig nur aus einem einzelnen Schulungsthema bestehen.
- Split-Haelften bleiben als zusammengehoerige Sitzung geordnet; Abhaengigkeiten werden erst freigegeben, nachdem das vorausgesetzte Thema abgearbeitet wurde.
- Ausgewaehlte Schulungsinhalte besitzen im Projektworkflow ein Feld `Dauer im Projekt`. Eine Aenderung wirkt nur auf das aktuelle Projekt und veraendert den persistenten Schulungsinhalte-Katalog nicht.
- Projektmodelle speichern die Katalogdauer und den Override-Status rueckwaertskompatibel.
- Keine PostgreSQL-Migration erforderlich.

## v0.3.1 - 2026-09-03

### Personen-Eingabe stabilisiert

- Teilnehmerzahlen koennen jetzt ohne Fokusverlust mehrstellig eingegeben werden; das Personenformular wird beim Tippen nicht mehr vollstaendig neu aufgebaut.
- Zusammenfassung, Workflow-Fortschritt, Pruefansicht und abhaengige Schulungsinformationen werden weiterhin unmittelbar aktualisiert, ohne das aktive Eingabefeld zu ersetzen.
- Teilnehmerzahl-Felder verwenden explizit ganzzahlige Schritte und einen numerischen Eingabemodus.
- Der missverstaendliche Begriff `Basisdauer` wurde im gefuehrten Workflow durch `Dauer der Auswahl` ersetzt. Gemeint ist weiterhin die Summe der ausgewaehlten Schulungsinhalte vor zusaetzlichen Wiederholungen durch Teilnehmergruppen.
- Keine Datenbankmigration erforderlich.

## v0.3.0 - 2026-09-03

### Gefuehrter Planungsworkflow

- Die Stammdateneingabe wurde fuer neue Anwender grundlegend als gefuehrter Workflow neu aufgebaut: `Produkt -> Projekt -> Personen -> Schulungen -> Zeiten -> Pruefen`.
- Der Fortschritt ist dauerhaft kompakt im Sticky-Header sichtbar; erledigte und aktuelle Schritte sind klar unterscheidbar und direkt erreichbar.
- Das Produkt wird vor allen projektspezifischen Eingaben ausgewaehlt. Produktpflege und Schulungsinhalte-Verwaltung bleiben bewusst ausserhalb des Projektworkflows.
- Projektstammdaten wurden auf Kunde, Standort und Startdatum reduziert; selten benoetigte Angaben liegen unter `Weitere Angaben`.
- Trainer und Teilnehmergruppen befinden sich gemeinsam im Schritt `Personen` und zeigen eine laufende Zusammenfassung von Trainern, Teilnehmern und Gruppen.
- Im Schritt `Schulungen` werden vorhandene Schulungsinhalte nur noch ausgewaehlt statt im Projekt erneut bearbeitet. Dauer, Teilnehmerzuordnung, Kapazitaet und Split-Status werden kompakt angezeigt.
- Haufige Zeitvorgaben sind direkt sichtbar; selten benoetigte Regeln liegen unter `Weitere Planungsregeln`.
- Der neue Schritt `Pruefen` fasst Projekt, Personen, Schulungen und Zeiten kompakt zusammen und ist der einzige Ort fuer `Plan erstellen`.
- Eingaben erzeugen oder ersetzen keinen Kalender. Nach Aenderungen an einem bestehenden Projekt bleibt der manuell bearbeitete Kalender bestehen und wird als `Eingaben geaendert` markiert, bis der Anwender explizit neu plant.
- `Eingabe` und `Schulungsplan` sind im Header als direkte Projektansichten erreichbar; ein Planwechsel loest keine automatische Neuplanung aus.
- Die Navigation ist in `Projekt` und `Verwaltung` gegliedert, damit Produkt-/Inhaltspflege klar vom aktuellen Schulungsprojekt getrennt bleibt.
- Neue Projekte starten ohne vorgefuellte Teilnehmerzahlen, ohne Startdatum und ohne automatisch ausgewaehlte Schulungsinhalte.
- Keine Datenbankmigration erforderlich.

## v0.2.48 - 2026-09-03

- Der Produktkopf zeigt nur noch den Produktnamen; `Aktives Produkt:` wird nicht mehr vorangestellt.
- Der Button `Standarddaten` wurde entfernt, um ein versehentliches Zuruecksetzen aller aktuellen Eingaben auf Standardwerte zu verhindern.
- Die zugehoerige Frontend-Reset-Ereignisbehandlung wurde entfernt; die Standardprojektdefinition bleibt ausschliesslich fuer die initiale Projektanlage erhalten.
- Keine Datenbankmigration erforderlich.

## v0.2.47 - 2026-09-03

- Schulungsinhalte besitzen jetzt die Option `Schulungsblock teilen`.
- Aktivierte Inhalte werden bei `Plan erstellen` pro erforderlicher Schulungssitzung automatisch in zwei moeglichst gleich grosse, aufeinanderfolgende Teile aufgeteilt.
- Beide Teile bleiben demselben Trainer zugeordnet; Teil 2 wird niemals vor Teil 1 eingeplant und kann bei Bedarf auf den naechsten Schulungstag wechseln.
- Teilnehmerbasierte `Gruppe x/y`-Aufteilungen werden zuerst erzeugt und anschliessend jeweils in zwei Haelften geteilt, sodass jede benoetigte Gruppe den kompletten Schulungsinhalt erhaelt.
- Die Einstellung wird persistent im Schulungsinhalte-Katalog gespeichert und beim Start bestehender Datenbanken automatisch ueber die neue Spalte `split_enabled` ergaenzt.
- Bestehende Projektdateien bleiben kompatibel; neue Planungsbloecke speichern zusaetzlich ihre Herkunft zum urspruenglichen Schulungsinhalt und optionale Teil-Metadaten.

## v0.2.46 - 2026-09-03

- Kalenderkacheln zeigen Schulungsbloecke jetzt strukturiert in bis zu drei Zeilen: Schulungsinhalt-Titel, optionale automatisch erzeugte Gruppennummer und Zeitbereich mit Gesamtdauer in Stunden.
- Die allgemeine Teilnehmergruppenbezeichnung bleibt aus der Kalenderkachel entfernt.
- `Gruppe x/y` wird bei aufgeteilten Schulungen als eigene zweite Zeile angezeigt und nicht mehr an den Titel angehaengt.
- Kalender-Vorschau und PDF-Kalenderseiten verwenden die gleiche Darstellungslogik; strukturierte Exportdaten bleiben unveraendert.
- Keine Datenbankmigration erforderlich.

## v0.2.45 - 2026-09-03

- Kalenderkacheln zeigen bei Schulungsbloecken nicht mehr die Teilnehmergruppenbezeichnung im Titel.
- Automatisch erzeugte Untergruppen bleiben sichtbar, z. B. `DU Viewer - Gruppe 4/6`.
- Nicht aufgeteilte Schulungen zeigen nur den eigentlichen Schulungstitel.
- Intern gespeicherte Titel, Planungslogik und Validierung bleiben unveraendert; die PDF-Kalenderseiten verwenden dieselbe kompakte Anzeige wie die Browser-Vorschau.
- Keine Datenbankmigration erforderlich.

## v0.2.44 - 2026-09-03

- Schriftgroesse von Kalenderkacheln skaliert jetzt stufenlos mit der tatsaechlichen Kachelhoehe.
- Beim Live-Resize werden Titel- und Zeit-/Dauer-Schrift bei jeder Hoehenaenderung direkt aktualisiert.
- Der bisher sichtbare Schriftgroessensprung beim Wechsel zwischen kompakter und normaler Kacheldarstellung entfaellt.
- Kompakte 15-/30-Minuten-Kacheln behalten weiterhin ihre platzsparenden Aktionsbuttons und das bestehende 15-Minuten-Raster.
- Keine Datenbankmigration erforderlich.

## v0.2.43 - 2026-09-03

- Schulungsbloecke im Kalender erhalten obere und untere Resize-Griffe fuer direkte Start-/Endzeit-Anpassung.
- Resize arbeitet live auf dem bestehenden 15-Minuten-Raster und aktualisiert die Kachelhoehe sofort.
- Nach Abschluss des Resize wird die bestehende Planungsvalidierung erneut ausgefuehrt.
- Kalender-Metazeile zeigt Blockdauer in Stunden statt des technischen Labels `training`.
- Auch kompakte 15-/30-Minuten-Kacheln zeigen die Zeit-/Dauerzeile in verkleinerter Form.
- Bestehendes Drag-and-drop zum Verschieben kompletter Bloecke bleibt erhalten.
- Keine Datenbankmigration erforderlich.


## v0.2.42 - 2026-09-03

### Kompakte Darstellung kurzer Kalenderbloecke

- 15- und 30-Minuten-Kalenderbloecke verwenden in der interaktiven Kalenderansicht eine eigene kompakte Darstellung.
- Die vier Aktionsbuttons werden fuer kurze Bloecke als kleinere 2x2-Gruppe dargestellt und passen vollstaendig innerhalb der Kachelhoehe.
- Der Blocktitel kann bis zu zwei Zeilen einnehmen; die zusaetzliche Zeit-/Typ-Zeile wird bei kurzen Kacheln ausgeblendet, damit Titel und Bedienelemente nicht abgeschnitten werden.
- Der vollstaendige Titel sowie Start- und Endzeit sind weiterhin ueber den Tooltip des Kalenderblocks verfuegbar.
- Die visuelle Blockhoehe bleibt an die reale Dauer gekoppelt und wird nicht kuenstlich vergroessert; dadurch bleibt die Viertelstunden-Zeitachse korrekt.

## v0.2.41 - 2026-09-02

### Leere Schulungswochen automatisch ausblenden

- Kalenderwochen ohne einen Block vom Typ `training` werden nicht mehr als bestehende Schulungswochen dargestellt.
- Werden alle Schulungsbloecke einer Woche durch Drag-and-Drop, Ausschneiden/Einfuegen, Bearbeiten oder Loeschen entfernt, verschwindet die Woche automatisch aus der Kalenderansicht.
- Die PDF-Vorschau sowie PDF- und XLSX-Export erzeugen nur noch Wochen, in denen tatsaechlich Schulungen liegen.
- Von der automatischen Planung initialisierte, aber nie mit Schulungen belegte Wochen werden nicht mehr als manuelle Wochen uebernommen.
- `Woche hinzufügen` bleibt nutzbar: eine neu angelegte leere Woche wird waehrend der aktuellen Bearbeitung angezeigt, damit dort ein erster Schulungsblock angelegt werden kann.
- Projektdateien bleiben kompatibel; vorhandene leere `manual_weeks` koennen im JSON erhalten bleiben, werden aber ohne Schulungsblock nicht als Kalender-/Exportwoche dargestellt.

## v0.2.40 - 2026-09-02

### Kompakter Anreise-Titel in Kalenderkacheln

- Anreisebloecke werden in den Kalenderkacheln nur noch als `Anreise` angezeigt.
- Der intern gespeicherte Titel `Anreise / Eintreffen der Teilnehmer` bleibt unveraendert.
- Planungslogik, Validierung sowie PDF-/XLSX-/Projekt-Exportdaten werden durch die reine Anzeigeaenderung nicht veraendert.

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
