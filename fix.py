import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        return True
    else:
        print(f"MISSING in {path}: snippet not matched")
        return False

# ================================================================
# FIX: Remove COMPLETED filter from LedgerPage (conflicts with PAID TITLES)
# PAID TITLES = fully paid (amountPaid >= totalCost) OR released
# COMPLETED was doing the same thing -- remove it
# ================================================================

LEDGER = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

patch(
    LEDGER,
    """    const FILTERS = [
        { key: 'ALL',       label: 'ALL ARCHIVES' },
        { key: 'PAID',      label: 'PAID TITLES'  },
        { key: 'COMPLETED', label: 'COMPLETED'     },
        { key: 'BACKLOG',   label: 'BACKLOG'       },
        { key: 'DEBTORS',   label: 'UNPAID'        },
        { key: 'CRITICAL',  label: 'CRITICAL'      },
    ];""",
    """    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES' },
        { key: 'PAID',     label: 'PAID TITLES'  },
        { key: 'BACKLOG',  label: 'BACKLOG'       },
        { key: 'DEBTORS',  label: 'UNPAID'        },
        { key: 'CRITICAL', label: 'CRITICAL'      },
    ];"""
)

patch(
    LEDGER,
    """        if (activeFilter === 'PAID')      filtered = filtered.filter(p => p.amountPaid >= p.totalCost || p.landTitle?.isReleased);
        if (activeFilter === 'COMPLETED') filtered = filtered.filter(p => p.landTitle?.isReleased || (p.amountPaid >= p.totalCost && !p.isBacklog));
        if (activeFilter === 'BACKLOG')   filtered = filtered.filter(p => p.isBacklog);""",
    """        if (activeFilter === 'PAID')    filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isBacklog);
        if (activeFilter === 'BACKLOG') filtered = filtered.filter(p => p.isBacklog);"""
)

# ================================================================
# FIX: Remove COMPLETED from PaymentsPage filter
# ================================================================

PAYMENTS = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'

patch(
    PAYMENTS,
    "        {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL', 'COMPLETED'].map(t => (\n                        <button key={t}\n                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}\n                            onClick={() => setTypeFilter(t)}>\n                            {t === 'ALL' ? 'ALL TYPES' : t === 'COMPLETED' ? 'COMPLETED PLOTS' : TYPE_LABELS[t]}\n                        </button>\n                    ))}",
    "        {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL'].map(t => (\n                        <button key={t}\n                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}\n                            onClick={() => setTypeFilter(t)}>\n                            {t === 'ALL' ? 'ALL TYPES' : TYPE_LABELS[t]}\n                        </button>\n                    ))}"
)

patch(
    PAYMENTS,
    "        if (typeFilter === 'COMPLETED') list = list.filter(p => p.balanceAfter !== null && p.balanceAfter !== undefined && Number(p.balanceAfter) <= 0);\n        else if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);",
    "        if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);"
)

print("Done!")
print("Changes:")
print("  1. LedgerPage: removed COMPLETED filter (was duplicate of PAID TITLES)")
print("  2. LedgerPage: PAID TITLES now = fully paid OR released, excluding backlog")
print("  3. PaymentsPage: removed COMPLETED PLOTS filter")
print("")
print("Run: git add -A && git commit -m 'fix: remove duplicate COMPLETED filter, PAID TITLES is the single source' && git push")