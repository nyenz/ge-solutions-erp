import os

BASE = 'erp-frontend/src'

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f'OK: {label}')
    else:
        print(f'MISSING: {label}')

# ─── 1. SHELL: remove mobile padding that fights page containers ────────────────
SHELL = os.path.join(BASE, 'components/layout/Shell.module.css')

patch(SHELL,
    '@media (max-width: 768px) {\n    .scrollArea {\n        padding: 20px 15px;\n    }\n}\n\n@media (max-width: 480px) {\n    .scrollArea {\n        padding: 15px 10px;\n    }\n}',
    '@media (max-width: 768px) {\n    .scrollArea {\n        padding: 0;\n    }\n}\n\n@media (max-width: 480px) {\n    .scrollArea {\n        padding: 0;\n    }\n}',
    'Shell: remove mobile scrollArea padding'
)

# ─── 2. LEDGER: fix mobile container/table boundaries ───────────────────────────
LEDGER = os.path.join(BASE, 'pages/Ledger/LedgerPage.module.css')

patch(LEDGER,
    '@media (max-width: 768px) {\n    .searchBlock { max-width: 100%; }\n    .ownerName   { max-width: clamp(80px, 28vw, 140px); }\n    .tableScroll { margin: -20px; margin-bottom: 0; }\n    .ledgerTable { min-width: clamp(560px, 90vw, 900px); }\n    .ledgerTable th { padding: 9px 10px; font-size: 7px; }\n    .ledgerTable td { padding: 8px 10px; }\n    .pagination { padding: 8px 10px; }\n}',
    '@media (max-width: 768px) {\n    .container {\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .pageHeader {\n        margin-left: 0;\n        margin-right: 0;\n        border-radius: 0;\n    }\n    .controlHub {\n        margin-left: 0;\n        margin-right: 0;\n        padding-left: clamp(8px, 2vw, 12px);\n        padding-right: clamp(8px, 2vw, 12px);\n    }\n    .searchBlock { max-width: 100%; }\n    .ownerName   { max-width: clamp(80px, 28vw, 140px); }\n    .tableScroll { margin: 0; border-radius: 0; }\n    .ledgerTable { min-width: clamp(560px, 90vw, 900px); }\n    .ledgerTable th { padding: 9px 10px; font-size: 7px; }\n    .ledgerTable td { padding: 8px 10px; }\n    .pagination { padding: 8px 10px; border-radius: 0; }\n}',
    'Ledger: mobile container/table boundary fix'
)

patch(LEDGER,
    '@media (max-width: 480px) {\n    .jointBadge  { display: none; }\n    .pctLabel    { display: none; }\n    .tableScroll { margin: -15px; margin-bottom: 0; }\n    .ledgerTable { min-width: 480px; font-size: 10px; }\n    .plotCell strong { font-size: 10px; }\n    .ownerName { max-width: 90px; font-size: 10px; }\n    .ownerPhone { font-size: 9px; }\n    .debtAmount, .debtCritical { font-size: 10px; }\n    .boxTag { font-size: 8px; padding: 2px 5px; }\n}',
    '@media (max-width: 480px) {\n    .container {\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .jointBadge  { display: none; }\n    .pctLabel    { display: none; }\n    .tableScroll { margin: 0; border-radius: 0; }\n    .ledgerTable { min-width: 480px; font-size: 10px; }\n    .plotCell strong { font-size: 10px; }\n    .ownerName { max-width: 90px; font-size: 10px; }\n    .ownerPhone { font-size: 9px; }\n    .debtAmount, .debtCritical { font-size: 10px; }\n    .boxTag { font-size: 8px; padding: 2px 5px; }\n}',
    'Ledger: mobile 480 table boundary fix'
)

# ─── 3. PAYMENTS: fix mobile container/table boundaries ─────────────────────────
PAYMENTS = os.path.join(BASE, 'pages/Payments/PaymentsPage.module.css')

patch(PAYMENTS,
    '@media (max-width: 640px) {\n    .summaryRow { grid-template-columns: 1fr; gap: 8px; }\n    .searchWrap { max-width: 100%; }\n    .filterRow { gap: 6px; }\n    .ledgerTable { min-width: 650px; }\n}',
    '@media (max-width: 640px) {\n    .container {\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .pageHeader {\n        border-radius: 0;\n    }\n    .controls {\n        margin-left: 0;\n        margin-right: 0;\n        padding-left: clamp(8px, 2vw, 12px);\n        padding-right: clamp(8px, 2vw, 12px);\n    }\n    .summaryRow {\n        grid-template-columns: 1fr;\n        gap: 8px;\n        padding: 0 clamp(8px, 2vw, 12px);\n    }\n    .searchWrap { max-width: 100%; }\n    .filterRow { gap: 6px; }\n    .tableScroll { margin: 0; border-radius: 0; }\n    .ledgerTable { min-width: 650px; }\n}',
    'Payments: mobile container/table boundary fix'
)

