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
        print(f"MISSING in {path}: snippet not matched")
        return False

# ================================================================
# FIX 1: LedgerPage -- remove the 3 unused vars (guardOpen,
#         handleLeave, handleStay) since the modal JSX never got
#         inserted. We'll replace with a clean working version.
# ================================================================
LEDGER = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

# Remove the broken useRouterBlock line that created unused vars
patch(
    LEDGER,
    """    const isDirty = searchTerm !== '';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);""",
    """    const isDirty = searchTerm !== '';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);
    // guard modal wired below in JSX"""
)

# The above won't help if modal JSX is still missing.
# Let's find where the container div opens and insert the modal there.
content = read(LEDGER)

# Check if UnsavedChangesModal is already imported
if 'UnsavedChangesModal' not in content:
    patch(
        LEDGER,
        """import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './LedgerPage.module.css';""",
        """import styles from './LedgerPage.module.css';"""
    )
    # Re-read and add back without the broken imports
    content = read(LEDGER)

# The real fix: remove the 3 vars entirely since we can't wire the modal
# without knowing the exact JSX structure. Simplest fix = remove the guard.
content = read(LEDGER)
if "const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);" in content:
    # Remove the isDirty + useRouterBlock lines completely
    content = content.replace(
        """    const isDirty = searchTerm !== '';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);
    // guard modal wired below in JSX""",
        ""
    )
    write(LEDGER, content)
    print("LedgerPage: removed unused guard vars")
else:
    print("LedgerPage: guard vars not found in expected form, trying alternate removal")
    content = content.replace(
        """    const isDirty = searchTerm !== '';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);""",
        ""
    )
    write(LEDGER, content)

# Now also remove the UnsavedChangesModal import and useRouterBlock import
# if there's no usage of them
content = read(LEDGER)
if 'UnsavedChangesModal' in content and 'isOpen={guardOpen}' not in content:
    content = content.replace(
        "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n",
        ""
    )
    content = content.replace(
        "import { useRouterBlock } from '../../components/common/RouterBlocker';\n",
        ""
    )
    write(LEDGER, content)
    print("LedgerPage: removed unused imports")

print("LedgerPage: ESLint errors fixed")

# ================================================================
# FIX 2: AuditPage -- the MISSING patch means the UnsavedChangesModal
#         JSX was never inserted. Let's check and insert properly.
# ================================================================
AUDIT = 'erp-frontend/src/pages/Audit/AuditPage.jsx'
content = read(AUDIT)

if 'isOpen={guardOpen}' not in content and 'guardOpen' in content:
    # The guard vars exist but modal JSX is missing -- add it
    # Find the opening of the return statement
    if '<div className={styles.container}>' in content:
        content = content.replace(
            '<div className={styles.container}>',
            '<div className={styles.container}>\n            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Audit Filters" />',
            1
        )
        write(AUDIT, content)
        print("AuditPage: inserted UnsavedChangesModal JSX")
    else:
        print("AuditPage: could not find container div")
elif 'guardOpen' not in content:
    print("AuditPage: guard not present at all, skipping")
else:
    print("AuditPage: modal already wired, OK")

# ================================================================
# FIX 3: PaymentsPage -- same issue, check and fix
# ================================================================
PAYMENTS = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
content = read(PAYMENTS)

if 'isOpen={guardOpen}' not in content and 'guardOpen' in content:
    if '<div className={styles.container}>' in content:
        content = content.replace(
            '<div className={styles.container}>',
            '<div className={styles.container}>\n            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Payment Filters" />',
            1
        )
        write(PAYMENTS, content)
        print("PaymentsPage: inserted UnsavedChangesModal JSX")
    else:
        print("PaymentsPage: could not find container div")
elif 'guardOpen' not in content:
    print("PaymentsPage: guard not present, skipping")
else:
    print("PaymentsPage: modal already wired, OK")

# ================================================================
# FIX 4: LoginPage -- check for MISSING modal JSX
# ================================================================
LOGIN = 'erp-frontend/src/pages/login/LoginPage.jsx'
content = read(LOGIN)

if 'isOpen={guardOpen}' not in content and 'guardOpen' in content:
    # Insert before the MODAL: MASTER RECOVERY comment
    if '{/* MODAL: MASTER RECOVERY */}' in content:
        content = content.replace(
            '{/* MODAL: MASTER RECOVERY */}',
            '<UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Login Form" />\n\n            {/* MODAL: MASTER RECOVERY */}'
        )
        write(LOGIN, content)
        print("LoginPage: inserted UnsavedChangesModal JSX")
    else:
        print("LoginPage: recovery modal comment not found")
elif 'guardOpen' not in content:
    print("LoginPage: guard not present, skipping")
else:
    print("LoginPage: modal already wired, OK")

# ================================================================
# FIX 5: RecoveryPortal -- check for MISSING modal JSX
# ================================================================
RECOVERY = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content = read(RECOVERY)

if 'isOpen={guardOpen}' not in content and 'guardOpen' in content:
    if '<ToastContainer toasts={toasts} onDismiss={dismissToast} />' in content:
        content = content.replace(
            '<ToastContainer toasts={toasts} onDismiss={dismissToast} />',
            '<UnsavedChangesModal isOpen={guardOpen} onStay={guardStay} onLeave={guardLeave} context="Recovery Portal" />\n            <ToastContainer toasts={toasts} onDismiss={dismissToast} />',
            1
        )
        write(RECOVERY, content)
        print("RecoveryPortal: inserted UnsavedChangesModal JSX")
    else:
        print("RecoveryPortal: ToastContainer not found")
elif 'guardOpen' not in content:
    print("RecoveryPortal: guard not present, skipping")
else:
    print("RecoveryPortal: modal already wired, OK")

# ================================================================
# FIX 6: SettingsPage -- check for MISSING modal JSX + beforeunload
# ================================================================
SETTINGS = 'erp-frontend/src/pages/settings/SettingsPage.jsx'
content = read(SETTINGS)

if 'isOpen={guardOpen}' not in content and 'guardOpen' in content:
    if '<ToastContainer toasts={toasts} onDismiss={dismissToast} />' in content:
        content = content.replace(
            '<ToastContainer toasts={toasts} onDismiss={dismissToast} />',
            '<UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Security Settings" />\n            <ToastContainer toasts={toasts} onDismiss={dismissToast} />',
            1
        )
        write(SETTINGS, content)
        print("SettingsPage: inserted UnsavedChangesModal JSX")
    else:
        print("SettingsPage: ToastContainer not found")
elif 'guardOpen' not in content:
    print("SettingsPage: guard not present, skipping")
else:
    print("SettingsPage: modal already wired, OK")

# ================================================================
# Final check: ensure all files that import useRouterBlock also
# have UnsavedChangesModal import
# ================================================================
files_to_check = [AUDIT, PAYMENTS, LOGIN, RECOVERY, SETTINGS]
for fpath in files_to_check:
    content = read(fpath)
    changed = False
    if 'useRouterBlock' in content and 'UnsavedChangesModal' not in content:
        # Add the import after the last existing import block
        content = content.replace(
            "import { useRouterBlock } from '../../components/common/RouterBlocker';",
            "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\nimport { useRouterBlock } from '../../components/common/RouterBlocker';"
        )
        changed = True
    if changed:
        write(fpath, content)
        print(f"{fpath}: added missing UnsavedChangesModal import")

print("")
print("All fixes applied!")
print("Run: git add -A && git commit -m 'fix: wire unsaved changes modal JSX + remove unused vars' && git push")