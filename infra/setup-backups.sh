#!/usr/bin/env bash
# PATH: infra/setup-backups.sh
# fix271: turns on the nightly database copy (every night at 02:00, Uganda time) and runs one copy right now to prove it works.
set -euo pipefail
chmod +x /opt/ges/infra/nightly-backup.sh
cat > /etc/cron.d/ges-backup <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 2 * * * root /opt/ges/infra/nightly-backup.sh >> /var/log/ges-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/ges-backup
systemctl enable --now cron
bash /opt/ges/infra/nightly-backup.sh
ls -lh /opt/ges-backups
echo "=== DONE === A copy is made every night at 02:00 and the last 14 are kept."