patch(PAYMENTS,
    '@media (max-width: 480px) {\n    .summaryRow { grid-template-columns: 1fr 1fr; }\n    .sumCard strong { font-size: 13px; }\n    .ledgerTable { min-width: 600px; }\n    .ledgerTable th { font-size: 7px; letter-spacing: 1px; }\n    .ledgerTable td { padding: 8px; }\n    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }\n}',
    '@media (max-width: 480px) {\n    .container {\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .summaryRow {\n        grid-template-columns: 1fr 1fr;\n        padding: 0 clamp(8px, 2vw, 12px);\n    }\n    .sumCard strong { font-size: 13px; }\n    .tableScroll { margin: 0; border-radius: 0; }\n    .ledgerTable { min-width: 600px; }\n    .ledgerTable th { font-size: 7px; letter-spacing: 1px; }\n    .ledgerTable td { padding: 8px; }\n    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }\n}',
    'Payments: mobile 480 table boundary fix'
)

# ─── 4. AUDIT: fix mobile container/table boundaries ────────────────────────────
AUDIT = os.path.join(BASE, 'pages/Audit/AuditPage.module.css')

patch(AUDIT,
    '@media (max-width: 768px) {\n    .header      { flex-direction: column; align-items: flex-start; }\n    .controlHub  { gap: var(--gap-md); }\n    .filterGrid  {\n        flex-direction: row;\n        flex-wrap: wrap;\n        overflow: visible;\n        width: 100%;\n        gap: 6px;\n        padding-bottom: 6px;\n        padding-top: 4px;\n    }\n    .hwSelectWrap { flex: 1 1 120px; max-width: 100%; min-width: 110px; }\n    .resetBtn    { flex: 0 0 auto; padding: 0 10px; }\n    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }\n    .timeMark    { grid-column: 1; }\n    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }\n    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }\n    .iconChassis { display: none; }\n    .actionMeta  { align-items: flex-end; }\n}',
    '@media (max-width: 768px) {\n    .container {\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .pageHeader {\n        border-radius: 0;\n    }\n    .controlHub {\n        margin-left: 0;\n        margin-right: 0;\n        padding-left: clamp(8px, 2vw, 12px);\n        padding-right: clamp(8px, 2vw, 12px);\n        gap: var(--gap-md);\n    }\n    .timelineFrame { border-radius: 0; }\n    .header      { flex-direction: column; align-items: flex-start; }\n    .filterGrid  {\n        flex-direction: row;\n        flex-wrap: wrap;\n        overflow: visible;\n        width: 100%;\n        gap: 6px;\n        padding-bottom: 6px;\n        padding-top: 4px;\n    }\n    .hwSelectWrap { flex: 1 1 120px; max-width: 100%; min-width: 110px; }\n    .resetBtn    { flex: 0 0 auto; padding: 0 10px; }\n    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }\n    .timeMark    { grid-column: 1; }\n    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }\n    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }\n    .iconChassis { display: none; }\n    .actionMeta  { align-items: flex-end; }\n}',
    'Audit: mobile container/table boundary fix'
)

