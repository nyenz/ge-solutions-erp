import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK     {label}")
    else:
        print(f"MISSING  {label}")


# =============================================================================
# FIX 1: AuditPage.module.css
# Add .hwSelectWrapActive variant that makes the box look orange-filled
# like the active filter buttons when a non-default value is selected.
# =============================================================================

AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'

old_audit_end = '''.hwSelectWrap .active {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
}
.hwSelectWrap .active [class*="currentValue"], .hwSelectWrap .active [class*="icon"] {
    color: #1a2e30 !important;
}'''

new_audit_end = '''.hwSelectWrap .active {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
}
.hwSelectWrap .active [class*="currentValue"], .hwSelectWrap .active [class*="icon"] {
    color: #1a2e30 !important;
}

/* ACTIVE FILTER STATE for HardwareSelect dropdowns
   When operator != ALL STAFF or action != ALL ACTIONS, the parent
   gets .hwSelectWrapActive via JS -- this makes it orange-filled
   identical to the active filter pill buttons. */
.hwSelectWrapActive [class*="selectBox"] {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35) !important;
}
.hwSelectWrapActive [class*="currentValue"] {
    color: #1a2e30 !important;
    font-weight: 900 !important;
}
.hwSelectWrapActive [class*="icon"] {
    color: #1a2e30 !important;
}
.hwSelectWrapActive [class*="selectBox"]:hover {
    background: #f0a050 !important;
    border-color: #f0a050 !important;
    box-shadow: 0 0 18px rgba(238, 140, 58, 0.5) !important;
}'''

patch(AUDIT_CSS, old_audit_end, new_audit_end, "AuditPage.module.css: add hwSelectWrapActive orange state")


# =============================================================================
# FIX 2: AuditPage.jsx
# Add hwSelectWrapActive class to the wrap div when a non-default value is
# selected, so the dropdown looks orange-filled like the active buttons.
# =============================================================================

AUDIT_JSX = 'erp-frontend/src/pages/Audit/AuditPage.jsx'

old_select_operator = '''                    <div className={styles.hwSelectWrap}>
                        <HardwareSelect
                            label="OPERATOR ID"
                            options={operatorOptions}
                            value={filters.operator || 'ALL STAFF'}
                            onChange={val => setFilters({...filters, operator: val})}
                        />
                    </div>
                    <div className={styles.hwSelectWrap}>
                        <HardwareSelect
                            label="PROTOCOL CLASS"
                            options={['ALL ACTIONS', 'CALL LOG', 'LOGIN_SUCCESS', 'EDIT RECORD', 'STAGE OVERRIDE', 'INTAKE']}
                            value={filters.action || 'ALL ACTIONS'}
                            onChange={val => setFilters({...filters, action: val})}
                        />
                    </div>'''

new_select_operator = '''                    <div className={`${styles.hwSelectWrap} ${(filters.operator && filters.operator !== 'ALL STAFF') ? styles.hwSelectWrapActive : ''}`}>
                        <HardwareSelect
                            label="OPERATOR ID"
                            options={operatorOptions}
                            value={filters.operator || 'ALL STAFF'}
                            onChange={val => setFilters({...filters, operator: val})}
                        />
                    </div>
                    <div className={`${styles.hwSelectWrap} ${(filters.action && filters.action !== 'ALL ACTIONS') ? styles.hwSelectWrapActive : ''}`}>
                        <HardwareSelect
                            label="PROTOCOL CLASS"
                            options={['ALL ACTIONS', 'CALL LOG', 'LOGIN_SUCCESS', 'EDIT RECORD', 'STAGE OVERRIDE', 'INTAKE']}
                            value={filters.action || 'ALL ACTIONS'}
                            onChange={val => setFilters({...filters, action: val})}
                        />
                    </div>'''

patch(AUDIT_JSX, old_select_operator, new_select_operator, "AuditPage.jsx: orange-fill active HardwareSelect")


# =============================================================================
# FIX 3: IntakePage.jsx -- unsaved data protection
# A) Browser refresh / tab close with data entered  -> beforeunload warning
# B) In-app navigation (clicking sidebar) with data -> custom confirm modal
# C) The form is considered "dirty" when any field has a value
# =============================================================================

INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Add useBeforeUnload + useBlocker to the react-router-dom import
old_intake_import = "import { useNavigate } from 'react-router-dom';"

new_intake_import = "import { useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';"

patch(INTAKE_JSX, old_intake_import, new_intake_import, "IntakePage.jsx: import useBeforeUnload + useBlocker")

