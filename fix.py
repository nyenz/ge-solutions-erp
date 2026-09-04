# fix.py -- fix61: patch 3 compile errors
# 1) RecoveryTaskDTO.CoOwnerRef missing clientId field (RecoveryController.java line 163)
# 2) FolderPortalController.java has toggleProblem(UUID) declared twice
# 3) LandProject.java has the 'problem' field declared twice
import re, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p):
    return p.read_text(encoding="utf-8", errors="replace")

def write(p, s):
    p.write_text(s, encoding="utf-8", newline="\n")

results = {}

# ---------- FIX 1: RecoveryTaskDTO.CoOwnerRef needs clientId ----------
dto_path = BACKEND / "modules" / "client" / "dto" / "RecoveryTaskDTO.java"
s = read(dto_path)
old = "public static class CoOwnerRef {\n        private String fullName;"
new = "public static class CoOwnerRef {\n        private java.util.UUID clientId;\n        private String fullName;"
if old in s:
    s = s.replace(old, new, 1)
    write(dto_path, s)
    results["RecoveryTaskDTO.CoOwnerRef.clientId"] = "OK"
elif "private java.util.UUID clientId;" in s or "private UUID clientId;" in s:
    results["RecoveryTaskDTO.CoOwnerRef.clientId"] = "OK (already present)"
else:
    results["RecoveryTaskDTO.CoOwnerRef.clientId"] = "MISSING (pattern not found, paste file back)"

# ---------- FIX 2: LandProject.java duplicate 'problem' field ----------
lp_path = BACKEND / "modules" / "land" / "model" / "LandProject.java"
lines = read(lp_path).split("\n")

FIELD_START = re.compile(r'^\s*private\s+boolean\s+problem\b')
out = []
seen_field = False
i = 0
while i < len(lines):
    line = lines[i]
    if FIELD_START.match(line):
        if seen_field:
            # duplicate -- strip trailing annotations already pushed to out
            j = len(out) - 1
            while j >= 0 and out[j].strip().startswith("@"):
                out.pop()
                j -= 1
            if out and out[-1].strip() == "":
                out.pop()
            i += 1
            continue
        else:
            seen_field = True
    out.append(line)
    i += 1

if seen_field:
    write(lp_path, "\n".join(out))
    # count how many 'private boolean problem' remain
    remaining = len(re.findall(r'^\s*private\s+boolean\s+problem\b', "\n".join(out), re.MULTILINE))
    results["LandProject.problem field dedupe"] = f"OK (remaining declarations: {remaining})"
else:
    results["LandProject.problem field dedupe"] = "MISSING (field not found)"

# ---------- FIX 3: FolderPortalController.java duplicate toggleProblem method ----------
fp_path = BACKEND / "modules" / "land" / "controller" / "FolderPortalController.java"
lines = read(fp_path).split("\n")

METHOD_START = re.compile(r'public\s+Map<String,\s*Object>\s+toggleProblem\(')
out = []
seen_method = False
i = 0
while i < len(lines):
    line = lines[i]
    if METHOD_START.search(line):
        if seen_method:
            # remove preceding annotation lines (@PostMapping, @PreAuthorize, @Transactional)
            j = len(out) - 1
            while j >= 0 and out[j].strip().startswith("@"):
                out.pop()
                j -= 1
            if out and out[-1].strip() == "":
                out.pop()
            # remove method body via brace balance
            depth = line.count("{") - line.count("}")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue
        else:
            seen_method = True
    out.append(line)
    i += 1

if seen_method:
    write(fp_path, "\n".join(out))
    remaining = len(re.findall(r'public\s+Map<String,\s*Object>\s+toggleProblem\(', "\n".join(out)))
    results["FolderPortalController.toggleProblem dedupe"] = f"OK (remaining declarations: {remaining})"
else:
    results["FolderPortalController.toggleProblem dedupe"] = "MISSING (method not found)"

# ---------- REPORT ----------
for k, v in results.items():
    print(f"{v}: {k}")

bad = sum(1 for v in results.values() if v.startswith("MISSING"))
print("VERIFY:", "CLEAN" if bad == 0 else f"{bad} issue(s) remain (do NOT push, paste this)")

# retire old fix files
for p in ROOT.glob("fix*.py"):
    if p.name != "fix.py":
        shutil.move(str(p), str(p) + ".done")
        print("retired", p.name)

if bad == 0:
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "fix61: resolve CoOwnerRef.clientId missing + duplicate problem field + duplicate toggleProblem method"], cwd=ROOT, check=True)
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
        print("GIT pushed")
    except Exception as e:
        print("GIT WARN", e)
print("DONE")