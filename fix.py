# fix.py — fix55b: repair RecoveryNoteController line 163 type mismatch
import os, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ctrl = None
for r, d, fs in os.walk(os.path.join(ROOT, "erp-backend", "src")):
    if "RecoveryNoteController.java" in fs: ctrl = os.path.join(r, "RecoveryNoteController.java"); break
if not ctrl:
    print("ABORT: RecoveryNoteController.java not found."); sys.exit(1)
shutil.copy2(ctrl, os.path.join(ROOT, ".fix_backup", "RecoveryNoteController.java.bak55"))

with open(ctrl, "r", encoding="utf-8") as f:
    src = f.read()

old_lines = """            try {
                author = (com.gesolutions.erp.modules.auth.model.User)
                    userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (author instanceof java.util.Optional) author = ((java.util.Optional<com.gesolutions.erp.modules.auth.model.User>) author).orElse(null);
            } catch (Exception ignored) { }"""

new_lines = """            try {
                Object temp = userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (temp instanceof java.util.Optional) {
                    author = ((java.util.Optional<com.gesolutions.erp.modules.auth.model.User>) temp).orElse(null);
                } else {
                    author = (com.gesolutions.erp.modules.auth.model.User) temp;
                }
            } catch (Exception ignored) { }"""

if old_lines in src:
    src = src.replace(old_lines, new_lines, 1)
    with open(ctrl, "w", encoding="utf-8") as f:
        f.write(src)
    print("✓ Line 163 fixed: proper Optional handling with temp variable")
else:
    print("Pattern not found — may already be fixed")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix55b: repair RecoveryNoteController line 163 type mismatch"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("✓ Pushed to main")
except Exception as e:
    print("GIT WARN:", e)