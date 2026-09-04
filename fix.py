# fix.py -- FINAL: streaming dedupe of the two remaining duplicate blocks
# (adopts the proven single-pass pop-from-output approach + regex safety pass)
import re, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n")
results = {}

# ---------- LandProject.java : duplicate 'problem' field ----------
lp = BACKEND / "modules" / "land" / "model" / "LandProject.java"
lines = read(lp).split("\n")
FIELD = re.compile(r'^\s*private\s+boolean\s+problem\b')
out, seen = [], False
for line in lines:
    if FIELD.match(line):
        if seen:
            j = len(out) - 1
            while j >= 0 and out[j].strip().startswith("@"): out.pop(); j -= 1
            if out and out[-1].strip() == "": out.pop()
            continue
        seen = True
    out.append(line)
s = "\n".join(out)
# safety pass: regex-remove any 2nd+ full block, whitespace-tolerant
block = re.compile(r'(@Builder\.Default\s*@Column\(name\s*=\s*"is_problem"[^)]*\)\s*private\s+boolean\s+problem\s*=\s*false;)')
ms = list(block.finditer(s))
if len(ms) > 1:
    for m in reversed(ms[1:]): s = s[:m.start()] + s[m.end():]
write(lp, s)
results["LandProject.problem"] = "remaining=" + str(len(block.findall(s)))

# ---------- FolderPortalController.java : duplicate toggleProblem ----------
fp = BACKEND / "modules" / "land" / "controller" / "FolderPortalController.java"
lines = read(fp).split("\n")
METHOD = re.compile(r'public\s+Map<String,\s*Object>\s+toggleProblem\(')
out, seen = [], False
i = 0
while i < len(lines):
    line = lines[i]
    if METHOD.search(line):
        if seen:
            j = len(out) - 1
            while j >= 0 and out[j].strip().startswith("@"): out.pop(); j -= 1
            if out and out[-1].strip() == "": out.pop()
            depth = line.count("{") - line.count("}")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            if i < len(lines) and lines[i].strip() == "": i += 1
            continue
        seen = True
    out.append(line)
    i += 1
s = "\n".join(out)
write(fp, s)
results["FolderPortalController.toggleProblem"] = "remaining=" + str(len(METHOD.findall(s)))

# ---------- report + verify ----------
bad = 0
for k, v in results.items():
    print(v, ":", k)
    if not v.endswith("remaining=1"): bad += 1
print("VERIFY:", "CLEAN" if bad == 0 else f"{bad} issue(s) remain (do NOT push, paste this)")

for p in ROOT.glob("fix*.py"):
    if p.name != "fix.py":
        shutil.move(str(p), str(p) + ".done"); print("retired", p.name)

if bad == 0:
    try:
        subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
        subprocess.run(["git","commit","-m","FINAL: dedupe problem field + toggleProblem method"],cwd=ROOT,check=True)
        subprocess.run(["git","push"],cwd=ROOT,check=True)
        print("GIT pushed")
    except Exception as e:
        print("GIT WARN", e)
print("DONE")