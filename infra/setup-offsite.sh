#!/usr/bin/env bash
# PATH: infra/setup-offsite.sh
# fix274: nightly copy of the database and the documents to Google Drive, LOCKED (encrypted) before it leaves the server.
# Run once as root on the server:  cd /opt/ges && git pull && bash infra/setup-offsite.sh
# It asks for (1) the Google token you made on your own computer and (2) a passphrase of your choice. Both are typed
# here, hidden. The passphrase is the ONLY way to open the copies, so keep it in your password manager.
set -euo pipefail

CONF=/root/.config/rclone/rclone.conf
export RCLONE_CONFIG="$CONF"

echo "=== 1/4 Installing rclone ==="
apt-get update -y >/dev/null
apt-get install -y rclone >/dev/null
rclone version | head -1

echo
echo "=== 2/4 Google token ==="
echo "Paste the token you got on your computer (the line that starts with { and ends with }), then press Enter."
read -rs TOKEN </dev/tty; echo
case "$TOKEN" in
    *'"access_token"'*'"refresh_token"'*) ;;
    *) echo "That does not look like the token. Nothing was changed."; exit 1 ;;
esac

echo
echo "=== 3/4 Passphrase (locks every copy) ==="
echo "Choose a long passphrase (for example 4 or 5 random words). Save it in your password manager NOW."
read -rsp "Passphrase: " P1 </dev/tty; echo
read -rsp "Same passphrase again: " P2 </dev/tty; echo
[ "$P1" = "$P2" ] || { echo "The two did not match. Nothing was changed."; exit 1; }
[ "${#P1}" -ge 12 ] || { echo "Too short: use at least 12 characters. Nothing was changed."; exit 1; }
SALT=$(printf '%s' "ges-salt:$P1" | sha256sum | cut -d' ' -f1)

mkdir -p "$(dirname "$CONF")"; umask 077
{
    echo "[gdrive]"
    echo "type = drive"
    echo "scope = drive.file"
    echo "token = $TOKEN"
    echo
    echo "[gescrypt]"
    echo "type = crypt"
    echo "remote = gdrive:GES-Backup"
    echo "password = $(rclone obscure "$P1")"
    echo "password2 = $(rclone obscure "$SALT")"
} > "$CONF"
chmod 600 "$CONF"

echo
echo "=== 4/4 Test copy ==="
printf 'GES offsite test %s\n' "$(date)" | rclone rcat gescrypt:test.txt
echo "Reading it back: $(rclone cat gescrypt:test.txt)"
echo "What Google Drive can see (locked names, nobody can read them):"
rclone lsf gdrive:GES-Backup | head -3
rclone delete gescrypt:test.txt

echo "Running the first full copy now..."
bash /opt/ges/infra/nightly-backup.sh
echo
echo "=== DONE === Every night the copies go to the folder GES-Backup in your Google Drive, locked."
echo "REMEMBER: without the passphrase the copies cannot be opened. Keep it in your password manager."