patch(AUDIT,
    '@media (max-width: 480px) {\n    .container {\n        --gap-xl:  10px;\n        --gap-lg:  7px;\n        --gap-md:  4px;\n        --fs-h1:   15px;\n        --fs-time: 10px;\n        --fs-action: 8px;\n        --fs-target: 9px;\n        --fs-btn:  8px;\n    }\n    .filterGrid  {\n        flex-direction: row;\n        flex-wrap: wrap;\n        overflow: visible;\n        gap: 5px;\n    }\n    .hwSelectWrap { flex: 1 1 110px; max-width: 100%; min-width: 100px; }\n    .resetBtn    { flex: 0 0 auto; padding: 0 10px; font-size: 8px; height: 32px; }\n    .header         { padding: 8px 11px; }\n    .diagItem       { padding: 4px 8px; gap: 4px; font-size: 7px; border-radius: 4px; height: 24px; }\n    .diagItem svg   { font-size: 8px; }\n    .searchPill     { max-width: 100%; height: 36px; }\n    .searchInput    { font-size: 12px; }\n    .resetBtn       { height: 34px; padding: 0 12px; font-size: 8px; }\n    .logMain        { padding: 8px 11px; gap: 8px; }\n    .pagination     { padding: 7px 11px; }\n    .pgBtn          { padding: 5px 10px; font-size: 8px; }\n    .rawBox         { padding: 8px; margin: 5px; }\n    .rawOutput      { font-size: 10px; }\n    .loadingPulse   { padding: 28px 0; font-size: 9px; letter-spacing: 2px; }\n    .emptySignal    { padding: 22px 0; font-size: 9px; }\n}',
    '@media (max-width: 480px) {\n    .container {\n        --gap-xl:  10px;\n        --gap-lg:  7px;\n        --gap-md:  4px;\n        --fs-h1:   15px;\n        --fs-time: 10px;\n        --fs-action: 8px;\n        --fs-target: 9px;\n        --fs-btn:  8px;\n        padding: 0 0 clamp(24px, 3vw, 36px);\n    }\n    .filterGrid  {\n        flex-direction: row;\n        flex-wrap: wrap;\n        overflow: visible;\n        gap: 5px;\n    }\n    .hwSelectWrap { flex: 1 1 110px; max-width: 100%; min-width: 100px; }\n    .resetBtn    { flex: 0 0 auto; padding: 0 10px; font-size: 8px; height: 32px; }\n    .header         { padding: 8px 11px; }\n    .diagItem       { padding: 4px 8px; gap: 4px; font-size: 7px; border-radius: 4px; height: 24px; }\n    .diagItem svg   { font-size: 8px; }\n    .searchPill     { max-width: 100%; height: 36px; }\n    .searchInput    { font-size: 12px; }\n    .logMain        { padding: 8px 11px; gap: 8px; }\n    .pagination     { padding: 7px 11px; }\n    .pgBtn          { padding: 5px 10px; font-size: 8px; }\n    .rawBox         { padding: 8px; margin: 5px; }\n    .rawOutput      { font-size: 10px; }\n    .loadingPulse   { padding: 28px 0; font-size: 9px; letter-spacing: 2px; }\n    .emptySignal    { padding: 22px 0; font-size: 9px; }\n}',
    'Audit: mobile 480 boundary fix'
)

# ─── 5. FOLDER: fix action buttons, tab sizing, ctrlZone on mobile ──────────────
FOLDER = os.path.join(BASE, 'pages/DigitalFolder/FolderPage.module.css')

patch(FOLDER,
    '@media (max-width: 960px) {\n    .pipelineHUD { flex-direction: column; align-items: stretch; }\n    .protocolReadout { border-left: none; border-top: 1px solid var(--white-10); padding-left: 0; padding-top: clamp(8px, 1.2vw, 12px); min-width: unset; display: flex; justify-content: space-between; align-items: center; text-align: left; }\n    .terminalHeader { flex-direction: column; align-items: stretch; }\n    .ctrlZone { width: 100%; }\n    .handshakeActions { width: 100%; }\n    .handshakeActions .btn { flex: 1; justify-content: center; }\n    .unlockMasterBtn { width: 100%; justify-content: center; }\n    .purgeBtn { align-self: flex-start; }\n    .intelDoubleRow { grid-template-columns: 1fr; width: 100%; }\n    .ownersGrid2 { grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); }\n    /* inputGrid3 stays 3-col at 960px — only narrows at 680px */\n}',
    '@media (max-width: 960px) {\n    .pipelineHUD { flex-direction: column; align-items: stretch; }\n    .protocolReadout { border-left: none; border-top: 1px solid var(--white-10); padding-left: 0; padding-top: clamp(8px, 1.2vw, 12px); min-width: unset; display: flex; justify-content: space-between; align-items: center; text-align: left; }\n    .terminalHeader { flex-direction: column; align-items: stretch; }\n    .ctrlZone { width: 100%; }\n    .ctrlGroup {\n        display: grid;\n        grid-template-columns: repeat(auto-fit, minmax(min(100%, 120px), 1fr));\n        gap: clamp(6px, 1vw, 8px);\n        width: 100%;\n    }\n    .handshakeActions { width: 100%; }\n    .handshakeActions .btn { flex: 1; justify-content: center; }\n    .unlockMasterBtn {\n        width: 100%;\n        justify-content: center;\n        height: clamp(44px, 5.5vw, 50px);\n    }\n    .ctrlBtnPay, .ctrlBtnBacklog {\n        height: clamp(44px, 5.5vw, 50px);\n        justify-content: center;\n        flex: 1;\n    }\n    .purgeBtn {\n        align-self: stretch;\n        height: clamp(44px, 5.5vw, 50px);\n        justify-content: center;\n    }\n    .btn {\n        height: clamp(44px, 5.5vw, 50px);\n        flex: 1;\n        justify-content: center;\n    }\n    .printBtn {\n        height: clamp(44px, 5.5vw, 50px);\n        width: clamp(44px, 5.5vw, 50px);\n    }\n    .intelDoubleRow { grid-template-columns: 1fr; width: 100%; }\n    .ownersGrid2 { grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); }\n    /* inputGrid3 stays 3-col at 960px — only narrows at 680px */\n}',
    'Folder: 960px button height and ctrlGroup grid'
)

