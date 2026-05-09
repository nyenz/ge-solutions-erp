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

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK     {label}")
    else:
        print(f"MISSING  {label} -- snippet not found")

INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# ---------------------------------------------------------------
# THE FIX: Remove both useEffect blocks that reference isDirty
# before it is declared, and the early isDirty useMemo that sits
# before the state declarations it depends on.
# Then add ONE clean useEffect AFTER isDirty is declared.
#
# The component body should be:
#   useState hooks (saving, drawers, errors, plot fields, owners,
#                   financials, docs, notes)
#   isDirty useMemo  <-- depends on the state above
#   useEffect for beforeunload  <-- depends on isDirty + saving
#   useEffect for submit / navigate
#   rest of handlers
# ---------------------------------------------------------------

# Step 1: Remove the first (orphan) useEffect that fires before isDirty exists
patch(INTAKE,
    '''    // UNSAVED DATA PROTECTION via window.beforeunload
    // Form is "dirty" if any meaningful field has been touched

    useEffect(() => {
        const handler = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    const [saving, setSaving] = useState(false);''',
    '''    const [saving, setSaving] = useState(false);''',
    "IntakePage: remove orphan useEffect that fires before isDirty is declared"
)

# Step 2: Remove the duplicate beforeunload useEffect that appears after
# isDirty useMemo (we'll keep only the correct one below)
patch(INTAKE,
    '''    // Warn on browser refresh / tab close
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
    '''    useEffect(() => {
        const handler = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    const sg = key => predictionService.getSuggestions(key) || [];''',
    "IntakePage: replace duplicate useEffect with single clean version"
)

print()
print("--- Done ---")
print("Run: git add -A && git commit -m 'fix: resolve TDZ crash - isDirty declared before state' && git push")