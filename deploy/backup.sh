#!/bin/sh
set -eu
umask 077
mkdir -p backups
target="backups/policytime-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose --env-file deploy/production.env -f compose.production.yaml exec -T db \
  pg_dump --username=postgres --dbname=policytime --format=custom > "$target"
test -s "$target"
printf 'Created %s\n' "$target"
