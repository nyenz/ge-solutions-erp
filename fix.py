import subprocess
import pathlib

DRY_RUN = True  # True = change nothing

MSG = 'fix85: catalogue repaired (matched keys, ALL scopes, ~45 reports) + DEFAULT VIEW pin row'

FIXES = [
    # ("path/to/file.jsx", "OLD_CODE", "NEW_CODE"),
]

print("fix.py: start")
print("DRY_RUN:", DRY_RUN)
print("fix count:", len(FIXES))

for path, old, new in FIXES:
    p = pathlib.Path(path)

    if not p.exists():
        print("missing:", path)
        continue

    txt = p.read_text(encoding="utf-8")

    if old not in txt:
        print("not found:", path)
        continue

    print("would fix:", path)

    if not DRY_RUN:
        p.write_text(txt.replace(old, new, 1), encoding="utf-8")

if DRY_RUN:
    print("fix.py: dry run only, nothing changed")
    print("git commands skipped")
else:
    print('')
    print('git: staging, committing, pushing...')
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'commit', '-m', MSG])
    subprocess.run(['git', 'push'])