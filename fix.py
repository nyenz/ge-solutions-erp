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

# =================================================================
# UNIFY PAYMENTS PAGE NAMING
# =================================================================
patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.jsx",
    "className={`${styles.searchInput} ${searchTerm ? styles.searchInputTyping : ''}`}",
    "className={`${styles.searchInput} ${searchTerm ? styles.searchInputActive : ''}`}",
    "PaymentsPage.jsx - Rename to searchInputActive"
)

patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    """.searchInputTyping {
    padding-left: 12px !important;
}""",
    """.searchInputActive {
    padding-left: 12px;
}""",
    "PaymentsPage.module.css - Rename to searchInputActive"
)

print("\n=== PAYMENTS PAGE UNIFIED ===")