#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.images.yml}"

if [[ ! -f .env ]]; then
  echo "Fehler: .env fehlt. Fuer eine Erstinstallation scripts/install.sh verwenden." >&2
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Fehler: Compose-Datei ${COMPOSE_FILE} wurde nicht gefunden." >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
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

docker compose -f "${COMPOSE_FILE}" config >/dev/null
docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

docker compose -f "${COMPOSE_FILE}" ps
