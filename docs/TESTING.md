# Schulungsplantool – interne Tests und Freigabeprüfungen

Stand: **v0.4.10**

Dieses Dokument beschreibt die Prüfungen, die vor der Bereitstellung einer neuen Version des Schulungsplantools durchgeführt werden. Es trennt zwischen den automatisierten Regressionstests im Repository, zusätzlichen Syntax-/Konfigurationsprüfungen und Prüfungen, die erst in GitHub CI vollständig möglich sind.

## 1. Automatisierte Python-/Regressionstests

Die komplette Test-Suite wird mit Pytest ausgeführt:

```bash
python -m pytest -q
```

Für **v0.4.10** lautet das Ergebnis:

```text
142 passed
```

### Testaufteilung in v0.4.10

| Testdatei | Anzahl | Schwerpunkt |
|---|---:|---|
| `tests/test_static_paths.py` | 64 | Frontend-Struktur, UI-Regeln, Kalender, KundenHTML, Versionsregressionen |
| `tests/test_planner.py` | 33 | automatische Planung, Pausen, Trainerverfügbarkeit, An-/Abreise, Remote/Vor-Ort |
| `tests/test_project_export.py` | 25 | Projektdateien, PDF, KundenHTML, Rückimport, Manipulationsschutz |
| `tests/test_content_catalog.py` | 10 | Schulungsinhalte, Produkte, Historie und Persistenz |
| `tests/test_docx_training_content.py` | 6 | DOCX Import/Export und Schutz vor nicht unterstützten Inhalten |
| `tests/test_codeql_workflow.py` | 2 | CodeQL-Konfiguration und Sprachmatrix |
| `tests/test_security_regressions.py` | 2 | sicherheitsrelevante Regressionen |
| **Gesamt** | **142** | |

## 2. Wichtige fachliche Regressionstests

Die Test-Suite deckt unter anderem folgende fachliche Regeln ab:

- Anreise und Abreise werden bei **Vor-Ort-Schulungen** korrekt reserviert.
- Bei **Remote-Schulungen** werden keine Anreise- oder Abreiseblöcke erzeugt.
- Alte Projekte ohne Delivery-Mode bleiben kompatibel und werden als **Vor Ort** behandelt.
- Schulungen werden auf dem 15-Minuten-Raster geplant.
- In der KundenHTML müssen zwischen zwei Schulungsblöcken desselben Trainers mindestens **15 Minuten Pause** verbleiben.
- Genau 15 Minuten Abstand werden akzeptiert; weniger als 15 Minuten werden beim Rückimport abgelehnt.
- Unsichtbare Pausen- und Mittagspausenblöcke dürfen das Verschieben sichtbarer Blöcke in der KundenHTML nicht blockieren.
- Geparkte Schulungsblöcke können auf einen gültigen Schulungstag zurückverschoben werden.
- Schulungsblöcke auf nicht verfügbaren Trainertagen werden als geparkt erkannt.
- Ein Kunden-Rückimport darf die Dauer eines Blocks nicht manipulieren.
- Manipulationen an der signierten Ausgangsbasis werden abgelehnt.
- Sichtbare Blöcke dürfen sich nicht überschneiden.
- Automatisch erzeugte Mittagspausen dürfen keine Schulungsblöcke überlagern.
- Trainerverfügbarkeiten, einschließlich expliziter Freitage, werden berücksichtigt.
- Mehrere Trainer können parallel geplant werden, ohne sich gegenseitig fälschlich zu blockieren.
- Projektdateien können exportiert und wieder eingelesen werden, ohne den Planungszustand zu verlieren.

## 3. JavaScript-Syntaxprüfung

Zusätzlich werden alle aktuell verwendeten JavaScript-Dateien mit Node.js syntaktisch geprüft:

```bash
node --check app/static/app.js
node --check app/static/calendar.js
node --check app/customer_assets/app.js
```

Damit werden unter anderem Syntaxfehler erkannt, die erst im Browser auffallen würden.

## 4. GitHub-Workflow-/YAML-Prüfung

Die GitHub-Workflow-Dateien werden auf gültige YAML-Struktur geprüft:

```text
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/release-image.yml
```

