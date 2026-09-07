# fix.py -- fix77: resolve missing seedNotificationsIfEmpty method compilation error
import subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

di = BE / "config" / "DataInitializer.java"
s = di.read_text(encoding="utf-8", errors="replace")

# If the method definition is missing, remove the call from run()
if "public void seedNotificationsIfEmpty()" not in s and "seedNotificationsIfEmpty()" in s:
    s = re.sub(r'[ \t]*seedNotificationsIfEmpty\(\);[ \t]*\r?\n', '', s)
    di.write_text(s, encoding="utf-8", newline="\n")
    print("OK removed orphaned seedNotificationsIfEmpty() call")
else:
    print("SKIP call already removed or method exists")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix77: resolve missing seedNotificationsIfEmpty compilation error"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")