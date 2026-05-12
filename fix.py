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

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    write(path, content.replace(old, new, 1))
    print(f"OK patch ({label or path})")


# ================================================================
# STAGE 3 (or Stage 1 of the new visual/interaction requirements)
# OVERVIEW:
# 1. Parse #financials hash to set default tab
# 2. Add mobile truncation markup for tab names
# 3. Add CSS for sticky tab bar (dark navy) and Cinzel section headers
# ================================================================

# ── PATCH 1: Update useState to read hash for default tab ──
OLD_STATE = "const [activeTab, setActiveTab] = useState('OVERVIEW');"

NEW_STATE = """const [activeTab, setActiveTab] = useState(() => {
    return typeof window !== 'undefined' && window.location.hash.toLowerCase().includes('financials') 
        ? 'FINANCIALS' 
        : 'OVERVIEW';
});"""

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    OLD_STATE,
    NEW_STATE,
    'FolderPage Stage 3 - hash navigation'
)


# ── PATCH 2: Add full/short text spans for mobile tab labels ──
OLD_TABS = """            {/* TAB BAR */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </div>"""

NEW_TABS = """            {/* TAB BAR */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                        title={tab}
                    >
                        <span className={styles.tabFull}>{tab}</span>
                        <span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                    </button>
                ))}
            </div>"""

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    OLD_TABS,
    NEW_TABS,
    'FolderPage Stage 3 - responsive tab markup'
)


# ── PATCH 3: Append sticky styling and Cinzel fonts to CSS ──
# We hook into the print media query at the bottom to inject the new rules cleanly.
OLD_PRINT = """/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */
@media print {"""

NEW_PRINT = """/* ═══════════════════════════════════════════════════════════════════
   STAGE 3: VISUAL & INTERACTION REFINEMENTS
   ═══════════════════════════════════════════════════════════════════ */

/* Sticky Tab Bar with Dark Navy Panel Style */
.tabBar {
    position: sticky !important;
    top: 0 !important;
    z-index: 50 !important;
    background: rgba(22, 42, 44, 0.98) !important; /* Matches terminal header */
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: clamp(10px, 1.5vw, 16px) !important;
    backdrop-filter: blur(12px);
    margin: 0 !important;
}

/* Mobile Tab Label Truncation */
.tabShort { display: none; }

@media (max-width: 600px) {
    .tabFull { display: none; }
    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }
    .tabBtn { 
        padding: 8px 14px !important; 
        min-width: unset !important;
        flex: 1;
    }
}

/* Upgrade Section Headers to Cinzel Serif */
.finPanelHeader {
    font-family: 'Cinzel', serif !important;
    font-size: clamp(12px, 1.2vw, 16px) !important;
    letter-spacing: 1.5px !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */
@media print {"""

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    OLD_PRINT,
    NEW_PRINT,
    'FolderPage.module.css Stage 3 visual updates'
)

print()
print("Stage 1 of UI/Interaction details complete.")
print("Run: py fix.py")