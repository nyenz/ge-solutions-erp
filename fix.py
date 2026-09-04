# fix.py -- fix64: structural dedupe of duplicated fields/methods (line-based, anchor-free)
import re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)

DECL = re.compile(r'^\s*(?:private|protected|public)\s+[\w.<>\[\]]+\s+(\w+)\s*(?:=|;)')

def dedup_fields(src, names):
    lines = src.split('\n'); pos = {}
    for i, l in enumerate(lines):
        m = DECL.match(l)
        if m and m.group(1) in names: pos.setdefault(m.group(1), []).append(i)
    rm = set(); report = []
    for name, idxs in pos.items():
        if len(idxs) > 1:
            report.append(f"{name} x{len(idxs)} -> 1")
            for i in idxs[:-1]:                      # keep LAST (original) copy
                j = i - 1
                while j >= 0 and lines[j].strip().startswith('@'):
                    rm.add(j); j -= 1                # its annotations
                rm.add(i)
                if i + 1 < len(lines) and lines[i+1].strip() == '': rm.add(i+1)
    return '\n'.join(l for i, l in enumerate(lines) if i not in rm), report

def dedup_method(src, sig):
    lines = src.split('\n')
    sigs = [i for i, l in enumerate(lines) if sig in l]
    if len(sigs) <= 1: return src, 0
    rm = set()
    for si in sigs[1:]:                              # keep FIRST copy
        j = si - 1
        while j >= 0 and lines[j].strip().startswith('@'):
            rm.add(j); j -= 1                        # its annotations
        depth = 0; started = False; k = si
        while k < len(lines):
            depth += lines[k].count('{') - lines[k].count('}')
            if '{' in lines[k]: started = True
            if started and depth == 0: break
            k += 1
        rm.update(range(si, min(k + 1, len(lines))))
        if k + 1 < len(lines) and lines[k+1].strip() == '': rm.add(k+1)
    return '\n'.join(l for i, l in enumerate(lines) if i not in rm), len(sigs) - 1

# ---------- Client.java ----------
cp = BE / "modules" / "client" / "model" / "Client.java"
s = read(cp)
s, rep = dedup_fields(s, ["fullName","nationalId","phoneNumber","email","homeAddress",
                          "monthlyContactCount","lastContactedAt","reliabilityScore"])
for r in rep: print("OK  Client dedupe:", r)
s, n = dedup_method(s, "public boolean shouldResetMonthlyCounter()")
if n: print("OK  Client dedupe: shouldResetMonthlyCounter x", n+1, "-> 1")
write(cp, s)

# ---------- LandProject.java ----------
lp = BE / "modules" / "land" / "model" / "LandProject.java"
s = read(lp)
s, rep = dedup_fields(s, ["problem"])
for r in rep: print("OK  LandProject dedupe:", r)
write(lp, s)

# ---------- FolderPortalController.java ----------
fp = BE / "modules" / "land" / "controller" / "FolderPortalController.java"
s = read(fp)
s, n = dedup_method(s, "public Map<String, Object> toggleProblem(")
if n: print("OK  Controller dedupe: toggleProblem x", n+1, "-> 1")
s = s.replace('m.put("problem", p.isProblem());\n        m.put("problem", p.isProblem());',
              'm.put("problem", p.isProblem());')
write(fp, s)

# ---------- VERIFY single copies ----------
for p, names in [(cp, ["monthlyContactCount","lastContactedAt","reliabilityScore","fullName","phoneNumber"]),
                 (lp, ["problem"])]:
    txt = read(p)
    for nm in names:
        c = len(re.findall(r'\b' + nm + r'\s*(?:=|;)', txt))
        print(f"VERIFY {p.name}:{nm} count={c}", "OK" if c == 1 else "!! STILL DUP")
c = read(fp).count("public Map<String, Object> toggleProblem(")
print("VERIFY toggleProblem count=", c, "OK" if c == 1 else "!! STILL DUP")

# ---------- git ----------
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix64: structural dedupe of duplicated entity fields and methods"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")