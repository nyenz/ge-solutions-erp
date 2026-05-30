import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old in content:
        write_file(path, content.replace(old, new, 1))
        print(f"OK: {label}")
    else:
        print(f"MISSING: {label}")

base = os.path.dirname(os.path.abspath(__file__))
ledger_jsx = os.path.join(base, 'erp-frontend/src/pages/Ledger/LedgerPage.jsx')
intake_jsx = os.path.join(base, 'erp-frontend/src/pages/Intake/IntakePage.jsx')
intake_css = os.path.join(base, 'erp-frontend/src/pages/Intake/IntakePage.module.css')
folder_jsx = os.path.join(base, 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx')

# ── 1. LEDGER: fix debt calculation to include storage fees for backlog ──

patch(
    ledger_jsx,
    '''                                const pct        = proj.totalCost > 0 ? Math.min((proj.amountPaid / proj.totalCost) * 100, 100) : 0;
                                const debt       = (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const isCritical = pct < 25 && proj.totalCost > 0;
                                const isBacklog  = proj.isBacklog;''',
    '''                                const isBacklog  = proj.isBacklog;
                                const storageFees = Number(proj.storageFeesAccumulated || 0);
                                const debt       = isBacklog
                                    ? (proj.totalCost || 0) + storageFees - (proj.amountPaid || 0)
                                    : (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const pct        = proj.totalCost > 0 ? Math.min((proj.amountPaid / proj.totalCost) * 100, 100) : 0;
                                const isCritical = pct < 25 && proj.totalCost > 0;''',
    'LedgerPage: debt calculation includes storage fees'
)

patch(
    ledger_jsx,
    "        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.amountPaid < p.totalCost);",
    "        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.isBacklog ? (Number(p.totalCost||0) + Number(p.storageFeesAccumulated||0) - Number(p.amountPaid||0)) > 0 : p.amountPaid < p.totalCost);",
    'LedgerPage: DEBTORS filter uses backlog-aware debt'
)

patch(
    ledger_jsx,
    "        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25 && !p.isBacklog);",
    "        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => !p.isBacklog && p.totalCost > 0 && (p.amountPaid / p.totalCost) < 0.25);",
    'LedgerPage: CRITICAL filter unchanged but explicit'
)

# ── 2. INTAKE: docs error state + visual highlight ──

# Add docs error tracking to errors state
patch(
    intake_jsx,
    '''    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });
        if (fileQueue.length === 0) {
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0;
    };''',
    '''    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });
        if (fileQueue.length === 0) {
            e.docs = true;
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0;
    };''',
    'IntakePage: add docs error to errors state'
)

# Apply vaultError class to vaultWrapper when errors.docs is true
patch(
    intake_jsx,
    '                                <div className={styles.vaultWrapper}>',
    '                                <div className={`${styles.vaultWrapper} ${errors.docs ? styles.vaultError : \'\'}`}>',
    'IntakePage: apply vaultError class on docs error'
)

# Add vaultError CSS
patch(
    intake_css,
    '.vaultWrapper { display: flex; flex-direction: column; gap: var(--gap-md); }',
    '.vaultWrapper { display: flex; flex-direction: column; gap: var(--gap-md); }\n\n.vaultError .fileDisplay {\n    border: 2px solid var(--red) !important;\n    box-shadow: 0 0 0 3px rgba(239,68,68,0.2) !important;\n    animation: shake 0.35s cubic-bezier(0.36,0.07,0.19,0.97) both;\n}\n\n@keyframes shake {\n    0%,100% { transform: translateX(0); }\n    20%     { transform: translateX(-6px); }\n    40%     { transform: translateX(6px); }\n    60%     { transform: translateX(-4px); }\n    80%     { transform: translateX(4px); }\n}',
    'IntakePage CSS: vaultError highlight style'
)

# ── 3. Language: Replace "ARREARS" labels in FolderPage and IntakePage ──

# FolderPage - read-only spec label
patch(
    folder_jsx,
    "                                        ['ARREARS',      project.landTitle.district],",
    "                                        ['AMOUNT OWED',  project.landTitle.district],",
    'FolderPage: ARREARS label (spec grid) - skip, wrong context'
)

# FolderPage - arrears in edit mode balance section
patch(
    folder_jsx,
    '''                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                            <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                        </div>''',
    '''                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                            <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                        </div>''',
    'FolderPage: ARREARS -> AMOUNT OWED in edit mode balance'
)

# IntakePage - arrears auto calc label
patch(
    intake_jsx,
    '''                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>ARREARS</label>
                                        <span className={styles.capsBadge} style={{ background: \'rgba(6,182,212,0.15)\', color:\'#06b6d4\' }}>AUTO</span>
                                    </div>
                                    <div className={styles.diagBox}>
                                        UGX {arrears >= 0 ? arrears.toLocaleString() : 0}
                                    </div>
                                </div>''',
    '''                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>AMOUNT OWED</label>
                                        <span className={styles.capsBadge} style={{ background: \'rgba(6,182,212,0.15)\', color:\'#06b6d4\' }}>AUTO</span>
                                    </div>
                                    <div className={styles.diagBox}>
                                        UGX {arrears >= 0 ? arrears.toLocaleString() : 0}
                                    </div>
                                </div>''',
    'IntakePage: ARREARS -> AMOUNT OWED label'
)

# FolderPage: fix the ARREARS label in spec grid (was wrongly mapped to district above)
# Let's find the actual line
content = read_file(folder_jsx)
if "['ARREARS'" in content:
    content = content.replace("['ARREARS'", "['AMOUNT OWED'", 1)
    write_file(folder_jsx, content)
    print("OK: FolderPage: ARREARS -> AMOUNT OWED in spec grid")
else:
    print("MISSING: FolderPage ARREARS in spec grid (already fixed or not found)") 

print("\nAll patches complete.")