# fix.py -- fix65: line-based removal of the two remaining duplicate blocks
import re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)

# ---------- LandProject.java : dedupe `private boolean problem` ----------
lp = BE / "modules" / "land" / "model" / "LandProject.java"
lines = read(lp).split("\n")
idxs = [i for i, l in enumerate(lines) if re.search(r"\bprivate\s+boolean\s+problem\b", l)]
print("LandProject 'problem' declarations found:", len(idxs))
if len(idxs) > 1:
    rm = set()
    for i in idxs[1:]:                      # keep FIRST, delete the rest
        rm.add(i)                           # the declaration line
        j = i - 1
        while j >= 0 and lines[j].strip().startswith("@"):
            rm.add(j); j -= 1               # its @Builder.Default / @Column annotations
        if j >= 0 and lines[j].strip() == "":
            rm.add(j)                       # blank line above
    lines = [l for i, l in enumerate(lines) if i not in rm]
    write(lp, "\n".join(lines))
    print("OK  LandProject ->", sum(1 for l in lines if re.search(r"\bprivate\s+boolean\s+problem\b", l)), "copy")

# ---------- FolderPortalController.java : dedupe toggleProblem ----------
fpc = BE / "modules" / "land" / "controller" / "FolderPortalController.java"
lines = read(fpc).split("\n")
sigs = [i for i, l in enumerate(lines) if "public Map<String, Object> toggleProblem(" in l]
print("toggleProblem signatures found:", len(sigs))
if len(sigs) > 1:
    rm = set()
    for si in sigs[1:]:                     # keep FIRST, delete the rest
        start = si
        j = si - 1
        while j >= 0 and lines[j].strip().startswith("@"):
            start = j; j -= 1               # @PostMapping/@PreAuthorize/@Transactional
        depth = 0; started = False; k = si  # brace-balance to the closing }
        while k < len(lines):
            depth += lines[k].count("{") - lines[k].count("}")
            if "{" in lines[k]: started = True
            if started and depth == 0: break
            k += 1
        rm.update(range(start, min(k + 1, len(lines))))
        if k + 1 < len(lines) and lines[k+1].strip() == "": rm.add(k+1)
    lines = [l for i, l in enumerate(lines) if i not in rm]
    write(fpc, "\n".join(lines))
    print("OK  toggleProblem ->", sum(1 for l in lines if "public Map<String, Object> toggleProblem(" in l), "copy")

# ---------- git ----------
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix65: remove duplicate problem field + toggleProblem method"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE - both counts must read 1; the 12 problems then collapse to 0.")