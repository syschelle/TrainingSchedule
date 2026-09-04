# Produktionsinstallation v0.3.7

## 1. Repository klonen

```bash
git clone <REPOSITORY-URL> Schulungsplantool
cd Schulungsplantool
```

## 2. Installieren

```bash
./install.sh
```

Die Installation verwendet standardmaessig `docker-compose.images.yml`, erzeugt bei Bedarf `.env` mit einem zufaelligen PostgreSQL-Passwort, zieht das Multi-Arch-Image aus GHCR und startet die Container.

## 3. Netzwerkmodell

Nur die Webanwendung wird auf dem Host veroeffentlicht:

```text
0.0.0.0:${APP_PORT:-18083} -> schulungsplantool:8000
```

PostgreSQL besitzt absichtlich **kein Host-Port-Mapping**. Es gibt insbesondere kein `5432:5432`. Die Datenbank ist nur im privaten Compose-Netz unter `postgres:5432` fuer die Webapp erreichbar.

## 4. Status pruefen

```bash
docker compose -f docker-compose.images.yml ps
curl http://127.0.0.1:18083/api/health
```

## 5. Update

```bash
./update.sh
```

Das PostgreSQL-Volume `schulungsplantool_pgdata` bleibt erhalten. Falls eine Installation noch von einem Stand vor v0.2.26 kommt, werden das Markdown-Feld und die Historientabelle beim Start automatisch angelegt. v0.2.47 erweitert bestehende `training_contents`-Tabellen beim Start automatisch um die boolesche Spalte `split_enabled`. Es ist kein manueller SQL-Schritt erforderlich. Die Mehrtrainer- und Projektdatei-Funktionen werden weiterhin im Projektmodell abgebildet und benoetigen keine neue PostgreSQL-Tabelle. Beim Start werden bestehende Markdown-Historien automatisch auf maximal 5 Eintraege pro Schulungsinhalt begrenzt.

## 6. Backup

```bash
./scripts/backup-db.sh
```

## 7. Manuelle Image-Installation

```bash
docker compose -f docker-compose.images.yml pull
docker compose -f docker-compose.images.yml up -d --remove-orphans
```

Standard-Image fuer die Produktion:

```text
ghcr.io/syschelle/schulungsplantool:latest
```

Fuer reproduzierbare Rollbacks steht zusaetzlich der Versions-Tag `ghcr.io/syschelle/schulungsplantool:0.3.7` zur Verfuegung.

Unterstuetzte Architekturen: `linux/amd64` und `linux/arm64`.

## 8. Lokaler Build

Fuer Entwicklung/Test kann weiterhin lokal gebaut werden:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

Auch in diesem Modus ist PostgreSQL nicht auf dem Host veroeffentlicht.

## 9. Wichtiger Hinweis

Zum normalen Update niemals `docker compose down -v` verwenden. `-v` wuerde das PostgreSQL-Volume und damit gespeicherte Produkt- und Schulungsinhalte entfernen.
