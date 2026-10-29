#!/usr/bin/env bash
# PATH: infra/nightly-backup.sh
# fix271: one copy of the whole database every night, kept for 14 days, in /opt/ges-backups on this server.
# It is started by cron (see infra/setup-backups.sh). You can also run it by hand: bash /opt/ges/infra/nightly-backup.sh
set -euo pipefail
cd /opt/ges/infra
DIR=/opt/ges-backups
mkdir -p "$DIR"; chmod 700 "$DIR"
FILE="$DIR/ges-$(date +%Y-%m-%d_%H%M).dump"
docker compose -f docker-compose.prod.yml --env-file .env exec -T db pg_dump -U ges -d ges --format=custom --no-owner > "$FILE.part"
# a copy that is too small is a failed copy
if [ "$(stat -c %s "$FILE.part")" -lt 20000 ]; then
    echo "$(date) BACKUP FAILED: file too small" >&2
    rm -f "$FILE.part"
    exit 1
fi
mv "$FILE.part" "$FILE"
find "$DIR" -name 'ges-*.dump' -mtime +14 -delete
# fix273: the uploaded documents live on this disk too: keep a second copy of them next to the database copies
if [ -d /opt/ges/infra/ge_uploads ]; then
    mkdir -p "$DIR/files-latest"
    rsync -a /opt/ges/infra/ge_uploads/ "$DIR/files-latest/"
fi
echo "$(date) backup ok: $FILE ($(du -h "$FILE" | cut -f1))"
