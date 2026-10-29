#!/usr/bin/env bash
# PATH: infra/deploy.sh
# fix270: puts the app on the Netcup server, or updates it. Run as root ON THE SERVER:
#   first time:  git clone https://github.com/nyenz/ge-solutions-erp.git /opt/ges && bash /opt/ges/infra/deploy.sh ges-erp.duckdns.org
#   later:       bash /opt/ges/infra/deploy.sh
# The secrets (database password, login signing key) are made here with random values and kept ONLY in
# /opt/ges/infra/.env on this server. They are never in GitHub and never need to be typed or remembered.
set -euo pipefail

APP=/opt/ges
cd "$APP"
git pull --ff-only || echo "(could not pull; building what is here)"
cd "$APP/infra"

if [ ! -f .env ]; then
    DOMAIN="${1:-}"
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
MYIP=$(curl -fsS https://api.ipify.org 2>/dev/null || true)
DNSIP=$(getent ahostsv4 "$DOMAIN" | awk '{print $1; exit}' || true)
if [ -n "$MYIP" ] && [ "$MYIP" != "$DNSIP" ]; then
    echo "WARNING: $DOMAIN points to '${DNSIP:-nothing}' but this server is $MYIP. The padlock cannot be made until they match."
fi

echo "Building and starting (the first time this takes 8 to 15 minutes)..."
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker image prune -f >/dev/null 2>&1 || true

echo "Waiting for the server to wake up..."
for i in $(seq 1 60); do
    if docker compose -f docker-compose.prod.yml exec -T backend wget -qO- http://localhost:8080/api/v1/auth/health >/dev/null 2>&1; then
        echo "The server answers."
        docker compose -f docker-compose.prod.yml ps
        echo "=== DONE === Open https://$DOMAIN in the browser."
        exit 0
    fi
    sleep 5
done
echo "The server did not answer in time. Last lines of its log:"
docker compose -f docker-compose.prod.yml logs --tail 40 backend
exit 1
