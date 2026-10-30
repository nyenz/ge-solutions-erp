#!/usr/bin/env bash
# PATH: infra/deploy.sh
# fix276: puts the app on the Netcup server, or UPDATES it SAFELY. Run as root ON THE SERVER.
#   first time:  git clone https://github.com/nyenz/ge-solutions-erp.git /opt/ges && bash /opt/ges/infra/deploy.sh ges-erp.duckdns.org
#   later:       bash /opt/ges/infra/deploy.sh
#   force:       bash /opt/ges/infra/deploy.sh --force     (also rebuild when nothing is new, or when this version was rolled back)
#
# THE SAFE-UPDATE RULE (David, 30 Oct 2026): no update may ever break the app or lose data. So every update:
#   1. makes a safety copy of the data FIRST (if that fails, nothing is changed);
#   2. keeps the running version's images as "previous";
#   3. builds the new version (a failed build leaves the running app untouched);
#   4. checks the new version really works (server answers, front door answers, no start-up fault in the log);
#   5. if any check fails it puts the previous version back by itself (rollback.sh --auto) and says so.
# The secrets (database password, login signing key) are made here with random values and kept ONLY in
# /opt/ges/infra/.env on this server. They are never in GitHub and never need to be typed or remembered.
set -euo pipefail

APP="${GES_APP:-/opt/ges}"
FORCE=0; DOMAIN_ARG=""
for a in "$@"; do case "$a" in --force) FORCE=1 ;; *) DOMAIN_ARG="$a" ;; esac; done
DC="docker compose -f docker-compose.prod.yml --env-file .env"

# ---------------------------------------------------------------- stage 1: safety copy, then fetch the new code
if [ -z "${GES_DEPLOY_STAGE2:-}" ]; then
    cd "$APP"
    OLD=$(git rev-parse HEAD)
    cd "$APP/infra"
    if [ -f .env ] && [ -n "$($DC ps -q db 2>/dev/null || true)" ]; then
        echo "=== Safety copy of the data first ==="
        if ! bash "$APP/infra/nightly-backup.sh"; then
            echo "The safety copy FAILED. Nothing was changed. Tell Claude what you see above."
            exit 1
        fi
    fi
    cd "$APP"
    if ! git pull --ff-only; then
        echo "Could not fetch the new version. Nothing was changed."
        exit 1
    fi
    NEW=$(git rev-parse HEAD)
    if [ -f "$APP/infra/.rolled-back-from" ] && [ "$(cat "$APP/infra/.rolled-back-from")" = "$NEW" ] && [ "$FORCE" = 0 ]; then
        echo "This version ($NEW) was already tried and ROLLED BACK because it failed."
        echo "Do not update until Claude says a fix is merged. (Only if told to: bash infra/deploy.sh --force)"
        exit 1
    fi
    export GES_DEPLOY_STAGE2=1 GES_OLD_COMMIT="$OLD" GES_NEW_COMMIT="$NEW"
    exec bash "$APP/infra/deploy.sh" "$@"   # continue with the freshly fetched copy of this script
fi

# ---------------------------------------------------------------- stage 2: build, start, check, roll back if needed
OLD="$GES_OLD_COMMIT"; NEW="$GES_NEW_COMMIT"
cd "$APP/infra"

if [ ! -f .env ]; then
    DOMAIN="$DOMAIN_ARG"
    [ -n "$DOMAIN" ] || read -rp "Web address (for example ges-erp.duckdns.org): " DOMAIN </dev/tty
    umask 077
    {
        echo "GES_DOMAIN=$DOMAIN"
        echo "DB_PASSWORD=$(openssl rand -hex 24)"
        echo "JWT_SECRET=$(openssl rand -base64 48 | tr -d '\n')"
        echo "ADMIN_DEFAULT_PASSWORD=$(openssl rand -hex 16)"
        echo "SEED_DEMO_DATA=false"
    } > .env
    chmod 600 .env
    echo "Settings saved on this server."
fi

