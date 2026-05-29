import os, re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# ── helpers ──────────────────────────────────────────────────────────────────

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f'OK: {label}')
    else:
        print(f'MISSING: {label}')

# ── 1. Replace the @media print block in FolderPage.module.css ───────────────

CSS_PATH = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.module.css')

OLD_PRINT = '''@media print {
    /* Hide interactive elements */
    .toastContainer, .savingOverlay, .ctrlZone, .printBtn,
    .addDocBtn, .addNoteBtn, .iconBtn, .editBadge,
    .drawerHeader .chevron, .pipelineHUD .protocolReadout { display: none !important; }

    /* Reset container */
    .container {
        padding: 0 !important;
        animation: none !important;
        color: #000 !important;
        max-width: 100% !important;
    }

    /* Pipeline HUD — compact horizontal row */
    .pipelineHUD {
        border: 1px solid #ccc !important;
        background: #f8f8f8 !important;
        box-shadow: none !important;
        padding: 8px 12px !important;
        margin-bottom: 12px !important;
        flex-wrap: nowrap !important;
    }
    .track { gap: 4px !important; }
    .stageModule { gap: 2px !important; }
    .dot {
        width: 20px !important; height: 20px !important;
        font-size: 9px !important;
        border: 1.5px solid #888 !important;
        background: #eee !important;
        color: #555 !important;
    }
    .dotActive {
        background: #1a2e30 !important;
        color: #fff !important;
        border-color: #1a2e30 !important;
    }
    .stageLabel { font-size: 7px !important; color: #666 !important; display: block !important; }

    /* Terminal header */
    .terminalHeader {
        background: #fff !important;
        border-left: 4px solid #1a2e30 !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        padding: 10px 16px !important;
        margin-bottom: 10px !important;
    }
    .idPlate h1 { color: #1a2e30 !important; font-size: 18px !important; }
    .metaTag { background: #eee !important; color: #333 !important; border: 1px solid #ccc !important; }
    .editBadge { display: none !important; }

    /* Panels — all open, white background */
    .hwPanel {
        border: 1px solid #ccc !important;
        box-shadow: none !important;
        background: #fff !important;
        margin-bottom: 12px !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    
    

    scroll-margin-top: 60px;}
    .drawerHeader {
        border-bottom: 1px solid #ddd !important;
        padding: 8px 14px !important;
        background: #f5f5f5 !important;
        border-radius: 10.5px 10.5px 0 0;
}
    .drawerTitle { color: #1a2e30 !important; font-size: 10px !important; }
    .panelBody { overflow: visible !important; }
    .bodyOpen   { max-height: none !important; }
    .bodyClosed { max-height: none !important; display: block !important; }
    .panelInner { padding: 12px 14px !important; }

    /* Read-only grid */
    .readOnlyGrid { grid-template-columns: repeat(3, 1fr) !important; gap: 8px 16px !important; }
    .specLabel { color: #666 !important; font-size: 8px !important; }
    .specValue { color: #000 !important; font-size: 12px !important; }
    .specItem { border-left: 2px solid #1a2e30 !important; }

    /* Owners */
    .ownersGrid2 { grid-template-columns: repeat(2, 1fr) !important; }
    .ownerStaticCard { background: #f9f9f9 !important; border: 1px solid #ddd !important; }
    .ownerName { color: #000 !important; font-size: 13px !important; }
    .infoRow { color: #333 !important; font-size: 11px !important; }
    .infoRow svg { color: #1a2e30 !important; }
    .phoneHighlight { color: #1a2e30 !important; }

    /* Financials */
    .statBox { background: #f5f5f5 !important; border: 1px solid #ddd !important; }
    .statBox label { color: #555 !important; font-size: 8px !important; }
    .statBox strong { color: #000 !important; font-size: 14px !important; }
    .redGlow { color: #c00 !important; text-shadow: none !important; }
    .velocityNote { background: #f0fdf4 !important; border: 1px solid #ccc !important; color: #166534 !important; }
    .moneyStatsRow { grid-template-columns: repeat(3, 1fr) !important; }

    /* Notes */
    .ruledNote { background: #fff !important; border: 1px solid #ddd !important; box-shadow: none !important; }
    .noteContent { color: #000 !important; }
    .noteTime { color: #666 !important; }
    .notebookTimeline { max-height: none !important; overflow: visible !important; }

    /* Documents */
    .compactVault { max-height: none !important; overflow: visible !important; background: #f9f9f9 !important; border: 1px solid #ddd !important; }
    .docTag { background: #f0f0f0 !important; border: 1px solid #ccc !important; }
    .docName { color: #1a2e30 !important; }

    /* Double row */
    .intelDoubleRow { grid-template-columns: 1fr 1fr !important; }

    /* Page setup */
    @page { margin: 15mm; size: A4 portrait; }
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}'''

