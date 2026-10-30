#!/usr/bin/env bash
# PATH: infra/setup-mail.sh
# fix279: lets the app email the owner recovery code, using a Gmail address.
# Run once as root on the server:  cd /opt/ges && git pull && bash infra/setup-mail.sh
# You type the Gmail address and its 16-letter APP PASSWORD here (hidden). They are saved only in /opt/ges/infra/.env.
# Before this: (1) in the Netcup panel (SCP) remove the "netcup Mail Block" firewall policy from this server,
#              (2) in your Google account turn on 2-step verification and make an "App password" (name: Golden Seed).
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "No infra/.env here. Run deploy.sh first."; exit 1; }
DC="docker compose -f docker-compose.prod.yml --env-file .env"

echo "=== 1/3 The mail account ==="
read -rp "Gmail address that will SEND the codes: " GMAIL </dev/tty
case "$GMAIL" in *@gmail.com) ;; *) echo "That is not a gmail.com address. Nothing was changed."; exit 1 ;; esac
read -rsp "App password (16 letters, spaces do not matter): " APPPW </dev/tty; echo
APPPW="${APPPW// /}"
[ "${#APPPW}" -eq 16 ] || { echo "An app password has 16 letters. Nothing was changed."; exit 1; }

echo "=== 2/3 Testing that this server can send mail ==="
GMAIL="$GMAIL" APPPW="$APPPW" python3 - <<'PY' || { echo "The test FAILED. Nothing was changed. Check: the Netcup mail block is removed, 2-step verification is on, the app password is right."; exit 1; }
import os, smtplib, ssl
from email.message import EmailMessage
u, p = os.environ["GMAIL"], os.environ["APPPW"]
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=20) as s:
    s.login(u, p)
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = u, u, "Golden Seed - mail test"
    m.set_content("This server can send mail. You can ignore this message.")
    s.send_message(m)
print("Test email sent to", u)
PY

echo "=== 3/3 Saving and restarting the app (data is not touched) ==="
umask 077
grep -v -E '^(MAIL_ENABLED|MAIL_FROM|MAIL_USERNAME|MAIL_PASSWORD)=' .env > .env.new || true
{ echo "MAIL_ENABLED=true"; echo "MAIL_FROM=$GMAIL"; echo "MAIL_USERNAME=$GMAIL"; echo "MAIL_PASSWORD=$APPPW"; } >> .env.new
mv .env.new .env
$DC up -d backend
echo
echo "=== DONE === Check your inbox for the test email."
echo "Next: sign in as the owner, Settings > Security > RECOVERY EMAIL, and type the email that should get the codes."
