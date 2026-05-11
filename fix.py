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
# FIX 1: FolderPage.jsx -- move touchedRef declaration BEFORE
# useRouterBlock to eliminate the TDZ "cannot access before
# initialization" crash in the minified bundle.
# ================================================================
FOLDER = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Remove touchedRef from its current (late) position
patch(
    FOLDER,
    '    const firstInputRef = useRef(null);\n    const fileInputRef  = useRef(null);\n    // Track whether any field was actually changed since edit mode opened\n    const touchedRef    = useRef(false);\n    // Wrap setBuffer so any change marks the form as touched\n    const touchedSetBuffer = React.useCallback((updater) => {',
    '    const firstInputRef = useRef(null);\n    const fileInputRef  = useRef(null);\n    // Track whether any field was actually changed since edit mode opened\n    // MUST be declared before useRouterBlock to avoid TDZ crash in minified build\n    const touchedRef    = useRef(false);\n    // Wrap setBuffer so any change marks the form as touched\n    const touchedSetBuffer = React.useCallback((updater) => {',
    'FolderPage touchedRef position comment'
)

# Move the useRouterBlock call to AFTER touchedRef is declared.
# The real fix: remove the useRouterBlock line from its current early position
# and re-insert it after touchedRef. Currently it appears before touchedRef.
content = read(FOLDER)

OLD_GUARD = "    // Unsaved changes guard -- active only while in edit mode and not mid-save\n    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!committing && isEditing && touchedRef.current);"

# If the guard block appears before the touchedRef declaration, move it after
touchedref_pos = content.find('const touchedRef    = useRef(false);')
guard_pos = content.find(OLD_GUARD)

if guard_pos != -1 and touchedref_pos != -1 and guard_pos < touchedref_pos:
    # Remove from current (early) position
    content = content.replace(OLD_GUARD + '\n', '', 1)
    # Insert after touchedSetBuffer declaration
    insert_after = '    const touchedSetBuffer = React.useCallback((updater) => {\n        touchedRef.current = true;\n        setBuffer(updater);\n    }, []);'
    content = content.replace(
        insert_after,
        insert_after + '\n\n    // Unsaved changes guard -- active only while in edit mode and not mid-save\n    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!committing && isEditing && touchedRef.current);'
    )
    write(FOLDER, content)
    print("OK: FolderPage -- moved useRouterBlock after touchedRef (TDZ fix)")
else:
    print("INFO: FolderPage guard position already correct or not found -- skipping reorder")

# ================================================================
# FIX 2: PaymentsPage.jsx -- clicking a row navigates to the
# folder page and scrolls to the finance/payments section.
# We add #payments hash so FolderPage can open that drawer.
# ================================================================
PAYMENTS = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'

# Fix row click to use hash navigation
patch(
    PAYMENTS,
    "                                    onClick={() => pay.projectId && navigate(`/folder/${pay.projectId}`)}",
    "                                    onClick={() => pay.projectId && navigate(`/folder/${pay.projectId}#payments`)}",
    'PaymentsPage row click hash'
)

patch(
    PAYMENTS,
    "                                        onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}`); }}",
    "                                        onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}#payments`); }}",
    'PaymentsPage VIEW button hash'
)

# ================================================================
# FIX 3: FolderPage.jsx -- open the payments drawer when the
# page loads with #payments hash in the URL.
# ================================================================
content = read(FOLDER)

OLD_SCROLL = "    useEffect(() => { window.scrollTo({ top:0, behavior:'smooth' }); }, [id]);"
NEW_SCROLL = """    useEffect(() => {
        // If navigated here with a hash (e.g. #payments from PaymentsPage),
        // open the matching drawer and scroll to it. Otherwise scroll to top.
        const hash = window.location.hash.replace('#', '');
        if (hash && ['tech','identity','finance','vault','intel','payments'].includes(hash)) {
            setDrawers(prev => ({ ...prev, [hash]: true }));
            setTimeout(() => {
                const el = document.getElementById('drawer-' + hash);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 350);
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);"""

patch(FOLDER, OLD_SCROLL, NEW_SCROLL, 'FolderPage hash scroll')

# Add id attributes to the section elements so we can scroll to them.
# We target the payments section specifically.
patch(
    FOLDER,
    '<section className={styles.hwPanel} aria-label="Payment History">',
    '<section id="drawer-payments" className={styles.hwPanel} aria-label="Payment History">',
    'FolderPage payments section id'
)

patch(
    FOLDER,
    '<section className={styles.hwPanel} aria-label="Plot Details">',
    '<section id="drawer-tech" className={styles.hwPanel} aria-label="Plot Details">',
    'FolderPage tech section id'
)

patch(
    FOLDER,
    '<section className={styles.hwPanel} aria-label="Owners">',
    '<section id="drawer-identity" className={styles.hwPanel} aria-label="Owners">',
    'FolderPage identity section id'
)

patch(
    FOLDER,
    '<section className={styles.hwPanel} aria-label="Financials">',
    '<section id="drawer-finance" className={styles.hwPanel} aria-label="Financials">',
    'FolderPage finance section id'
)

print("\nAll patches applied.")
print("Run: git add -A && git commit -m 'fix: TDZ crash + payments deep-link to folder payments section' && git push")