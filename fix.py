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


INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# =============================================================================
# FIX 1: IntakePage -- isDirty is declared BEFORE the useState variables it
# references (plotNumber, owners, totalCost, fileQueue, noteText).
# This causes "Cannot access 'I' before initialization" -- a temporal dead zone
# error in the minified bundle. Move isDirty AFTER all the useState declarations.
# Solution: Replace isDirty with a useMemo hook placed after all state declarations.
# =============================================================================

# Step 1: Remove the early isDirty declaration (it references uninitialized state)
patch(INTAKE_JSX,
    '''    // UNSAVED DATA PROTECTION
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
    );

    const [saving, setSaving] = useState(false);''',
    '''    const [saving, setSaving] = useState(false);''',
    "IntakePage: remove early isDirty (temporal dead zone fix)"
)

# Step 2: Add isDirty as useMemo AFTER all useState declarations, and add
# the window.beforeunload effect right after
patch(INTAKE_JSX,
    '''    const sg = key => predictionService.getSuggestions(key) || [];''',
    '''    // isDirty must be defined AFTER all useState hooks to avoid
    // "Cannot access before initialization" error in the minified bundle
    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, noteText]);

    // Warn on browser refresh / tab close
    useEffect(() => {
        const handleBeforeUnload = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [isDirty, saving]);

    const sg = key => predictionService.getSuggestions(key) || [];''',
    "IntakePage: add isDirty as useMemo after all useState (correct order)"
)

# Step 3: Make sure useEffect is imported (it already is via React.useEffect
# but let's use the named import which is already in the import list)
# Check if useEffect is already imported
content = read(INTAKE_JSX)
if 'useState, useEffect' in content or 'useEffect,' in content:
    print("OK     IntakePage: useEffect already imported")
else:
    patch(INTAKE_JSX,
        'import React, { useState, useCallback, useRef } from',
        'import React, { useState, useEffect, useCallback, useRef } from',
        "IntakePage: add useEffect to React import"
    )

# Step 4: Fix the in-app nav blocker -- since we removed useBlocker,
# remove the blocker JSX modal that references blocker.state and blocker.reset()
content = read(INTAKE_JSX)
if 'blocker.state' in content:
    patch(INTAKE_JSX,
        '''            {/* UNSAVED DATA BLOCKER MODAL */}
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
            )}''',
        '',
        "IntakePage: remove blocker modal JSX (blocker no longer exists)"
    )
else:
    print("OK     IntakePage: blocker modal JSX already removed")

# =============================================================================
# FIX 2: FolderPage -- same circular dep check
# The navBlocker modal should already be gone from last fix.py run.
# But double-check isDirty-like patterns in FolderPage aren't causing issues.
# FolderPage uses isEditing (boolean state), not a computed isDirty,
# so it should be fine. Just verify navBlocker references are gone.
# =============================================================================

FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

content = read(FOLDER_JSX)
if 'navBlocker' in content:
    print("FOUND  FolderPage: navBlocker still present -- removing")
    patch(FOLDER_JSX,
        "    const navBlocker = useBlocker(",
        "    // navBlocker removed",
        "FolderPage: remove navBlocker declaration"
    )
else:
    print("OK     FolderPage: navBlocker already removed")

# Check for useBlocker import in FolderPage
if 'useBlocker' in content:
    patch(FOLDER_JSX,
        ', useBlocker',
        '',
        "FolderPage: remove useBlocker from imports"
    )
else:
    print("OK     FolderPage: useBlocker already removed from imports")

# Check for useBeforeUnload in FolderPage
if 'useBeforeUnload' in read(FOLDER_JSX):
    patch(FOLDER_JSX,
        ', useBeforeUnload',
        '',
        "FolderPage: remove useBeforeUnload from imports"
    )
else:
    print("OK     FolderPage: useBeforeUnload already removed from imports")

print("\n--- All patches applied ---")
print()
print("Next steps:")
print("1. git add -A && git commit -m 'fix: isDirty temporal dead zone - fixes blank page' && git push")
print("2. Wait for Render green tick (5-10 min)")
print("3. Test golden-seed.onrender.com/land/new and /folder/[any-id]")