patch(FOLDER,
    '@media (max-width: 600px) {\n    .tabBar {\n    display: flex;\n    flex-direction: row;\n    align-items: center;\n    gap: clamp(6px, 0.8vw, 10px);\n    flex-wrap: nowrap;\n    overflow-x: auto;\n    scrollbar-width: none;\n    padding-bottom: clamp(8px, 2vw, 10px);\n    padding-top: clamp(8px, 2vw, 10px);\n    margin-bottom: clamp(10px, 1.3vw, 14px);\n    position: sticky;\n    top: 0;\n    z-index: 100;\n    background: rgba(244, 242, 239, 0.95);\n    backdrop-filter: blur(12px);\n    -webkit-backdrop-filter: blur(12px);\n}\n    .drawerHeader, .finPanelHeader { top: 22px;     border-radius: 10.5px 10.5px 0 0;\n}\n    .tabFull  { display: none; }\n    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }\n    .tabBtn {\n        flex: 1;\n        min-width: 0;\n        padding: clamp(7px, 2vw, 9px) clamp(8px, 2.5vw, 14px) !important;\n        font-size: clamp(8px, 2.5vw, 10px) !important;\n        letter-spacing: 1px !important;\n        justify-content: center;\n    }\n}',
    '@media (max-width: 600px) {\n    .container {\n        padding: 0 0 clamp(40px, 5vw, 60px);\n    }\n    .tabBar {\n        display: flex;\n        flex-direction: row;\n        align-items: center;\n        gap: clamp(4px, 1.5vw, 8px);\n        flex-wrap: nowrap;\n        overflow-x: auto;\n        scrollbar-width: none;\n        padding: clamp(8px, 2vw, 10px) clamp(8px, 2vw, 12px);\n        margin-bottom: clamp(8px, 1.3vw, 12px);\n        position: sticky;\n        top: 0;\n        z-index: 100;\n        background: rgba(244, 242, 239, 0.95);\n        backdrop-filter: blur(12px);\n        -webkit-backdrop-filter: blur(12px);\n    }\n    .pipelineHUD {\n        border-radius: 0;\n    }\n    .terminalHeader {\n        border-radius: 0;\n        margin-left: 0;\n        margin-right: 0;\n    }\n    .drawerHeader, .finPanelHeader { top: 22px; border-radius: 10.5px 10.5px 0 0; }\n    .tabFull  { display: none; }\n    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }\n    .tabBtn {\n        flex: 1;\n        min-width: 44px;\n        height: clamp(42px, 11vw, 48px);\n        padding: clamp(10px, 3vw, 12px) clamp(6px, 2vw, 10px) !important;\n        font-size: clamp(9px, 2.8vw, 11px) !important;\n        font-weight: 900 !important;\n        letter-spacing: 0.5px !important;\n        justify-content: center;\n        display: flex;\n        align-items: center;\n    }\n    .ctrlGroup {\n        display: flex;\n        flex-direction: column;\n        gap: clamp(6px, 1.5vw, 8px);\n        width: 100%;\n    }\n    .unlockMasterBtn,\n    .ctrlBtnPay,\n    .ctrlBtnBacklog,\n    .purgeBtn {\n        width: 100% !important;\n        height: clamp(44px, 12vw, 50px) !important;\n        justify-content: center !important;\n        font-size: clamp(10px, 2.8vw, 12px) !important;\n    }\n    .btn {\n        width: 100% !important;\n        height: clamp(44px, 12vw, 50px) !important;\n        justify-content: center !important;\n    }\n    .printBtn {\n        width: 100% !important;\n        height: clamp(44px, 12vw, 50px) !important;\n    }\n    .hwPanel {\n        border-radius: 0;\n    }\n}',
    'Folder: 600px tab sizing, button height, container padding'
)

print('\nAll patches attempted.')