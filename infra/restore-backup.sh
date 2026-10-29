#!/usr/bin/env bash
# PATH: infra/restore-backup.sh
# fix275: EMERGENCY ONLY. Puts a saved copy back as the LIVE database. Everything entered after that copy is lost.
# Usage on the server:  bash /opt/ges/infra/restore-backup.sh                 (uses the newest copy)
#                       bash /opt/ges/infra/restore-backup.sh /opt/ges-backups/ges-2026-11-02_0200.dump
# A copy from Google Drive: first  RCLONE_CONFIG=/root/.config/rclone/rclone.conf rclone copy gescrypt:db/<file> /opt/ges-backups/
# Before it changes anything it saves the CURRENT database as one more copy, so even a wrong restore can be undone.
set -euo pipefail
cd /opt/ges/infra
DC="docker compose -f docker-compose.prod.yml --env-file .env"
FILE="${1:-$(ls -1t /opt/ges-backups/ges-*.dump 2>/dev/null | head -1 || true)}"
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "No copy file found."; exit 1; }
echo "Restore from: $FILE"
echo "This REPLACES the live database. Anything entered after this copy is lost."
read -rp "Type RESTORE to go on: " A </dev/tty
[ "$A" = "RESTORE" ] || { echo "Cancelled. Nothing was changed."; exit 1; }
echo "1/4 Saving the current database first..."
mkdir -p /opt/ges-backups
$DC exec -T db pg_dump -U ges -d ges --format=custom --no-owner > "/opt/ges-backups/before-restore-$(date +%Y%m%d-%H%M%S).dump"
echo "2/4 Stopping the app..."
$DC stop backend
echo "3/4 Putting the copy in..."
$DC exec -T db psql -U ges -d ges -v ON_ERROR_STOP=1 -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
$DC exec -T db pg_restore -U ges -d ges --no-owner --exit-on-error < "$FILE"
echo "4/4 Starting the app..."
$DC start backend
echo "=== DONE === Open the app and check. The documents are not touched by this (they are in /opt/ges/infra/ge_uploads)."
