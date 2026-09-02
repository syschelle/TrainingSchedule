# Produktionsinstallation

## 1. Repository klonen

```bash
git clone <REPOSITORY-URL> Schulungsplantool
cd Schulungsplantool
```

## 2. Installation starten

```bash
./scripts/install.sh
```

Bei der ersten Ausfuehrung wird `.env` aus `.env.example` erzeugt und ein zufaelliges PostgreSQL-Passwort gesetzt.

## 3. Status pruefen

```bash
docker compose ps
curl http://127.0.0.1:18083/api/health
```

Beide Container sollen `healthy` anzeigen.

## 4. Port oder Bind-Adresse aendern

`.env` bearbeiten:

```text
APP_BIND=0.0.0.0
APP_PORT=18083
```

Danach:

```bash
docker compose up -d
```

## 5. Update

```bash
./scripts/update.sh
```

Das PostgreSQL-Volume bleibt dabei erhalten.

## 6. Backup vor groesseren Updates

```bash
./scripts/backup-db.sh
```

## 7. Wichtiger Hinweis

Zum normalen Update niemals `docker compose down -v` verwenden. `-v` wuerde das PostgreSQL-Volume und damit die gespeicherten Schulungsinhalte entfernen.
