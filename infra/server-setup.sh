#!/usr/bin/env bash
# PATH: infra/server-setup.sh
# fix269: first set-up of the Netcup server (Debian 13). Run ONCE, as root, on a fresh server:
#   curl -fsSL https://raw.githubusercontent.com/nyenz/ge-solutions-erp/main/infra/server-setup.sh | bash
# It is safe to run again. What it does:
#   1. updates the system and turns on automatic security updates
#   2. adds a small swap file (the Java build needs the room)
#   3. firewall: only SSH (22), web (80) and secure web (443) are open to the internet
#   4. fail2ban: blocks anyone who keeps guessing the SSH password
#   5. installs Docker (runs the app, the database and the web server)
# Nothing of the app is installed here; that is the next step.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then echo "Run this as root."; exit 1; fi
export DEBIAN_FRONTEND=noninteractive

say() { printf '\n=== %s ===\n' "$1"; }

say "1/5 Updating the system"
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg ufw fail2ban python3-systemd unattended-upgrades \
    apt-listchanges git cron nano htop unzip rsync

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
timedatectl set-timezone Africa/Kampala || true

say "2/5 Swap file (2 GB)"
if ! swapon --show | grep -q .; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'vm.swappiness=10' > /etc/sysctl.d/99-swap.conf
    sysctl -p /etc/sysctl.d/99-swap.conf >/dev/null
else
    echo "Swap already there."
fi

say "3/5 Firewall"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'web'
ufw allow 443/tcp comment 'secure web'
ufw --force enable
ufw status verbose

say "4/5 fail2ban (blocks password guessers)"
cat > /etc/fail2ban/jail.d/ges.conf <<'EOF'
[DEFAULT]
backend = systemd

[sshd]
enabled  = true
port     = ssh
maxretry = 5
findtime = 10m
bantime  = 1h
EOF
systemctl enable fail2ban
systemctl restart fail2ban

say "5/5 Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
docker --version
docker compose version

say "DONE"
echo "Server is updated, firewalled and ready for the app."
echo "Free memory:"; free -h
echo "Disk:";        df -h /
