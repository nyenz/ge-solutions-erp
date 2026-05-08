import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING: {label or path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    "    border-bottom: 2px solid var(--orange);",
    "    border-bottom: 3px solid var(--orange);\n    box-shadow: 0 3px 0 rgba(238,140,58,0.15);",
    "Ledger th - stronger orange separator"
)

print("\n=== DONE ===")
print("git add -A && git commit -m 'ledger: stronger table header separator' && git push")