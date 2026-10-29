#!/usr/bin/env bash
# PATH: infra/rollback.sh
# fix276: puts the PREVIOUS version of the app back (the one that ran before the last update). One line:
#   bash /opt/ges/infra/rollback.sh
# It changes only the PROGRAM, never the data. The data is exactly as it is now. (Data restored from a copy is a
# different job: infra/restore-backup.sh.) deploy.sh calls this by itself, with --auto, when a new version fails its checks.
set -euo pipefail
APP="${GES_APP:-/opt/ges}"
AUTO=0; [ "${1:-}" = "--auto" ] && AUTO=1
cd "$APP/infra"
DC="docker compose -f docker-compose.prod.yml --env-file .env"

for svc in backend frontend; do
    docker image inspect "ges-$svc:previous" >/dev/null 2>&1 || { echo "There is no previous version of the $svc saved. Nothing to go back to."; exit 1; }
done
if [ "$AUTO" = 0 ]; then
    echo "This puts the PREVIOUS version of the app back. The data stays as it is now."
    if [ -r /dev/tty ] && ( : </dev/tty ) 2>/dev/null; then read -rp "Type ROLLBACK to go on: " A </dev/tty; else read -rp "Type ROLLBACK to go on: " A; fi
    [ "$A" = "ROLLBACK" ] || { echo "Cancelled. Nothing was changed."; exit 1; }
fi

BROKEN=$(cd "$APP" && git rev-parse HEAD)
for svc in backend frontend; do docker tag "ges-$svc:previous" "ges-$svc:latest"; done
$DC up -d --no-build --force-recreate backend frontend

ok=0
for i in $(seq 1 40); do
    if $DC exec -T backend wget -qO- http://localhost:8080/api/v1/auth/health >/dev/null 2>&1; then ok=1; break; fi
    sleep "${GES_WAIT_STEP:-4}"
done
[ "$ok" = 1 ] || { echo "The previous version did not answer. Tell Claude. The safety copies are in /opt/ges-backups."; exit 1; }

# make the code on this server match the version that is running, and remember the bad one so deploy.sh will not rebuild it
if [ -f "$APP/infra/.previous-commit" ]; then
    echo "$BROKEN" > "$APP/infra/.rolled-back-from"
    ( cd "$APP" && git reset --hard "$(cat "$APP/infra/.previous-commit")" >/dev/null 2>&1 ) || true
fi
$DC ps
echo "=== DONE === The previous version is running again. Do not run deploy.sh until Claude says a fix is ready."
