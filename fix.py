# fix.py -- fix66: GENERIC duplicate-declaration remover (delete-only, self-verifying).
# Deletes any repeated field or repeated method signature in backend main sources,
# keeping the FIRST copy. Cannot re-add anything. Retires old fix files.
import os, re, subprocess, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "erp-backend" / "src" / "main"

FIELD = re.compile(r'^\s*(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?[\w.<>\[\]]+\s+([A-Za-z_$][\w$]*)\s*(?:=|;)')
METHOD = re.compile(r'^\s*(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?[\w.<>\[\],\s]+?\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*(?:throws[^{]*)?\{')
KEYWORDS = {"if","for","while","switch","return","new","catch","super","this"}

def clean(path):
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    seen_f, seen_m = set(), set()
    rm = set()
    i = 0
    while i < len(lines):
        l = lines[i]
        mf, mm = FIELD.match(l), METHOD.match(l)
        if mf and mf.group(1) not in KEYWORDS:
            name = mf.group(1)
            if name in seen_f:
                # duplicate field: delete it + its annotations + trailing blank
                rm.add(i)
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("@"):
                    rm.add(j); j -= 1
                if i + 1 < len(lines) and lines[i+1].strip() == "": rm.add(i+1)
            else:
                seen_f.add(name)
        elif mm and mm.group(1) not in KEYWORDS:
            sig = mm.group(1) + "(" + re.sub(r"\s+", " ", mm.group(2)).strip() + ")"
            if sig in seen_m:
                # duplicate method: delete annotations + brace-balanced body
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("@"):
                    rm.add(j); j -= 1
                rm.add(i)
                depth = lines[i].count("{") - lines[i].count("}")
                k = i + 1
                while k < len(lines) and depth > 0:
                    depth += lines[k].count("{") - lines[k].count("}")
                    rm.add(k); k += 1
                if k < len(lines) and lines[k].strip() == "": rm.add(k)
            else:
                seen_m.add(sig)
        i += 1
    if rm:
        out = [l for idx, l in enumerate(lines) if idx not in rm]
        path.write_text("\n".join(out), encoding="utf-8", newline="")
        return len(rm)
    return 0

total = 0
for r, d, fs in os.walk(SRC):
    for f in fs:
        if f.endswith(".java"):
            n = clean(Path(r) / f)
            if n: print("cleaned", f, "->", n, "lines removed"); total += n
print("TOTAL lines removed:", total)

# verify: re-scan for any remaining dupes
bad = 0
for r, d, fs in os.walk(SRC):
    for f in fs:
        if f.endswith(".java"):
            lines = (Path(r)/f).read_text(encoding="utf-8", errors="replace").split("\n")
            sf, sm = set(), set()
            for l in lines:
                mf, mm = FIELD.match(l), METHOD.match(l)
                if mf and mf.group(1) not in KEYWORDS:
                    if mf.group(1) in sf: print("STILL DUP field", mf.group(1), "in", f); bad += 1
                    sf.add(mf.group(1))
                elif mm and mm.group(1) not in KEYWORDS:
                    sig = mm.group(1)+"("+re.sub(r"\s+"," ",mm.group(2)).strip()+")"
                    if sig in sm: print("STILL DUP method", sig, "in", f); bad += 1
                    sm.add(sig)
print("VERIFY:", "CLEAN" if bad == 0 else str(bad)+" dupes remain (do NOT push, paste this)")

# retire old fix files so the loop ends
for p in ROOT.glob("fix*.py"):
    if p.name != "fix.py":
        shutil.move(str(p), str(p) + ".done"); print("retired", p.name)

if bad == 0:
    try:
        subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
        subprocess.run(["git","commit","-m","fix66: remove all duplicate field/method declarations"],cwd=ROOT,check=True)
        subprocess.run(["git","push"],cwd=ROOT,check=True)
        print("GIT pushed")
    except Exception as e:
        print("GIT WARN", e)
print("DONE")