NEW_PRINT = '''@media print {
    /* ================================================================
       GOLDEN SEED ERP — PROFESSIONAL PRINT / PDF DOSSIER
       A4 portrait, 15 mm margins, pure black-on-white.
       ================================================================ */

    /* ── GLOBAL RESET ── */
    *, *::before, *::after {
        box-shadow: none !important;
        text-shadow: none !important;
        animation: none !important;
        transition: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }

    html, body {
        background: #ffffff !important;
        color: #000000 !important;
        font-family: 'Georgia', serif !important;
        font-size: 10pt !important;
    }

    /* ── HIDE APP CHROME ── */
    /* sidebar, global header, circuit background */
    aside, nav[aria-label="System navigation"],
    header.header, /* Shell header */
    [class*="CircuitBackground"],
    [class*="circuitBg"],
    [class*="bgSvg"],
    [class*="particle"],
    [class*="wrapper"]:not(.container):not(.workstationBody) {
        display: none !important;
    }

    /* Shell layout: make main content fill page */
    [class*="shell"],
    [class*="mainWrapper"],
    [class*="mainContent"],
    [class*="scrollArea"] {
        display: block !important;
        overflow: visible !important;
        height: auto !important;
        min-height: 0 !important;
        background: #fff !important;
        backdrop-filter: none !important;
    }

    /* ── HIDE INTERACTIVE ELEMENTS ── */
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
    [class*="ctrlBtn"],
    [class*="purgeBtn"],
    [class*="unlockMaster"],
    [class*="ctrlBtnPay"],
    [class*="ctrlBtnBacklog"],
    [class*="filterBtn"],
    [class*="tabBtn"] {
        display: none !important;
    }

    /* ── PAGE SETUP ── */
    @page {
        size: A4 portrait;
        margin: 15mm 15mm 18mm 15mm;
    }

    /* ── CONTAINER ── */
    .container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        background: #fff !important;
        color: #000 !important;
        animation: none !important;
        font-family: 'Georgia', serif !important;
    }

    /* ── DOSSIER LETTERHEAD ── */
    /* Inject a printed header using the terminal header element */
    .terminalHeader {
        display: flex !important;
        justify-content: space-between !important;
        align-items: flex-start !important;
        background: #fff !important;
        border: none !important;
        border-bottom: 3px solid #1a2e30 !important;
        border-radius: 0 !important;
        padding: 0 0 10px 0 !important;
        margin-bottom: 14px !important;
        page-break-inside: avoid !important;
        width: 100% !important;
    }
    .terminalHeader::before {
        content: "GOLDEN SEED ERP \2014  ASSET DOSSIER";
        display: block !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        color: #555 !important;
        margin-bottom: 4px !important;
    }

    .idPlate {
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
    }
    .idPlate h1 {
        font-family: 'Arial Black', 'Arial', sans-serif !important;
        color: #1a2e30 !important;
        font-size: 22pt !important;
        font-weight: 900 !important;
        letter-spacing: 1px !important;
        line-height: 1 !important;
        margin: 0 !important;
    }
    .metaLine {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        align-items: center !important;
    }
    .metaTag {
        background: #e8e8e8 !important;
        color: #1a2e30 !important;
        border: 1px solid #bbb !important;
        border-radius: 3px !important;
        padding: 2px 7px !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* ── WORKSTATION BODY ── */
    .workstationBody {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
        width: 100% !important;
    }

    /* ── FORCE ALL PANELS AND TABS VISIBLE ── */
    /* Override the tab system: show ALL content regardless of active tab */
    .hwPanel {
        display: block !important;
        visibility: visible !important;
        background: #fff !important;
        border: 1.5px solid #333 !important;
        border-radius: 5px !important;
        box-shadow: none !important;
        margin-bottom: 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        overflow: visible !important;
        width: 100% !important;
    }

    /* Show panels that are hidden by the tab system */
    .financialsStack,
    [class*="financialsStack"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
    }

    /* Force ALL drawer bodies open */
    .panelBody,
    .panelBody.bodyClosed,
    .bodyClosed {
        display: block !important;
        max-height: none !important;
        height: auto !important;
        opacity: 1 !important;
        overflow: visible !important;
    }

    .bodyOpen,
    .bodyClosed {
        max-height: none !important;
        opacity: 1 !important;
        display: block !important;
        overflow: visible !important;
    }

    .panelInner {
        padding: 8px 12px !important;
    }

    /* ── DRAWER HEADER ── */
    .drawerHeader {
        background: #f0f0f0 !important;
        border-bottom: 1px solid #ccc !important;
        padding: 6px 12px !important;
        border-radius: 4px 4px 0 0 !important;
        cursor: default !important;
    }
    .drawerTitle {
        color: #1a2e30 !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 8pt !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    .drawerIcon { color: #1a2e30 !important; }
    .drawerCount {
        background: #ddd !important;
        color: #333 !important;
        border: 1px solid #bbb !important;
        border-radius: 10px !important;
        padding: 1px 6px !important;
        font-size: 7pt !important;
    }

    /* ── READ-ONLY SPEC GRID ── */
    .readOnlyGrid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px 18px !important;
    }
    .specItem {
        border-left: 2px solid #1a2e30 !important;
        padding: 3px 0 3px 8px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }
    .specLabel {
        color: #555 !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    .specValue {
        color: #000 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 10pt !important;
        font-weight: 700 !important;
        word-break: break-word !important;
    }

    /* ── FINANCIAL SECTION ── */
    .moneyStatsRow {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px !important;
    }
    .statBox {
        background: #f7f7f7 !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        padding: 8px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }
    .statBox label {
        color: #555 !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        display: block !important;
        margin-bottom: 3px !important;
    }
    .statBox strong {
        color: #000 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 12pt !important;
        font-weight: 900 !important;
        display: block !important;
    }
    .redGlow { color: #b00 !important; text-shadow: none !important; }
    .velocityNote {
        background: #f0fdf4 !important;
        border: 1px solid #aaa !important;
        border-radius: 4px !important;
        color: #166534 !important;
        padding: 6px 10px !important;
        font-size: 9pt !important;
    }
    .backlogNotice {
        background: #fff0f0 !important;
        border-left: 3px solid #b00 !important;
        padding: 6px 10px !important;
        border-radius: 0 4px 4px 0 !important;
        margin-bottom: 8px !important;
    }
    .backlogNoticeText strong { color: #b00 !important; font-size: 8pt !important; }
    .backlogNoticeText span   { color: #333 !important; font-size: 8pt !important; }
    .totalOwedBanner {
        background: #fff0f0 !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    .totalOwedBanner span { color: #b00 !important; font-size: 8pt !important; font-weight: 700 !important; }
    .totalOwedBanner strong { color: #b00 !important; font-size: 14pt !important; font-weight: 900 !important; }
    .collectionBar {
        height: 5px !important;
        background: #e0e0e0 !important;
        border-radius: 3px !important;
        overflow: hidden !important;
        margin: 8px 0 4px !important;
    }
    .collectionFill {
        height: 5px !important;
        background: #1a2e30 !important;
        border-radius: 3px !important;
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
        border: 1px solid #ddd !important;
        border-left: 3px solid #333 !important;
        border-radius: 3px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }
    .payAmount {
        font-family: 'Courier New', monospace !important;
        font-size: 11pt !important;
        font-weight: 900 !important;
        color: #000 !important;
    }
    .payType   { color: #333 !important; font-size: 8pt !important; }
    .payBy     { color: #555 !important; font-size: 8pt !important; }
    .payNotes  { color: #555 !important; font-style: italic !important; font-size: 8pt !important; }
    .payDate   { font-family: 'Courier New', monospace !important; font-size: 8pt !important; color: #333 !important; }
    .payBalance { font-size: 8pt !important; color: #555 !important; }

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
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        padding: 8px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }
    .ownerName {
        font-family: 'Arial Black', 'Arial', sans-serif !important;
        color: #000 !important;
        font-size: 12pt !important;
        font-weight: 900 !important;
        border-bottom: 1px solid #ddd !important;
        padding-bottom: 4px !important;
        margin-bottom: 5px !important;
    }
    .infoRow {
        color: #333 !important;
        font-size: 9pt !important;
        margin-bottom: 3px !important;
        display: flex !important;
        align-items: flex-start !important;
        gap: 6px !important;
    }
    .infoRow svg { color: #1a2e30 !important; flex-shrink: 0 !important; margin-top: 2px !important; }
    .phoneHighlight {
        font-family: 'Courier New', monospace !important;
        color: #1a2e30 !important;
        font-size: 11pt !important;
        font-weight: 700 !important;
    }

    /* ── NOTES ── */
    .notebookTimeline {
        max-height: none !important;
        overflow: visible !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }
    .ruledNote {
        background: #fff !important;
        border: 1px solid #ccc !important;
        border-left: 3px solid #1a2e30 !important;
        box-shadow: none !important;
        padding: 6px 10px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }
    .noteContent {
        color: #000 !important;
        font-size: 9pt !important;
        line-height: 1.5 !important;
    }
    .noteTime   { color: #555 !important; font-size: 8pt !important; }
    .noteAuthor { color: #777 !important; font-size: 8pt !important; }
    .noteMeta {
        display: flex !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #eee !important;
        padding-bottom: 3px !important;
        margin-bottom: 4px !important;
    }

    /* ── DOCUMENTS ── */
    .compactVault {
        max-height: none !important;
        overflow: visible !important;
        background: #f9f9f9 !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
        padding: 8px 10px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
    }
    .docTag {
        background: #f0f0f0 !important;
        border: 1px solid #ccc !important;
        border-radius: 3px !important;
        padding: 4px 8px !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }
    .docName {
        color: #1a2e30 !important;
        font-size: 9pt !important;
        font-weight: 700 !important;
        text-decoration: none !important;
    }
    .docIcon { color: #1a2e30 !important; }

    /* ── BACKLOG MANAGEMENT SECTION ── */
    .readOnlyGrid .specItem { page-break-inside: avoid !important; break-inside: avoid !important; }

    /* ── PRINT FOOTER (page numbers via CSS) ── */
    @page {
        @bottom-center {
            content: "GOLDEN SEED ERP  |  Page " counter(page) " of " counter(pages);
            font-family: Arial, sans-serif;
            font-size: 7pt;
            color: #888;
        }
    }

    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}'''

