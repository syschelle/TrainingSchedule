#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.images.yml}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Fehler: Docker wurde nicht gefunden." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Fehler: Docker Compose v2 wurde nicht gefunden." >&2
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Fehler: Compose-Datei ${COMPOSE_FILE} wurde nicht gefunden." >&2
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
  if command -v openssl >/dev/null 2>&1; then
    exchange_secret="$(openssl rand -hex 32)"
  else
    exchange_secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
  fi
  sed -i "s/^CUSTOMER_EXCHANGE_SECRET=.*/CUSTOMER_EXCHANGE_SECRET=${exchange_secret}/" .env
  chmod 600 .env
  echo "Lokale .env wurde mit einem zufaelligen PostgreSQL-Passwort erzeugt."
else
  echo "Vorhandene .env wird unveraendert verwendet."
fi

current_exchange_secret="$(grep '^CUSTOMER_EXCHANGE_SECRET=' .env | cut -d= -f2- || true)"
if [[ -z "${current_exchange_secret}" || "${current_exchange_secret}" == "change-me" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    exchange_secret="$(openssl rand -hex 32)"
  else
    exchange_secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
  fi
  if grep -q '^CUSTOMER_EXCHANGE_SECRET=' .env; then
    sed -i "s/^CUSTOMER_EXCHANGE_SECRET=.*/CUSTOMER_EXCHANGE_SECRET=${exchange_secret}/" .env
  else
    printf '\nCUSTOMER_EXCHANGE_SECRET=%s\n' "${exchange_secret}" >> .env
  fi
  chmod 600 .env
  echo "CUSTOMER_EXCHANGE_SECRET wurde fuer stabile Kundenrueckimporte erzeugt."
fi

echo "Verwende ${COMPOSE_FILE}."
docker compose -f "${COMPOSE_FILE}" config >/dev/null
docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

echo
docker compose -f "${COMPOSE_FILE}" ps
echo
echo "Schulungsplantool wurde gestartet."
echo "Nur der Webport wird auf dem Host veroeffentlicht; PostgreSQL besitzt kein Host-Port-Mapping."
echo "Aufruf: http://localhost:$(grep '^APP_PORT=' .env | cut -d= -f2 || echo 18083)"
