#!/bin/sh
set -eu
psql --username postgres --dbname policytime --set ON_ERROR_STOP=1 \
  --set app_password="$POLICYTIME_DB_PASSWORD" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
SELECT format('CREATE ROLE policytime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'app_password') \gexec
ALTER DATABASE policytime OWNER TO policytime;
ALTER SCHEMA public OWNER TO policytime;
SQL