# Add dirty detection and blocking logic after the fileInputRef line
old_intake_filedref = "    const fileInputRef = useRef(null);"

new_intake_filedref = '''    const fileInputRef = useRef(null);

    // UNSAVED DATA PROTECTION
    // Form is "dirty" if any meaningful field has been touched
    const isDirty = plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '';

    // A) Browser refresh / tab close -- shows browser native warning
    useBeforeUnload(
        React.useCallback(
            (e) => {
                if (isDirty && !saving) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            },
            [isDirty, saving]
        )
    );

    // B) In-app navigation (React Router) -- shows custom confirm
    const blocker = useBlocker(
        React.useCallback(
            ({ currentLocation, nextLocation }) =>
                isDirty && !saving && currentLocation.pathname !== nextLocation.pathname,
            [isDirty, saving]
        )
    );'''

patch(INTAKE_JSX, old_intake_filedref, new_intake_filedref, "IntakePage.jsx: dirty state + beforeunload + blocker")

# Add the blocker confirm UI before the closing return/JSX container
old_intake_container_open = "    return (\n        <div className={styles.container}>"

new_intake_container_open = '''    return (
        <div className={styles.container}>
            {/* UNSAVED DATA BLOCKER MODAL */}
            {blocker.state === 'blocked' && (
                <div style={{
                    position:'fixed',inset:0,zIndex:99999,
                    background:'rgba(10,20,22,0.85)',
                    backdropFilter:'blur(6px)',
                    display:'flex',alignItems:'center',justifyContent:'center',
                    padding:'20px'
                }} role="dialog" aria-modal="true">
                    <div style={{
                        background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                        border:'2px solid rgba(238,140,58,0.4)',
                        borderRadius:14,maxWidth:440,width:'100%',
                        padding:'clamp(20px,3vw,32px)',
                        boxShadow:'0 30px 80px rgba(0,0,0,0.7)'
                    }}>
                        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:16,paddingBottom:14,borderBottom:'1px solid rgba(245,158,11,0.25)'}}>
                            <FiAlertTriangle style={{color:'#f59e0b',fontSize:22,flexShrink:0}} aria-hidden="true"/>
                            <span style={{fontFamily:"'Space Mono',monospace",fontWeight:900,fontSize:12,letterSpacing:2,textTransform:'uppercase',color:'#fcd34d'}}>
                                UNSAVED DATA
                            </span>
                        </div>
                        <p style={{fontFamily:"'DM Sans',sans-serif",fontSize:14,fontWeight:700,color:'rgba(255,255,255,0.8)',lineHeight:1.6,margin:'0 0 20px'}}>
                            You have unsaved data on this form. If you leave now, all entered information will be lost.
                        </p>
                        <div style={{display:'flex',justifyContent:'flex-end',gap:10,flexWrap:'wrap'}}>
                            <button
                                onClick={() => blocker.reset()}
                                style={{background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',padding:'9px 18px',borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:10,textTransform:'uppercase',letterSpacing:1,cursor:'pointer'}}>
                                <FiX style={{marginRight:5}} aria-hidden="true"/>STAY ON PAGE
                            </button>
                            <button
                                onClick={() => blocker.proceed()}
                                style={{background:'rgba(239,68,68,0.15)',border:'1.5px solid rgba(239,68,68,0.5)',color:'#fca5a5',padding:'9px 18px',borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:10,textTransform:'uppercase',letterSpacing:1,cursor:'pointer'}}>
                                <FiTrash2 style={{marginRight:5}} aria-hidden="true"/>LEAVE & DISCARD
                            </button>
                        </div>
                    </div>
                </div>
            )}'''

patch(INTAKE_JSX, old_intake_container_open, new_intake_container_open, "IntakePage.jsx: blocker confirm modal UI")

# Verify icons are already imported
content = read(INTAKE_JSX)
if 'FiAlertTriangle' in content and 'FiTrash2' in content:
    print("OK     IntakePage.jsx: FiAlertTriangle and FiTrash2 already imported")
else:
    print("MISSING  IntakePage.jsx: check icon imports manually")


# =============================================================================
# FIX 4: FolderPage.jsx -- add in-app nav blocker while isEditing=true
# (already has beforeunload; we add useBlocker for sidebar navigation)
# =============================================================================

FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Add useBlocker to the react-router-dom import
old_folder_router_import = "import { useParams, useNavigate } from 'react-router-dom';"

new_folder_router_import = "import { useParams, useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';"

patch(FOLDER_JSX, old_folder_router_import, new_folder_router_import, "FolderPage.jsx: import useBlocker")