Zusätzlich enthält die Pytest-Suite Regressionstests für den CodeQL-Workflow. Dabei wird insbesondere geprüft, dass nur die vorgesehenen CodeQL-Sprachen verwendet werden und `actions` nicht versehentlich wieder als eigene Analyse-Sprache aktiviert wird.

## 5. CodeQL

CodeQL ist für folgende Sprachen konfiguriert:

```text
python
javascript-typescript
```

Die eigentliche CodeQL-Analyse läuft in GitHub Actions. Lokal bzw. in der internen Prüfungsumgebung kann die GitHub-CodeQL-Infrastruktur nicht vollständig nachgebildet werden.

Vor dem Taggen einer neuen Version sollte deshalb kontrolliert werden, dass die CodeQL-Jobs in GitHub erfolgreich abgeschlossen wurden.

## 6. Docker-/Compose-Prüfungen

GitHub CI führt zusätzlich folgende Prüfungen aus:

```bash
docker compose -f docker-compose.yml config >/dev/null
docker compose -f docker-compose.images.yml config >/dev/null
docker build --build-arg APP_VERSION="$(cat VERSION)" -t schulungsplantool:ci .
```

Damit werden beide Compose-Dateien validiert und das Anwendungsimage gebaut.

**Wichtig:** Wenn in der internen Ausführungsumgebung kein Docker-CLI vorhanden ist, können diese Prüfungen dort nicht ausgeführt werden. In diesem Fall werden sie nicht als lokal bestanden bezeichnet; maßgeblich ist dann der GitHub-CI-Lauf.

## 7. Release-Prüfung vor dem Tag

Vor dem Erstellen eines Tags sollte mindestens Folgendes erfüllt sein:

- `python -m pytest -q` ist vollständig grün.
- JavaScript-Syntaxprüfungen sind grün.
- GitHub-Workflow-YAML ist gültig.
- GitHub CI ist grün.
- CodeQL ist grün.
- Die Versionsnummer in `VERSION` entspricht der vorgesehenen Release-Version.
- Erst danach wird der Git-Tag erstellt und gepusht.

Empfohlener Ablauf:

```bash
git add .
git commit -m "Release vX.Y.Z: <Beschreibung>"
git push origin main
```

Danach CI und CodeQL kontrollieren. Wenn beide erfolgreich sind:

```bash
git tag -a vX.Y.Z -m "Schulungsplantool vX.Y.Z"
git push origin vX.Y.Z
```

## 8. Zusätzliche Prüfungen bei Änderungen an der KundenHTML

Wenn Drag & Drop, Parken, Remote/Vor-Ort oder der Rückimport verändert werden, werden zusätzlich gezielte Regressionstests ergänzt. Typische Szenarien sind:

1. Block innerhalb desselben Tages verschieben.
2. Block auf einen anderen gültigen Tag verschieben.
3. Geparkten Block wieder auf einen gültigen Tag zurückholen.
4. Zielposition liegt auf einer unsichtbaren Pause.
5. Zielposition würde weniger als 15 Minuten Abstand zur vorherigen Schulung erzeugen.
6. Zielposition würde weniger als 15 Minuten Abstand zur folgenden Schulung erzeugen.
7. Genau 15 Minuten Abstand müssen akzeptiert werden.
8. Überlappungen sichtbarer Blöcke müssen abgelehnt werden.
9. Die Dauer des verschobenen Blocks muss unverändert bleiben.
10. Bei Remote-Projekten dürfen keine An-/Abreiseblöcke auftauchen.

## 9. Bekannte Hinweise in v0.4.10

Die aktuelle Test-Suite meldet zwei `DeprecationWarning`-Hinweise von FastAPI bezüglich `@app.on_event("startup")`. Diese Warnungen führen nicht zu einem Testfehler, sollten aber in einer späteren Version auf FastAPI-Lifespan-Handler umgestellt werden.

```text
142 passed, 2 warnings
```

## 10. Grundsatz für zukünftige Versionen

Eine Version wird nicht allein deshalb als erfolgreich geprüft bezeichnet, weil einzelne Tests bestanden haben. Für eine Freigabe werden die verfügbaren lokalen Prüfungen vollständig ausgeführt und GitHub CI sowie CodeQL anschließend separat kontrolliert. Wenn eine Prüfung wegen fehlender Laufzeitwerkzeuge – zum Beispiel Docker – nicht möglich ist, wird dies ausdrücklich angegeben.
