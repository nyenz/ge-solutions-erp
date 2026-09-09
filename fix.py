# fix.py -- fix112: restore FolderPage.jsx from backup to fix JSX mismatch build error
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BACKUP = ROOT / ".fix_backup"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)

# 1. Restore FolderPage.jsx from the known good backup
backup_file = BACKUP / "FolderPage.jsx.71"
target_file = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"

if backup_file.exists():
    content = read(backup_file)
    write(target_file, content)
    print("OK Restored FolderPage.jsx from backup")
else:
    print("MISSING backup file")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix112: restore FolderPage.jsx from backup to fix JSX mismatch build error"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")