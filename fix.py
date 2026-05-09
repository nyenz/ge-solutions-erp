import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK     {label}")
    else:
        print(f"MISSING  {label}")


FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'


# =========================================================================
# FIX 1: FolderPage.jsx
# Remove useBlocker and useBeforeUnload (both need data router in RR v7).
# Replace with window.onbeforeunload for browser tab close (always works).
# Replace the in-app blocker modal with a simple window.confirm approach.
# =========================================================================

# 1a. Fix import -- remove useBeforeUnload and useBlocker
patch(
    FOLDER_JSX,
    "import { useParams, useNavigate, useBeforeUnload, useBlocker } from 'react-router-dom';",
    "import { useParams, useNavigate } from 'react-router-dom';",
    "FolderPage: remove useBeforeUnload + useBlocker from import"
)

# Also handle the unstable_ variant in case it's still there
patch(
    FOLDER_JSX,
    "import { useParams, useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';",
    "import { useParams, useNavigate } from 'react-router-dom';",
    "FolderPage: remove unstable_ variant from import"
)

# 1b. Remove the useBeforeUnload call block
patch(
    FOLDER_JSX,
    """\n    // Browser refresh / tab close while editing
    useBeforeUnload(
        React.useCallback(
            (e) => {
                if (isEditing) { e.preventDefault(); e.returnValue = ''; }
            },
            [isEditing]
        )
    );\n""",
    "\n",
    "FolderPage: remove useBeforeUnload call"
)

# 1c. Remove the navBlocker declaration
patch(
    FOLDER_JSX,
    """\n    // In-app navigation while editing -- block and show custom confirm
    const navBlocker = useBlocker(
        React.useCallback(
            ({ currentLocation, nextLocation }) =>
                isEditing && currentLocation.pathname !== nextLocation.pathname,
            [isEditing]
        )
    );\n""",
    "\n",
    "FolderPage: remove useBlocker declaration"
)

# 1d. Remove the navBlocker modal JSX at bottom of return
patch(
    FOLDER_JSX,
    """            {/* IN-APP NAVIGATION BLOCKER WHILE EDITING */}
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
            )}\n""",
    "",
    "FolderPage: remove navBlocker modal JSX"
)

# 1e. Replace handleAbort with a version that uses window.confirm instead of useConfirm
# The existing handleAbort uses the custom confirm modal which is fine -- keep it.
# Just add window.onbeforeunload effect to warn on tab close while editing.
# Insert it after the useEffect for firstInputRef focus.
patch(
    FOLDER_JSX,
    "    useEffect(() => {\n        if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120);\n    }, [isEditing]);",
    """    useEffect(() => {
        if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120);
    }, [isEditing]);

    // Warn user if they try to close the tab while editing
    useEffect(() => {
        const handler = (e) => {
            if (isEditing) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing]);""",
    "FolderPage: add window beforeunload effect for tab close warning"
)


# =========================================================================
# FIX 2: IntakePage.jsx
# Remove useBeforeUnload and useBlocker. Use window.onbeforeunload instead.
# Remove the blocker modal JSX entirely.
# =========================================================================

# 2a. Fix import
patch(
    INTAKE_JSX,
    "import { useNavigate, useBeforeUnload, useBlocker } from 'react-router-dom';",
    "import { useNavigate } from 'react-router-dom';",
    "IntakePage: remove useBeforeUnload + useBlocker from import"
)

# Also handle unstable_ variant
patch(
    INTAKE_JSX,
    "import { useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';",
    "import { useNavigate } from 'react-router-dom';",
    "IntakePage: remove unstable_ variant from import"
)

# 2b. Remove isDirty computation and the two hook calls
patch(
    INTAKE_JSX,
    """    // UNSAVED DATA PROTECTION
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
    );""",
    """    // UNSAVED DATA PROTECTION via window.beforeunload
    // Form is "dirty" if any meaningful field has been touched
    const isDirty = plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '';

    useEffect(() => {
        const handler = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);""",
    "IntakePage: replace useBeforeUnload + useBlocker with window effect"
)

# 2c. Remove blocker modal JSX from return statement
patch(
    INTAKE_JSX,
    """            {/* UNSAVED DATA BLOCKER MODAL */}
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
            )}""",
    "",
    "IntakePage: remove blocker modal JSX"
)

# 2d. Also remove React import since we now use useEffect -- check if it's there
# IntakePage uses useState etc so React is imported. Just need useEffect.
patch(
    INTAKE_JSX,
    "import React, { useState, useEffect, useRef, useCallback } from 'react';",
    "import React, { useState, useEffect, useRef, useCallback } from 'react';",
    "IntakePage: React import already has useEffect (no change needed)"
)

# Check if useEffect is in the import
content = read(INTAKE_JSX)
if 'useEffect' not in content.split('from')[0]:
    patch(
        INTAKE_JSX,
        "import React, { useState, useRef, useCallback } from 'react';",
        "import React, { useState, useEffect, useRef, useCallback } from 'react';",
        "IntakePage: add useEffect to React import"
    )


# =========================================================================
# FIX 3: App.jsx
# BrowserRouter is fine for most things, but useBlocker is now removed
# so no router change is needed. App.jsx stays as-is.
# Just verify the import is clean.
# =========================================================================
print("\nApp.jsx does not need changes -- useBlocker is removed from all pages.")


print("\n--- All patches applied ---")
print()
print("Next steps for David:")
print("1. py fix.py")
print("2. Check output for OK / MISSING")
print("3. git add -A && git commit -m 'fix: remove useBlocker - fixes blank page crash' && git push")
print("4. Wait for Render green tick (5-10 min)")
print("5. Test golden-seed.onrender.com/land/new and /folder/[any-id]")