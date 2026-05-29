import os, sys

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old in content:
        write_file(path, content.replace(old, new, 1))
        print(f'OK: {label}')
    else:
        print(f'MISSING: {label}')

BASE = os.path.dirname(os.path.abspath(__file__))
FOLDER_JSX = os.path.join(BASE, 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx')
FOLDER_CSS = os.path.join(BASE, 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css')
INDEX_CSS  = os.path.join(BASE, 'erp-frontend/src/index.css')

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1: FolderPage.jsx — replace tab-conditional rendering with always-render
# We replace the <main> block that has {activeTab === 'X' && <section>} wrappers
# ─────────────────────────────────────────────────────────────────────────────

OLD_MAIN_OPEN = '''            <main className={styles.workstationBody} role="tabpanel">

                {/* ════════════════════════════════════════════════════
                    OVERVIEW TAB — Plot technical details
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'OVERVIEW' && (
                    <section className={styles.hwPanel} aria-label="Plot Details">'''

NEW_MAIN_OPEN = '''            <main className={styles.workstationBody} role="tabpanel">

                {/* ════════════════════════════════════════════════════
                    OVERVIEW TAB — Plot technical details
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Plot Details"
                    style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}
                    data-print-section="OVERVIEW"
                >'''

patch(FOLDER_JSX, OLD_MAIN_OPEN, NEW_MAIN_OPEN, 'JSX: overview tab open')

# Close of overview section — was `)}` after the section
OLD_OVERVIEW_CLOSE = '''                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    FINANCIALS TAB — Central hub:'''

NEW_OVERVIEW_CLOSE = '''                </section>

                {/* ════════════════════════════════════════════════════
                    FINANCIALS TAB — Central hub:'''

patch(FOLDER_JSX, OLD_OVERVIEW_CLOSE, NEW_OVERVIEW_CLOSE, 'JSX: overview tab close')

# Financials tab open
OLD_FIN_OPEN = '''                {activeTab === 'FINANCIALS' && (
                    <div className={styles.financialsStack}>'''

NEW_FIN_OPEN = '''                <div
                    className={styles.financialsStack}
                    style={activeTab !== 'FINANCIALS' ? {display:'none'} : {}}
                    data-print-section="FINANCIALS"
                >'''

patch(FOLDER_JSX, OLD_FIN_OPEN, NEW_FIN_OPEN, 'JSX: financials tab open')

# Financials tab close — ends with `)}` after the last section
OLD_FIN_CLOSE = '''                    </div>
                )}

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'OWNERS' && (
                    <section className={styles.hwPanel} aria-label="Owners">'''

NEW_FIN_CLOSE = '''                </div>

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Owners"
                    style={activeTab !== 'OWNERS' ? {display:'none'} : {}}
                    data-print-section="OWNERS"
                >'''

patch(FOLDER_JSX, OLD_FIN_CLOSE, NEW_FIN_CLOSE, 'JSX: financials close / owners open')

# Owners tab close
OLD_OWNERS_CLOSE = '''                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB — Files + upload
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'DOCUMENTS' && (
                    <section className={styles.hwPanel} aria-label="Documents">'''

NEW_OWNERS_CLOSE = '''                </section>

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB — Files + upload
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Documents"
                    style={activeTab !== 'DOCUMENTS' ? {display:'none'} : {}}
                    data-print-section="DOCUMENTS"
                >'''

patch(FOLDER_JSX, OLD_OWNERS_CLOSE, NEW_OWNERS_CLOSE, 'JSX: owners close / documents open')

# Documents tab close — the last `)}` before the file input
OLD_DOCS_CLOSE = '''                    </section>
                )}

            </main>'''

NEW_DOCS_CLOSE = '''                </section>

            </main>'''

patch(FOLDER_JSX, OLD_DOCS_CLOSE, NEW_DOCS_CLOSE, 'JSX: documents tab close')

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2: FolderPage.jsx — replace the print-only dossier header with the
#          corporate version
# ─────────────────────────────────────────────────────────────────────────────

OLD_DOSSIER_HEADER = '''            {/* PRINT-ONLY DOSSIER HEADER */}
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierLogo}>GOLDEN SEED ERP</div>
                <div className={styles.printDossierTitle}>ASSET DOSSIER</div>
                <div className={styles.printDossierMeta}>
                    <span>PLOT: {project.landTitle.plotNumber}</span>
                    <span>TENURE: {project.landTitle.tenure}</span>
                    {project.landTitle.district && <span>DISTRICT: {project.landTitle.district}</span>}
                    <span>BOX: {project.landTitle.physicalBoxNumber}</span>
                    <span>PRINTED: {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })}</span>
                </div>
            </div>'''

NEW_DOSSIER_HEADER = '''            {/* PRINT-ONLY CORPORATE DOSSIER HEADER */}
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierTopBar}>
                    <div className={styles.printDossierLeft}>
                        <div className={styles.printDossierCompany}>GE SOLUTIONS</div>
                        <div className={styles.printDossierDivision}>LAND REGISTRY DIVISION</div>
                    </div>
                    <div className={styles.printDossierCenter}>
                        <div className={styles.printDossierTitleBox}>OFFICIAL LAND DOSSIER</div>
                    </div>
                    <div className={styles.printDossierRight}>
                        <div className={styles.printDossierDateLabel}>PRINTED ON</div>
                        <div className={styles.printDossierDateVal}>
                            {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })}
                        </div>
                    </div>
                </div>
                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle.plotNumber}</span>
                    <span><strong>TENURE:</strong> {project.landTitle.tenure}</span>
                    {project.landTitle.district && <span><strong>DISTRICT:</strong> {project.landTitle.district}</span>}
                    <span><strong>BOX:</strong> {project.landTitle.physicalBoxNumber}</span>
                    <span><strong>STATUS:</strong> {project.status}</span>
                    <span><strong>STAGE:</strong> {STAGE_LABELS[(project.currentStageIndex || 1) - 1] || project.currentStageIndex}</span>
                </div>
            </div>'''

patch(FOLDER_JSX, OLD_DOSSIER_HEADER, NEW_DOSSIER_HEADER, 'JSX: corporate dossier header')

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3: FolderPage.module.css — completely replace the @media print block
# ─────────────────────────────────────────────────────────────────────────────

# We'll find the @media print block start and replace to end of file (it's the last block)
css_content = read_file(FOLDER_CSS)

PRINT_BLOCK_START = '@media print {'

# Find last occurrence of @media print {
idx = css_content.rfind(PRINT_BLOCK_START)
if idx == -1:
    print('MISSING: CSS print block not found')
else:
    # Everything before the last @media print block
    before_print = css_content[:idx]

    NEW_PRINT_CSS = r'''@media print {

    /* ================================================================
       GE SOLUTIONS — CORPORATE PRINT / PDF DOSSIER
       A4 portrait, 15mm margins, crisp black-on-white.
       ================================================================ */

    @page {
        size: A4 portrait;
        margin: 15mm 15mm 18mm 15mm;
    }

    /* ── GLOBAL RESET ── */
    *, *::before, *::after {
        box-shadow: none !important;
        text-shadow: none !important;
        animation: none !important;
        transition: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        background: #ffffff !important;
        color: #000000 !important;
    }

    /* ── CONTAINER ── */
    .container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        font-family: 'Georgia', serif !important;
        animation: none !important;
    }

    /* ── HIDE INTERACTIVE / APP CHROME ── */
    .toastContainer,
    .savingOverlay,
    .ctrlZone,
    .printBtn,
    .addDocBtn,
    .addNoteBtn,
    .iconBtn,
    .editBadge,
    .tabBar,
    .pipelineHUD,
    .chevron,
    .confirmOverlay,
    .actionBlock,
    .expandedActions,
    .recordPayBtnRow,
    .recordPayBtn,
    .backlogFeeConfig,
    .editBacklogFeeSection,
    [class*="ctrlBtn"],
    [class*="purgeBtn"],
    [class*="unlockMaster"],
    [class*="ctrlBtnPay"],
    [class*="ctrlBtnBacklog"],
    [class*="filterBtn"],
    [class*="tabBtn"] {
        display: none !important;
    }

    /* ── CORPORATE DOSSIER HEADER ── */
    .printDossierHeader {
        display: block !important;
        border-bottom: 2px solid #000000 !important;
        padding-bottom: 10px !important;
        margin-bottom: 16px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .printDossierTopBar {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 16px !important;
        margin-bottom: 8px !important;
    }

    .printDossierLeft {
        display: flex !important;
        flex-direction: column !important;
        gap: 2px !important;
    }

    .printDossierCompany {
        font-family: 'Arial Black', Arial, sans-serif !important;
        font-size: 13pt !important;
        font-weight: 900 !important;
        color: #000000 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
    }

    .printDossierDivision {
        font-family: Arial, sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        color: #555555 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
    }

    .printDossierCenter {
        flex: 1 !important;
        display: flex !important;
        justify-content: center !important;
    }

    .printDossierTitleBox {
        border: 2px solid #000000 !important;
        padding: 8px 20px !important;
        font-family: 'Arial Black', Arial, sans-serif !important;
        font-size: 14pt !important;
        font-weight: 900 !important;
        color: #000000 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        text-align: center !important;
        background: #f0f0f0 !important;
    }

    .printDossierRight {
        text-align: right !important;
    }

    .printDossierDateLabel {
        font-family: Arial, sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        color: #555555 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .printDossierDateVal {
        font-family: 'Courier New', monospace !important;
        font-size: 9pt !important;
        font-weight: 700 !important;
        color: #000000 !important;
    }

    .printDossierMeta {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 4px 20px !important;
        font-family: Arial, sans-serif !important;
        font-size: 8pt !important;
        color: #333333 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding-top: 6px !important;
        border-top: 1px solid #cccccc !important;
    }

    .printDossierMeta strong {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* ── TERMINAL HEADER — hide on print (dossier header replaces it) ── */
    .terminalHeader {
        display: none !important;
    }

    /* ── ALL TAB SECTIONS VISIBLE ON PRINT ── */
    [data-print-section] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    .financialsStack {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
    }

    /* ── SECTION LABELS ── */
    [data-print-section]::before {
        display: block !important;
        font-family: 'Arial Black', Arial, sans-serif !important;
        font-size: 9pt !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        color: #000000 !important;
        padding: 6px 0 4px 0 !important;
        border-top: 2px solid #000000 !important;
        margin-top: 16px !important;
        margin-bottom: 8px !important;
    }

    [data-print-section="OVERVIEW"]::before { content: 'SECTION A: PLOT TECHNICAL DETAILS'; }
    [data-print-section="FINANCIALS"]::before { content: 'SECTION B: FINANCIAL RECORDS'; }
    [data-print-section="OWNERS"]::before { content: 'SECTION C: REGISTERED PROPRIETORS'; }
    [data-print-section="DOCUMENTS"]::before { content: 'SECTION D: DOCUMENT VAULT'; }

    /* ── PANELS ── */
    .hwPanel {
        display: block !important;
        background: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        margin-bottom: 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        overflow: visible !important;
        width: 100% !important;
    }

    /* ── FORCE ALL DRAWERS OPEN ── */
    .panelBody,
    .bodyOpen,
    .bodyClosed {
        display: block !important;
        max-height: none !important;
        height: auto !important;
        opacity: 1 !important;
        overflow: visible !important;
    }

    .panelInner {
        padding: 8px 12px !important;
    }

    /* ── DRAWER HEADERS ── */
    .drawerHeader {
        background: #e8e8e8 !important;
        border-bottom: 1px solid #333333 !important;
        padding: 6px 12px !important;
        border-radius: 0 !important;
        cursor: default !important;
    }

    .drawerTitle {
        font-family: Arial, sans-serif !important;
        font-size: 8pt !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        color: #000000 !important;
    }

    .drawerIcon { color: #000000 !important; }

    .drawerCount {
        background: #dddddd !important;
        color: #333333 !important;
        border: 1px solid #999999 !important;
        border-radius: 10px !important;
        padding: 1px 6px !important;
        font-size: 7pt !important;
    }

    /* ── SPEC GRID ── */
    .readOnlyGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px 18px !important;
    }

    .specItem {
        border-left: 2px solid #000000 !important;
        padding: 3px 0 3px 8px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .specLabel {
        color: #555555 !important;
        font-family: Arial, sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .specValue {
        color: #000000 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 10pt !important;
        font-weight: 700 !important;
        word-break: break-word !important;
    }

    /* ── FINANCIALS ── */
    .moneyStatsRow {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px !important;
    }

    .statBox {
        background: #f7f7f7 !important;
        border: 1px solid #cccccc !important;
        border-radius: 0 !important;
        padding: 8px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .statBox label {
        color: #555555 !important;
        font-family: Arial, sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        display: block !important;
        margin-bottom: 3px !important;
    }

    .statBox strong {
        color: #000000 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 12pt !important;
        font-weight: 900 !important;
        display: block !important;
    }

    .redGlow { color: #aa0000 !important; text-shadow: none !important; }

    .backlogNotice {
        background: #fff0f0 !important;
        border-left: 3px solid #aa0000 !important;
        padding: 6px 10px !important;
        margin-bottom: 8px !important;
    }

    .backlogNoticeText strong { color: #aa0000 !important; font-size: 8pt !important; }
    .backlogNoticeText span   { color: #333333 !important; font-size: 8pt !important; }

    .totalOwedBanner {
        background: #fff0f0 !important;
        border: 1px solid #cccccc !important;
        padding: 8px 12px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }

    .totalOwedBanner span { color: #aa0000 !important; font-size: 8pt !important; font-weight: 700 !important; }
    .totalOwedBanner strong { color: #aa0000 !important; font-size: 14pt !important; font-weight: 900 !important; }

    .collectionBar {
        height: 5px !important;
        background: #e0e0e0 !important;
        border-radius: 0 !important;
        overflow: hidden !important;
        margin: 8px 0 4px !important;
    }

    .collectionFill {
        height: 5px !important;
        background: #000000 !important;
        border-radius: 0 !important;
    }

    .velocityNote {
        background: #f0fdf4 !important;
        border: 1px solid #aaaaaa !important;
        color: #166534 !important;
        padding: 6px 10px !important;
        font-size: 9pt !important;
    }

    /* ── PAYMENT HISTORY ── */
    .paymentList {
        display: flex !important;
        flex-direction: column !important;
        gap: 5px !important;
    }

    .paymentRow {
        display: flex !important;
        justify-content: space-between !important;
        align-items: flex-start !important;
        gap: 12px !important;
        padding: 6px 10px !important;
        background: #f9f9f9 !important;
        border: 1px solid #dddddd !important;
        border-left: 3px solid #333333 !important;
        border-radius: 0 !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .payAmount { font-family: 'Courier New', monospace !important; font-size: 11pt !important; font-weight: 900 !important; color: #000000 !important; }
    .payType   { color: #333333 !important; font-size: 8pt !important; }
    .payBy     { color: #555555 !important; font-size: 8pt !important; }
    .payNotes  { color: #555555 !important; font-style: italic !important; font-size: 8pt !important; }
    .payDate   { font-family: 'Courier New', monospace !important; font-size: 8pt !important; color: #333333 !important; }
    .payBalance { font-size: 8pt !important; color: #555555 !important; }

    /* ── BACKLOG MGMT SECTION ── */
    .readOnlyGrid .specItem { page-break-inside: avoid !important; break-inside: avoid !important; }

    /* ── OWNERS ── */
    .ownersScroll {
        max-height: none !important;
        overflow: visible !important;
    }

    .ownersGrid2 {
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 10px !important;
    }

    .ownerStaticCard {
        background: #f9f9f9 !important;
        border: 1px solid #cccccc !important;
        border-radius: 0 !important;
        padding: 8px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .ownerName {
        font-family: 'Arial Black', Arial, sans-serif !important;
        font-size: 11pt !important;
        font-weight: 900 !important;
        color: #000000 !important;
        border-bottom: 1px solid #dddddd !important;
        padding-bottom: 4px !important;
        margin-bottom: 5px !important;
    }

    .infoRow {
        color: #333333 !important;
        font-size: 9pt !important;
        margin-bottom: 3px !important;
        display: flex !important;
        align-items: flex-start !important;
        gap: 6px !important;
    }

    .infoRow svg { color: #000000 !important; flex-shrink: 0 !important; }
    .phoneHighlight { font-family: 'Courier New', monospace !important; color: #000000 !important; font-size: 10pt !important; font-weight: 700 !important; }

    /* ── NOTES ── */
    .notebookTimeline {
        max-height: none !important;
        overflow: visible !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }

    .ruledNote {
        background: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-left: 3px solid #000000 !important;
        box-shadow: none !important;
        padding: 6px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .noteContent { color: #000000 !important; font-size: 9pt !important; line-height: 1.5 !important; }
    .noteTime    { color: #555555 !important; font-size: 8pt !important; }
    .noteAuthor  { color: #777777 !important; font-size: 8pt !important; }

    .noteMeta {
        display: flex !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #eeeeee !important;
        padding-bottom: 3px !important;
        margin-bottom: 4px !important;
    }

    /* ── DOCUMENTS ── */
    .compactVault {
        max-height: none !important;
        overflow: visible !important;
        background: #f9f9f9 !important;
        border: 1px solid #dddddd !important;
        padding: 8px 10px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
    }

    .docTag {
        background: #f0f0f0 !important;
        border: 1px solid #cccccc !important;
        border-radius: 0 !important;
        padding: 4px 8px !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        page-break-inside: avoid !important;
    }

    .docName { color: #000000 !important; font-size: 9pt !important; font-weight: 700 !important; text-decoration: none !important; }
    .docIcon { color: #000000 !important; }

    /* ── EMPTY STATES — hide on print ── */
    .emptyState { display: none !important; }

    /* ── PRINT FOOTER ── */
    @page {
        @bottom-center {
            content: "GE SOLUTIONS — LAND REGISTRY DIVISION  |  CONFIDENTIAL  |  Page " counter(page) " of " counter(pages);
            font-family: Arial, sans-serif;
            font-size: 7pt;
            color: #888888;
        }
    }

    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}
'''

    write_file(FOLDER_CSS, before_print + NEW_PRINT_CSS)
    print('OK: CSS print block replaced with corporate dossier styles')

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 4: index.css — add global @media print at the bottom
# ─────────────────────────────────────────────────────────────────────────────

index_content = read_file(INDEX_CSS)

GLOBAL_PRINT_CSS = '''

/* ═══════════════════════════════════════════════════════════════
   GLOBAL PRINT — hide all shell/app chrome, enable full-page layout
   ═══════════════════════════════════════════════════════════════ */
@media print {

    /* Hide sidebar, global header, all app chrome */
    aside,
    nav[aria-label="System navigation"],
    [class*="sidebar"],
    [class*="Sidebar"],
    [class*="sidebarBackdrop"],
    [class*="header"],
    [class*="Header"],
    [class*="CircuitBackground"],
    [class*="circuitBg"],
    [class*="bgSvg"],
    [class*="particle"],
    [class*="logoutTrigger"],
    [class*="sidebarToggle"],
    [class*="notificationGroup"],
    [class*="toastContainer"],
    [class*="savingOverlay"] {
        display: none !important;
    }

    /* Reset shell layout to allow full-page multi-page printing */
    html,
    body {
        background: #ffffff !important;
        color: #000000 !important;
        overflow: visible !important;
        height: auto !important;
        width: 100% !important;
    }

    #root,
    [class*="shell"],
    [class*="Shell"],
    [class*="mainWrapper"],
    [class*="mainContent"],
    [class*="scrollArea"] {
        background: #ffffff !important;
        color: #000000 !important;
        overflow: visible !important;
        height: auto !important;
        min-height: 0 !important;
        position: static !important;
        display: block !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        transform: none !important;
        filter: none !important;
    }
}
'''

if '@media print' not in index_content or '/* GLOBAL PRINT' not in index_content:
    write_file(INDEX_CSS, index_content + GLOBAL_PRINT_CSS)
    print('OK: index.css global print block added')
else:
    print('OK: index.css global print block already present (skipped)')

print('\nDone. Run: git add -A && git commit -m "feat: corporate print dossier - all tabs print, shell hidden" && git push')