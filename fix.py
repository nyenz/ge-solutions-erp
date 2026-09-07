# fix.py -- fix70: resolve DataInitializer compile errors (undefined method + unused field)
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p):
    return p.read_text(encoding="utf-8", errors="replace")

def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print("WROTE", p.name)

res = []

# ─── 1. DataInitializer.java ────────────────────────────────────────────────
di = BE / "config" / "DataInitializer.java"
s = read(di)

# Remove NotificationService import if present
if "import com.gesolutions.erp.modules.notification.service.NotificationService;\n" in s:
    s = s.replace("import com.gesolutions.erp.modules.notification.service.NotificationService;\n", "")
    res.append("OK removed NotificationService import")

# Remove the unused notificationService field
# Matches: private final NotificationService notificationService;
# or:      private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;
old_field_pattern = r'[ \t]*private final [a-zA-Z0-9_.]*NotificationService notificationService;\n'
if re.search(old_field_pattern, s):
    s = re.sub(old_field_pattern, '', s)
    res.append("OK removed notificationService field")
else:
    res.append("MISS notificationService field")

# Remove the seedNotificationsIfEmpty(); call from run()
if "seedNotificationsIfEmpty();" in s:
    s = s.replace("seedNotificationsIfEmpty();\n", "")
    s = s.replace("seedNotificationsIfEmpty();", "")
    res.append("OK removed seedNotificationsIfEmpty() call")
else:
    res.append("MISS seedNotificationsIfEmpty() call")

# Remove any broken stub of the method itself if it exists
s = re.sub(r'\s*public void seedNotificationsIfEmpty\(\)[^{]*\{[^}]*\}\n', '\n', s)

write(di, s)

for r in res:
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix70: resolve DataInitializer compile errors (undefined method + unused field)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")