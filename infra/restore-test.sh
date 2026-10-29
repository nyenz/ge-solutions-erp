#!/usr/bin/env bash
# PATH: infra/restore-test.sh
# fix275: proves the newest nightly copy can really be restored. It restores into a throw-away database called
# restore_test, compares a few numbers with the live database, and deletes the throw-away database. The live app is
# not touched. Run as root on the server:  bash /opt/ges/infra/restore-test.sh
set -euo pipefail
cd /opt/ges/infra
DC="docker compose -f docker-compose.prod.yml --env-file .env"
LATEST=$(ls -1t /opt/ges-backups/ges-*.dump 2>/dev/null | head -1 || true)
[ -n "$LATEST" ] || { echo "No copy found in /opt/ges-backups."; exit 1; }
echo "Testing: $LATEST"
$DC exec -T db psql -U ges -d postgres -q -c "DROP DATABASE IF EXISTS restore_test;" -c "CREATE DATABASE restore_test;"
$DC exec -T db pg_restore -U ges -d restore_test --no-owner --exit-on-error < "$LATEST"
Q="SELECT (SELECT count(*) FROM users) AS users, (SELECT count(*) FROM land_projects) AS projects, (SELECT count(*) FROM information_schema.tables WHERE table_schema='public') AS tables;"
echo "--- the copy:"; $DC exec -T db psql -U ges -d restore_test -c "$Q"
echo "--- the live database now:"; $DC exec -T db psql -U ges -d ges -c "$Q"
$DC exec -T db psql -U ges -d postgres -q -c "DROP DATABASE restore_test;"
echo "=== DONE === If the numbers look right, the copy works. (The copy can be a day older than the live data.)"
