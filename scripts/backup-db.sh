#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.images.yml}"
mkdir -p backups

if [[ ! -f .env ]]; then
  echo "Fehler: .env fehlt." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

timestamp="$(date +%Y%m%d-%H%M%S)"
out="backups/schulungsplantool-${timestamp}.sql.gz"

docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-schulungsplantool}" \
  -d "${POSTGRES_DB:-schulungsplantool}" | gzip > "${out}"

echo "Backup erstellt: ${out}"
