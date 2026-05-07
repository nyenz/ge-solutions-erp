import os

def patch(path, old, new, label):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING (not found): {label}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label}")

# ==============================================================
# FIX 1: LedgerPage.module.css
# Replace old .plotCell span (orange bg) with tenureTag + districtTag
# ==============================================================
print("=== FIX 1: LedgerPage CSS - plotCell tags ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """/* Plot cell \u2014 two-line layout to avoid cramping */
.plotCell strong {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-value);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.5px;
    white-space: normal;
    word-break: break-all;
    line-height: 1.3;
}
/* Tenure on its own line \u2014 orange tag */
.plotCell span {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: #1a2e30;
    background: var(--orange);
    padding: 1px 6px;
    border-radius: 3px;
    text-transform: uppercase;
    width: fit-content;
}""",
    """/* Plot cell -- clean two-line layout */
.plotCell strong {
    display: block;
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-value);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.5px;
    white-space: normal;
    word-break: break-word;
    line-height: 1.3;
    margin-bottom: 3px;
}
/* Tenure -- muted pill, no orange bg */
.tenureTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: rgba(255,255,255,0.55);
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    padding: 1px 7px;
    border-radius: 3px;
    text-transform: uppercase;
    margin-right: 4px;
}
/* District tag */
.districtTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 800;
    color: rgba(238,140,58,0.85);
    padding: 0;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}""",
    "LedgerPage CSS - plotCell: replace orange span with tenureTag + districtTag"
)

# ==============================================================
# FIX 2: LedgerPage.jsx - remove the search hint <p> tag
# ==============================================================
print("\n=== FIX 2: LedgerPage JSX - remove search hint <p> tag ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                        {searchTerm && (
                            <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')}
                                aria-label="Clear search" type="button">
                                <FiX aria-hidden="true" />
                            </button>
                        )}
                    </div>
                    <p id="ledger-search-hint" className={styles.searchHint}>{SEARCH_HINT}</p>
                </div>""",
    """                        {searchTerm && (
                            <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')}
                                aria-label="Clear search" type="button">
                                <FiX aria-hidden="true" />
                            </button>
                        )}
                    </div>
                </div>""",
    "LedgerPage JSX - remove search hint <p> tag"
)

# ==============================================================
# FIX 3: LedgerPage.jsx - remove SEARCH_HINT const + update input
# ==============================================================
print("\n=== FIX 3: LedgerPage JSX - update search input ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                        <input
                            type="search" id="ledger-search"
                            placeholder="Search by plot, name, phone, NIN, box, district..."
                            className={styles.searchInput}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            aria-label="Search ledger records"
                            aria-describedby="ledger-search-hint"
                            autoComplete="off"
                        />""",
    """                        <input
                            type="search" id="ledger-search"
                            placeholder="Plot ID, box, owner, phone, NIN, email, district, county, tenure..."
                            className={styles.searchInput}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            aria-label="Search ledger records"
                            autoComplete="off"
                        />""",
    "LedgerPage JSX - remove aria-describedby, update placeholder"
)

print("\n=== ALL DONE ===")
print("Steps:")
print("1. py fix.py -- check all say OK")
print("2. git add -A && git commit -m 'ledger plotCell tags, remove search hint' && git push")
print("3. Wait Render green tick, test site")