patch(CSS_PATH, OLD_PRINT, NEW_PRINT, 'FolderPage.module.css @media print block replaced')

# ── 2. Add a print-only dossier heading above the terminal header in JSX ────

JSX_PATH = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx')

OLD_JSX = '''            {/* PIPELINE HUD */}
            <nav className={styles.pipelineHUD} aria-label="Project pipeline">'''

NEW_JSX = '''            {/* PRINT-ONLY DOSSIER HEADER */}
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
            </div>

            {/* PIPELINE HUD */}
            <nav className={styles.pipelineHUD} aria-label="Project pipeline">'''

patch(JSX_PATH, OLD_JSX, NEW_JSX, 'FolderPage.jsx print dossier header injected')

# ── 3. Add CSS classes for the print-only header and force all tabs visible ──

CSS_APPEND = '''

/* ── PRINT-ONLY DOSSIER HEADER ─────────────────────────────────────────────
   Hidden on screen, rendered at the very top of the printed page.
   ─────────────────────────────────────────────────────────────────────────── */
.printDossierHeader {
    display: none; /* hidden on screen */
}

@media print {
    .printDossierHeader {
        display: block !important;
        border-bottom: 3px solid #1a2e30 !important;
        padding-bottom: 10px !important;
        margin-bottom: 14px !important;
        page-break-inside: avoid !important;
    }
    .printDossierLogo {
        font-family: Arial, sans-serif !important;
        font-size: 7pt !important;
        font-weight: 700 !important;
        letter-spacing: 4px !important;
        text-transform: uppercase !important;
        color: #888 !important;
        margin-bottom: 3px !important;
    }
    .printDossierTitle {
        font-family: 'Arial Black', Arial, sans-serif !important;
        font-size: 22pt !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        color: #1a2e30 !important;
        text-transform: uppercase !important;
        margin-bottom: 6px !important;
        line-height: 1 !important;
    }
    .printDossierMeta {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 4px 20px !important;
        font-family: Arial, sans-serif !important;
        font-size: 8pt !important;
        color: #333 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Force ALL tab panels to be visible (override JS-driven tab switching) */
    [role="tabpanel"] > *,
    .workstationBody > * {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* Hide the empty-state "no docs" / "no notes" blocks when printing */
    .emptyState { display: none !important; }

    /* Tighter inline-double-row for print */
    .intelDoubleRow {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 10px !important;
    }

    /* Remove glow from payment type colours */
    .paymentRow[style] { border-left-color: #333 !important; }
}
'''

css_content = read(CSS_PATH)
if '.printDossierHeader' not in css_content:
    css_content += CSS_APPEND
    write(CSS_PATH, css_content)
    print('OK: Appended print-only dossier header CSS classes')
else:
    print('OK: Print dossier CSS classes already present, skipping append')

print('\nAll patches applied. Run: git add -A && git commit -m "print: professional A4 dossier layout" && git push')