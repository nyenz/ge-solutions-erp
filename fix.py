import os

files = {}

# ── FIX 1: Add missing CSS classes to LedgerPage.module.css
# rowBacklog and tagBacklog are used in LedgerPage.jsx but were missing from the CSS.
# We add them by appending to the existing file.

ledger_css_addition = """

/* ── BACKLOG ROW ────────────────────────────────────────────────── */
/* Applied to table rows where the plot is in backlog status */
.rowBacklog {
    background: rgba(239, 68, 68, 0.06);
    border-left: 3px solid rgba(239, 68, 68, 0.5) !important;
}
.rowBacklog:hover {
    background: rgba(239, 68, 68, 0.10) !important;
}

/* ── BACKLOG STATUS TAG ─────────────────────────────────────────── */
/* Shown in the STATUS column for backlog plots */
.tagBacklog {
    font-family: 'DM Sans', sans-serif;
    background: rgba(239, 68, 68, 0.18);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    animation: criticalPulse 1.8s ease-in-out infinite;
}
"""

css_path = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"
with open(css_path, "a", encoding="utf-8") as f:
    f.write(ledger_css_addition)
print(f"Updated: {css_path}")

print("All done.")