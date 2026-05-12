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


# ── FIX 1: FiHome and FiArchive icons missing from import ──────────
# The previous fix.py tried to add them but the patch may not have applied.
# We check for both possible states and fix whichever is present.

folder_path = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content = read(folder_path)

# Check if FiHome is already in imports
if 'FiHome' not in content:
    # Add FiHome and FiArchive to the react-icons import
    old_icons = "        FiDollarSign, FiActivity\n    } from 'react-icons/fi';"
    new_icons = "        FiDollarSign, FiActivity, FiHome, FiArchive\n    } from 'react-icons/fi';"
    if old_icons in content:
        patch(folder_path, old_icons, new_icons, "Add FiHome FiArchive icons")
    else:
        # Try alternate - maybe it was partially applied
        old_icons2 = "        FiDollarSign, FiActivity, FiHome, FiArchive\n    } from 'react-icons/fi';"
        if old_icons2 not in content:
            print("MISSING: Could not locate icons import line - checking content...")
            # Find the actual line
            for line in content.split('\n'):
                if 'FiDollarSign' in line and 'react-icons' not in line:
                    print(f"  Found: {line}")
else:
    print("OK: FiHome already present in imports")


# ── FIX 2: setDrawers is not defined ───────────────────────────────
# The hash navigation useEffect references setDrawers which no longer exists.
# Replace with the correct version that only uses setActiveTab.

old_hash_effect = """    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                const el = document.getElementById('paymentHistorySection');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);"""

# Also handle the OLD version that still references setDrawers
old_hash_with_drawers = """    useEffect(() => {
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

new_hash_effect = """    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                const el = document.getElementById('paymentHistorySection');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);"""

content = read(folder_path)
if 'setDrawers' in content:
    if old_hash_with_drawers in content:
        patch(folder_path, old_hash_with_drawers, new_hash_effect, "Fix setDrawers ref in hash effect")
    else:
        # setDrawers is somewhere else — find and report
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'setDrawers' in line:
                print(f"  setDrawers found at line {i+1}: {line.strip()}")
        print("ERROR: setDrawers found but could not auto-patch. Check lines above.")
elif old_hash_effect in content:
    print("OK: Hash effect already uses setActiveTab (correct)")
else:
    print("OK: No setDrawers reference found - already fixed")


print()
print("Done. Run: git add -A && git commit -m 'fix FiHome undefined and setDrawers reference error' && git push")