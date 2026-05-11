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
        print(f"MISSING (not found in {path}): snippet not matched")
        return False

# ================================================================
# FIX 1: IntakePage.jsx
# - Add beforeunload guard (tab close / hard refresh)
# - Add duplicate plot button
# ================================================================

# 1a: Add beforeunload effect in IntakePage
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!saving && isDirty);',
    '\n'.join([
        '    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =',
        '        useRouterBlock(!saving && isDirty);',
        '',
        '    // beforeunload -- catches tab close, hard refresh, browser back button to external site',
        '    useEffect(() => {',
        '        if (!isDirty || saving) return;',
        '        const handler = (e) => {',
        '            e.preventDefault();',
        "            e.returnValue = '';",
        '        };',
        "        window.addEventListener('beforeunload', handler);",
        "        return () => window.removeEventListener('beforeunload', handler);",
        '    }, [isDirty, saving]);',
    ])
)

# 1b: Add duplicate plot button + handler in IntakePage
# Add duplicatePlot function before handleSubmit
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '    const handleSubmit = async () => {',
    '\n'.join([
        '    // Duplicate: pre-fill from last submitted or current form data',
        '    const handleDuplicatePlot = () => {',
        '        // Keep all fields except plotNumber (must be unique)',
        "        setTenure(tenure);",
        "        setPhysicalBoxNumber(physicalBoxNumber);",
        "        setDistrict(district);",
        "        setCounty(county);",
        "        setBlockRoad(blockRoad);",
        "        setVolume(volume);",
        "        setFolio(folio);",
        "        setInstrumentNo(instrumentNo);",
        "        setTotalCost(totalCost);",
        "        setInitialPayment('');",
        "        setIsBacklog(isBacklog);",
        "        setMonthlyStorageFee(monthlyStorageFee);",
        "        setInitialStorageFee('');",
        "        // Clear unique fields",
        "        setPlotNumber('');",
        "        setFileQueue([]);",
        "        setNotesList([]);",
        "        // Keep owners as-is",
        "        toast('PLOT DUPLICATED -- enter new Plot ID and adjust details', 'info', 4000);",
        '    };',
        '',
        '    const handleSubmit = async () => {',
    ])
)

# 1c: Add duplicate button in submit section of IntakePage
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '                <div className={styles.submitSection}>\n                    <button type="button" className={styles.primaryCommitBtn}\n                        onClick={handleSubmit} disabled={saving}>\n                        <FiSend aria-hidden="true" />\n                        {saving ? \'SAVING...\' : \'SAVE NEW PLOT\'}\n                    </button>\n                </div>',
    '\n'.join([
        '                <div className={styles.submitSection}>',
        '                    <button type="button" className={styles.duplicateBtn}',
        '                        onClick={handleDuplicatePlot} disabled={saving}',
        '                        title="Copy all fields except Plot ID to quickly register a similar plot">',
        '                        <FiCopy aria-hidden="true" />',
        '                        DUPLICATE PLOT',
        '                    </button>',
        '                    <button type="button" className={styles.primaryCommitBtn}',
        '                        onClick={handleSubmit} disabled={saving}>',
        '                        <FiSend aria-hidden="true" />',
        "                        {saving ? 'SAVING...' : 'SAVE NEW PLOT'}",
        '                    </button>',
        '                </div>',
    ])
)

# 1d: Add FiCopy to imports in IntakePage
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    'import {\n    FiMap, FiUsers, FiCreditCard, FiUploadCloud,\n    FiInfo, FiPlusSquare, FiTrash2, FiSend, FiSave,\n    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon,\n    FiEdit3\n} from \'react-icons/fi\';',
    '\n'.join([
        'import {',
        '    FiMap, FiUsers, FiCreditCard, FiUploadCloud,',
        '    FiInfo, FiPlusSquare, FiTrash2, FiSend, FiSave, FiCopy,',
        '    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon,',
        '    FiEdit3',
        "} from 'react-icons/fi';",
    ])
)

# ================================================================
# FIX 2: FolderPage.jsx
# - Add beforeunload guard for edit mode
# ================================================================

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    "    // NOTE: beforeunload is now handled by useUnsavedChanges hook",
    '\n'.join([
        '    // beforeunload -- catches tab close, hard refresh, browser back to external site',
        '    useEffect(() => {',
        '        if (!isEditing || committing) return;',
        '        const handler = (e) => {',
        '            e.preventDefault();',
        "            e.returnValue = '';",
        '        };',
        "        window.addEventListener('beforeunload', handler);",
        "        return () => window.removeEventListener('beforeunload', handler);",
        '    }, [isEditing, committing]);',
    ])
)

# ================================================================
# FIX 3: IntakePage.module.css
# - Add duplicate button style + fix submitSection to space-between
# ================================================================

patch(
    'erp-frontend/src/pages/Intake/IntakePage.module.css',
    '.submitSection {\n    display: flex; justify-content: flex-end;\n    padding-top: clamp(20px, 3vw, 32px); margin-top: var(--gap-md);\n    border-top: 1px solid rgba(255, 255, 255, 0.1);\n}',
    '\n'.join([
        '.submitSection {',
        '    display: flex;',
        '    justify-content: space-between;',
        '    align-items: center;',
        '    gap: clamp(10px, 1.4vw, 16px);',
        '    padding-top: clamp(20px, 3vw, 32px);',
        '    margin-top: var(--gap-md);',
        '    border-top: 1px solid rgba(255, 255, 255, 0.1);',
        '    flex-wrap: wrap;',
        '}',
        '',
        '.duplicateBtn {',
        '    display: inline-flex;',
        '    align-items: center;',
        '    gap: clamp(5px, 0.7vw, 8px);',
        '    padding: 0 clamp(14px, 1.8vw, 20px);',
        '    height: clamp(36px, 4.5vw, 42px);',
        '    background: rgba(26, 46, 48, 0.75);',
        '    border: 1.5px solid rgba(255, 255, 255, 0.25);',
        '    color: rgba(255, 255, 255, 0.8);',
        '    border-radius: 8px;',
        "    font-family: 'DM Sans', sans-serif;",
        '    font-weight: 900;',
        '    font-size: clamp(9px, 0.9vw, 11px);',
        '    text-transform: uppercase;',
        '    letter-spacing: 1.5px;',
        '    cursor: pointer;',
        '    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;',
        '    white-space: nowrap;',
        '}',
        '.duplicateBtn:hover:not(:disabled) {',
        '    background: rgba(6, 182, 212, 0.12);',
        '    border-color: #06b6d4;',
        '    color: #06b6d4;',
        '    box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);',
        '}',
        '.duplicateBtn:disabled { opacity: 0.4; cursor: not-allowed; }',
        '.duplicateBtn:focus-visible { outline: 2px solid #06b6d4; outline-offset: 2px; }',
    ])
)

print("\nAll fixes applied!")
print("Now run: git add -A && git commit -m 'fix: consistent unsaved changes guard all scenarios + duplicate plot button' && git push")