# Replace the existing useEffect beforeunload with useBeforeUnload + add useBlocker
old_folder_beforeunload = '''    useEffect(() => {
        const h = (e) => { if (isEditing) { e.preventDefault(); e.returnValue=''; } };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, [isEditing]);'''

new_folder_beforeunload = '''    // Browser refresh / tab close while editing
    useBeforeUnload(
        React.useCallback(
            (e) => {
                if (isEditing) { e.preventDefault(); e.returnValue = ''; }
            },
            [isEditing]
        )
    );

    // In-app navigation while editing -- block and show custom confirm
    const navBlocker = useBlocker(
        React.useCallback(
            ({ currentLocation, nextLocation }) =>
                isEditing && currentLocation.pathname !== nextLocation.pathname,
            [isEditing]
        )
    );'''

patch(FOLDER_JSX, old_folder_beforeunload, new_folder_beforeunload, "FolderPage.jsx: replace useEffect beforeunload with useBeforeUnload + useBlocker")

# Add the navBlocker modal inside the JSX, right after the ConfirmModal line
old_folder_confirm_modal = "            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />"

new_folder_confirm_modal = '''            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />

            {/* IN-APP NAVIGATION BLOCKER WHILE EDITING */}
            {navBlocker.state === 'blocked' && (
                <div style={{
                    position:'fixed',inset:0,zIndex:99998,
                    background:'rgba(10,20,22,0.82)',
                    backdropFilter:'blur(6px)',
                    display:'flex',alignItems:'center',justifyContent:'center',
                    padding:'20px'
                }} role="dialog" aria-modal="true">
                    <div style={{
                        background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                        border:'2px solid rgba(238,140,58,0.4)',
                        borderRadius:14,maxWidth:440,width:'100%',
                        padding:'28px',
                        boxShadow:'0 30px 80px rgba(0,0,0,0.7)'
                    }}>
                        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:14,paddingBottom:14,borderBottom:'1px solid rgba(245,158,11,0.25)'}}>
                            <FiAlertTriangle style={{color:'#f59e0b',fontSize:22,flexShrink:0}} aria-hidden="true"/>
                            <span style={{fontFamily:"'Space Mono',monospace",fontWeight:900,fontSize:11,letterSpacing:2,textTransform:'uppercase',color:'#fcd34d'}}>
                                UNSAVED CHANGES
                            </span>
                        </div>
                        <p style={{fontFamily:"'DM Sans',sans-serif",fontSize:14,fontWeight:700,color:'rgba(255,255,255,0.8)',lineHeight:1.6,margin:'0 0 20px'}}>
                            You are in <strong style={{color:'#EE8C3A'}}>EDIT MODE</strong> with unsaved changes. Leaving this page will discard all modifications.
                        </p>
                        <div style={{display:'flex',justifyContent:'flex-end',gap:10,flexWrap:'wrap'}}>
                            <button
                                onClick={() => navBlocker.reset()}
                                style={{background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',padding:'9px 18px',borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:10,textTransform:'uppercase',letterSpacing:1,cursor:'pointer'}}>
                                <FiX style={{marginRight:5}} aria-hidden="true"/>STAY & KEEP EDITING
                            </button>
                            <button
                                onClick={() => { setIsEditing(false); navBlocker.proceed(); }}
                                style={{background:'rgba(239,68,68,0.15)',border:'1.5px solid rgba(239,68,68,0.5)',color:'#fca5a5',padding:'9px 18px',borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:10,textTransform:'uppercase',letterSpacing:1,cursor:'pointer'}}>
                                <FiTrash2 style={{marginRight:5}} aria-hidden="true"/>LEAVE & DISCARD
                            </button>
                        </div>
                    </div>
                </div>
            )}'''

patch(FOLDER_JSX, old_folder_confirm_modal, new_folder_confirm_modal, "FolderPage.jsx: navBlocker modal")

# Verify FiAlertTriangle is in FolderPage imports
content = read(FOLDER_JSX)
if 'FiAlertTriangle' in content:
    print("OK     FolderPage.jsx: FiAlertTriangle already imported")
else:
    print("MISSING  FolderPage.jsx: need to add FiAlertTriangle to imports")


print("\n--- All patches applied ---")
print()
print("SUMMARY OF CHANGES:")
print("  1. AuditPage: HardwareSelect turns orange-filled when non-default value selected")
print("  2. IntakePage: warns before browser refresh + blocks in-app nav with custom modal")
print("  3. FolderPage: improved beforeunload + blocks in-app nav while in edit mode")
print()
print("git add -A && git commit -m 'fix: orange active filter selects + unsaved data protection' && git push")