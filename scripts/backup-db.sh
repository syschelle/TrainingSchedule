#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p backups

set -a
# shellcheck disable=SC1091
source .env
set +a

timestamp="$(date +%Y%m%d-%H%M%S)"
out="backups/schulungsplantool-${timestamp}.sql.gz"

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-schulungsplantool}" \
  -d "${POSTGRES_DB:-schulungsplantool}" | gzip > "${out}"

echo "Backup erstellt: ${out}"
