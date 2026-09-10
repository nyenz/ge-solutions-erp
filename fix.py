# fix.py -- fix123: fast-fail DB waits so the backend can never hang silently on Render again
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROPS = ROOT / "erp-backend" / "src" / "main" / "resources" / "application.properties"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)

s = read(PROPS)
if 'connection-init-sql' not in s:
    s = s.rstrip("\n") + """
# fix123: time-limited database waits (stops the silent 15-minute Render hang)
# 10s to get a connection from the pool, then fail loudly instead of freezing.
spring.datasource.hikari.connection-timeout=10000
spring.datasource.hikari.initialization-fail-timeout=10000
# Any lock wait (schema update, migrations) cancels after 20s so startup
# either continues or prints the real culprit in the logs.
spring.datasource.hikari.connection-init-sql=SET lock_timeout = '20s'
"""
    write(PROPS, s)
    print("OK fast-fail DB settings added")
else:
    print("SKIP fast-fail DB settings already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix123: hikari connection timeout + lock_timeout so backend never hangs silently on Render"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")