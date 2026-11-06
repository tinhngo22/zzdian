#!/usr/bin/env bash
# Run on the Linux deployment host; the output contains private user data.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
env_file="${1:-.env.production}"
backup_dir="${2:-backups}"
mkdir -p -- "$backup_dir"
target="$backup_dir/hanzi-$(date -u +%Y%m%dT%H%M%S)-$$.dump"
temporary="${target}.partial"
trap 'rm -f -- "$temporary"' EXIT
docker compose --env-file "$env_file" -f compose.production.yml exec -T db \
  sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$temporary"
test -s "$temporary"
mv -- "$temporary" "$target"
printf 'Backup saved: %s\n' "$target"
