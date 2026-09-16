#!/bin/sh
set -eu
test "$#" -eq 1 || { printf 'Usage: sh deploy/restore-check.sh BACKUP.dump\n'; exit 2; }
test -f "$1"
# A separate database is used; this command never replaces the running database.
docker compose --env-file deploy/production.env -f compose.production.yaml exec -T db \
  createdb --username=postgres policytime_restore_test
docker compose --env-file deploy/production.env -f compose.production.yaml exec -T db \
  pg_restore --username=postgres --dbname=policytime_restore_test --exit-on-error < "$1"
docker compose --env-file deploy/production.env -f compose.production.yaml exec -T db \
  psql --username=postgres --dbname=policytime_restore_test --set ON_ERROR_STOP=1 \
  --command 'SELECT a.version, count(c.id) AS clauses FROM active_corpus a JOIN clauses c ON c.corpus_version = a.version GROUP BY a.version;'
printf 'Restore completed in policytime_restore_test. Inspect it before removing it.\n'
