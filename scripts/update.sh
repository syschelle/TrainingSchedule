#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -f .env ]]; then
  echo "Fehler: .env fehlt. Fuer eine Erstinstallation scripts/install.sh verwenden." >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

docker compose config >/dev/null
docker compose build --pull
docker compose up -d --remove-orphans

docker compose ps
