#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Fehler: Docker wurde nicht gefunden." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Fehler: Docker Compose v2 wurde nicht gefunden." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  if command -v openssl >/dev/null 2>&1; then
    db_password="$(openssl rand -hex 24)"
  else
    db_password="$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
  fi
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${db_password}/" .env
  sed -i "s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://schulungsplantool:${db_password}@postgres:5432/schulungsplantool#" .env
  chmod 600 .env
  echo "Lokale .env wurde mit einem zufaelligen PostgreSQL-Passwort erzeugt."
else
  echo "Vorhandene .env wird unveraendert verwendet."
fi

docker compose config >/dev/null
docker compose pull
docker compose up -d --remove-orphans

echo
docker compose ps
echo
echo "Schulungsplantool wurde gestartet."
echo "Aufruf: http://localhost:$(grep '^APP_PORT=' .env | cut -d= -f2 || echo 18083)"
