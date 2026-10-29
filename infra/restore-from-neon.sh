#!/usr/bin/env bash
# PATH: infra/restore-from-neon.sh
# fix270: copies ALL the data from the Neon database into the new database on this server.
# Neon is only READ; nothing is changed or deleted there. Run as root on the server:  bash /opt/ges/infra/restore-from-neon.sh
# It asks for the Neon connection address (hidden while you type). A copy of the data is also kept in /opt/ges-backups.
set -euo pipefail
cd /opt/ges/infra
read -rsp "Neon connection address (starts with postgresql://, hidden): " NEON </dev/tty; echo
[ -n "$NEON" ] || { echo "Nothing entered."; exit 1; }
mkdir -p /opt/ges-backups; chmod 700 /opt/ges-backups
FILE="/opt/ges-backups/neon-$(date +%Y%m%d-%H%M%S).dump"

NEONVER=$(docker run --rm postgres:17 psql "$NEON" -Atc "show server_version" 2>/dev/null || true)
echo "Neon database version: ${NEONVER:-unknown}"

echo "1/4 Reading the data from Neon..."
docker run --rm postgres:17 pg_dump "$NEON" --no-owner --no-privileges --format=custom > "$FILE"
ls -lh "$FILE"

echo "2/4 Stopping the app for a moment..."
docker compose -f docker-compose.prod.yml --env-file .env stop backend

echo "3/4 Putting the data into the new database..."
docker compose -f docker-compose.prod.yml --env-file .env exec -T db psql -U ges -d ges -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose -f docker-compose.prod.yml --env-file .env exec -T db pg_restore -U ges -d ges --no-owner --no-privileges --exit-on-error < "$FILE"

echo "4/4 Starting the app..."
docker compose -f docker-compose.prod.yml --env-file .env start backend

echo "Number of rows in the biggest tables now on this server:"
docker compose -f docker-compose.prod.yml --env-file .env exec -T db psql -U ges -d ges -c "SELECT relname AS table, n_live_tup AS rows FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 8;"
echo "=== DONE === Log in on the new address and check your data."
