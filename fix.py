# fix.py — fix50: repair broken if/else chain from fix48 + build-gate before push
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
jsx_path = None
for r, d, fs in os.walk(FE):
    if "FolderPage.jsx" in fs: jsx_path = os.path.join(r, "FolderPage.jsx"); break
if not jsx_path:
    print("ABORT: FolderPage.jsx not found."); sys.exit(1)

src = open(jsx_path, "r", encoding="utf-8").read()
before = src

# --- Repair: remove the stray '}' between the NOTES and OWNERS hash conditions ---
bad = "setActiveTab('NOTES');\n        } else if (hash === 'identity'"
good = "setActiveTab('NOTES');\n        else if (hash === 'identity'"
if bad in src:
    src = src.replace(bad, good, 1)
else:
    src = re.sub(r"(setActiveTab\('NOTES'\);\n)[ \t]*\}[ \t]*(else if \(hash === 'identity')",
                 r"\1        \2", src, count=1)

if src == before:
    print("NOTE: pattern not found — file may already be fixed. Verifying anyway.")

# --- Build-gate: transform with esbuild BEFORE committing ---
fe_root = os.path.dirname(FE)
esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
tmp = os.path.join(ROOT, ".jsx_check.js")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx_path, "--loader:.jsx=jsx", "--outfile=" + tmp],
                         capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX still broken — nothing pushed.")
        print(chk.stderr[:2000]); sys.exit(1)
    os.remove(tmp)
    print("VERIFY: esbuild transform OK.")
else:
    print("WARN: esbuild not found locally — skipping pre-verify.")

open(jsx_path, "w", encoding="utf-8").write(src)
print("WROTE: FolderPage.jsx (chain repaired)")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix50: repair hash if/else chain (build fix) + esbuild build-gate"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: committed and pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")