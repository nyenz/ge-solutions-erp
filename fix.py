import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING (patch target not found): {path}")
        return
    write(path, content.replace(old, new, 1))

print("=== FIX: Recovery Portal Buttons ===")

patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    """                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}
                                                {isAdmin && (
                                                    <button className={styles.payBtnMonthly}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiRepeat size={12} /> INSTALMENT
                                                    </button>
                                                )}""",
    """                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#record-payment`)}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}
                                                {isAdmin && (
                                                    <button className={styles.payBtnMonthly}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#storage-fees`)}>
                                                        <FiRepeat size={12} /> INSTALMENT
                                                    </button>
                                                )}"""
)

patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    """                                                {isAdmin && (
                                                    <button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiZap size={12} /> PAY
                                                    </button>
                                                )}""",
    """                                                {isAdmin && (
                                                    <button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#record-payment`)}>
                                                        <FiZap size={12} /> PAY
                                                    </button>
                                                )}"""
)

print("\n=== FIX: FolderPage Hashes and Scrolling ===")

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    """    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-')) {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {""",
    """    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-') || hash === 'record-payment' || hash === 'storage-fees') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash === 'record-payment') {
                    if (isAdmin) setPayModal({ open: true });
                } else if (hash === 'storage-fees') {
                    const el = document.getElementById('backlog-controls');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {"""
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    """                        {/* ── 2. BACKLOG CONTROLS (admin only, shown when backlog) ── */}
                        {isAdmin && isBacklog && (
                            <section className={styles.hwPanel} aria-label="Backlog Controls">""",
    """                        {/* ── 2. BACKLOG CONTROLS (admin only, shown when backlog) ── */}
                        {isAdmin && isBacklog && (
                            <section className={styles.hwPanel} aria-label="Backlog Controls" id="backlog-controls">"""
)


print("\n=== FIX: FolderPage Sticky Headers & Spelling ===")

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    """/* Inactive state -- matches all other filter buttons in the app */
.tabBtn {""",
    """.tabShort { display: none; }

/* Inactive state -- matches all other filter buttons in the app */
.tabBtn {"""
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    """.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 4px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
}""",
    """.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 10px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: -30px;
    z-index: 100;
    background: var(--navy);
    margin-left: -30px;
    margin-right: -30px;
    padding-left: 30px;
    padding-right: 30px;
}"""
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    """.drawerHeader {
    display: flex; justify-content: space-between; align-items: center;
    width: 100% !important; cursor: pointer; user-select: none;
    padding: clamp(8px, 1.1vw, 11px) clamp(12px, 1.5vw, 17px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.12);
    transition: background 0.2s; box-sizing: border-box;
}""",
    """.drawerHeader {
    display: flex; justify-content: space-between; align-items: center;
    width: 100% !important; cursor: pointer; user-select: none;
    padding: clamp(8px, 1.1vw, 11px) clamp(12px, 1.5vw, 17px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.12);
    transition: background 0.2s; box-sizing: border-box;
    position: sticky;
    top: 24px;
    z-index: 90;
    background: var(--panel-bg);
}"""
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    """.finPanelHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 18px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.18);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
}""",
    """.finPanelHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 18px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.18);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    position: sticky;
    top: 24px;
    z-index: 90;
    background: var(--panel-bg);
}"""
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    """@media (max-width: 600px) {
    .tabFull  { display: none; }
    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }""",
    """@media (max-width: 600px) {
    .tabBar { top: -20px; margin-left: -15px; margin-right: -15px; padding-left: 15px; padding-right: 15px; }
    .drawerHeader, .finPanelHeader { top: 22px; }
    .tabFull  { display: none; }
    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }"""
)

print("\n=== ALL FIXES APPLIED SUCCESSFULLY ===")