DOMAIN=$(grep '^GES_DOMAIN=' .env | cut -d= -f2-)
MYIP=$(curl -fsS --max-time 10 https://api.ipify.org 2>/dev/null || true)
DNSIP=$(getent ahostsv4 "$DOMAIN" | awk '{print $1; exit}' || true)
if [ -n "$MYIP" ] && [ "$MYIP" != "$DNSIP" ]; then
    echo "WARNING: $DOMAIN points to '${DNSIP:-nothing}' but this server is $MYIP. The padlock cannot be made until they match."
fi

# fix282: "newest" means the version that is really RUNNING (infra/.deployed-commit, written only after every check passed),
# not just the code on disk. Someone running a plain "git pull" first used to make this script think nothing was new.
DEPLOYED=""; [ -f "$APP/infra/.deployed-commit" ] && DEPLOYED=$(cat "$APP/infra/.deployed-commit")
if [ "$OLD" = "$NEW" ] && [ "$DEPLOYED" = "$NEW" ] && [ "$FORCE" = 0 ] && [ -n "$($DC ps -q backend 2>/dev/null || true)" ]; then
    echo "Nothing new to install: this server already has the newest version ($NEW). (Use --force to rebuild anyway.)"
    exit 0
fi

# keep the running version as "previous" so it can be put back
HAD_PREVIOUS=0
for svc in backend frontend; do
    if docker image inspect "ges-$svc:latest" >/dev/null 2>&1; then
        docker tag "ges-$svc:latest" "ges-$svc:previous"; HAD_PREVIOUS=1
    fi
done
PREV="$OLD"; [ -n "$DEPLOYED" ] && PREV="$DEPLOYED"
if [ "$PREV" = "$NEW" ]; then rm -f "$APP/infra/.previous-commit"; else echo "$PREV" > "$APP/infra/.previous-commit"; fi

go_back() {
    echo
    echo "!!! The new version did NOT pass the checks: $1"
    if [ "$HAD_PREVIOUS" = 1 ]; then
        echo "!!! Putting the previous version back now..."
        if bash "$APP/infra/rollback.sh" --auto; then
            echo "!!! The previous version is back and working. Your data is as it was. Tell Claude: \"the update was rolled back\"."
        else
            echo "!!! The automatic rollback also failed. Do not panic: the safety copy is in /opt/ges-backups. Tell Claude what you see above."
        fi
    else
        echo "!!! There is no previous version to go back to (this was the first install). Tell Claude what you see above."
    fi
    exit 1
}

echo "=== Building the new version (the first time 8 to 15 minutes, later about 1 to 4) ==="
if ! $DC build; then
    ( cd "$APP" && git reset --hard "$OLD" >/dev/null 2>&1 ) || true
    echo "The new version could not be BUILT. The running app was NOT touched and is still the old version."
    echo "Tell Claude what you see above."
    exit 1
fi
$DC up -d

echo "=== Checking that the new version really works ==="
ok=0
for i in $(seq 1 40); do
    if $DC exec -T backend wget -qO- http://localhost:8080/api/v1/auth/health >/dev/null 2>&1; then ok=1; break; fi
    sleep "${GES_WAIT_STEP:-4}"
done
[ "$ok" = 1 ] || go_back "the server did not answer in time"
sleep "${GES_WAIT_STEP:-3}"
if $DC logs --since 10m backend 2>&1 | grep -qE "FATAL STARTUP ERROR|APPLICATION FAILED TO START|Application run failed"; then
    go_back "the server reported a start-up fault"
fi
curl -fsSk --max-time 20 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/" >/dev/null 2>&1 || go_back "the website did not open through the front door"
curl -fsSk --max-time 20 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/api/v1/auth/health" >/dev/null 2>&1 || go_back "the server did not answer through the front door"

rm -f "$APP/infra/.rolled-back-from"
echo "$NEW" > "$APP/infra/.deployed-commit"
docker image prune -f >/dev/null 2>&1 || true
$DC ps
LASTCOPY=$(ls -1t "${GES_BACKUPS:-/opt/ges-backups}"/ges-*.dump 2>/dev/null | head -1 || true)
echo "=== DONE === The new version works. Open https://$DOMAIN in the browser."
[ -z "$LASTCOPY" ] || echo "Safety copy from before this update: $LASTCOPY"
echo "If anything looks wrong, undo with:  bash $APP/infra/rollback.sh"
