# fix.py — fix57: remove unused import + silence reflection cast warning
import os, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ctrl = None
for r, d, fs in os.walk(os.path.join(ROOT, "erp-backend", "src")):
    if "RecoveryNoteController.java" in fs: ctrl = os.path.join(r, "RecoveryNoteController.java"); break
if not ctrl:
    print("ABORT: RecoveryNoteController.java not found."); sys.exit(1)
shutil.copy2(ctrl, os.path.join(ROOT, ".fix_backup", "RecoveryNoteController.java.bak57"))

src = open(ctrl, "r", encoding="utf-8").read(); changed = False

# 1) Remove unused LocalTime import
if "import java.time.LocalTime;\n" in src:
    src = src.replace("import java.time.LocalTime;\n", "", 1); changed = True
    print("Removed unused import java.time.LocalTime")

# 2) Class-level @SuppressWarnings for the reflection cast
if "@SuppressWarnings" not in src and "public class RecoveryNoteController" in src:
    src = src.replace("public class RecoveryNoteController",
                      "@SuppressWarnings(\"unchecked\")\npublic class RecoveryNoteController", 1)
    changed = True
    print("Added @SuppressWarnings(\"unchecked\") at class level")

if changed:
    open(ctrl, "w", encoding="utf-8").write(src)
    print("WROTE: RecoveryNoteController.java")
else:
    print("NOTE: nothing to change.")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix57: clean RecoveryNoteController warnings (unused import, unchecked cast)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE. Remaining hint (@Autowired->constructor) is style-only; left untouched on purpose.")