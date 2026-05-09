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

# The fix.py from the previous session added isDirty as a useMemo
# but the old early declaration was not fully removed -- only the
# useBeforeUnload block was stripped. The original const isDirty = ...
# (the non-memo version at the top of the component) is still there.
# Remove it now.

patch(INTAKE_JSX,
    '''    const [saving, setSaving] = useState(false);
    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, docs: false, notes: false });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const [errors, setErrors] = useState({});''',
    '''    const [saving, setSaving] = useState(false);
    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, docs: false, notes: false });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const [errors, setErrors] = useState({});

    // -- plot fields, owners, financials, docs & notes all declared below --''',
    "IntakePage: add marker so we can find insertion point"
)

# Now find and remove the duplicate early isDirty if it still exists
content = read(INTAKE_JSX)

# Count occurrences
count = content.count('const isDirty')
print(f"INFO   Found {count} occurrence(s) of 'const isDirty'")

if count == 2:
    # Remove the FIRST occurrence (the early one before useState hooks)
    # The early one looks like a plain const, the second is useMemo
    # Find index of first occurrence
    idx1 = content.find('const isDirty')
    idx2 = content.find('const isDirty', idx1 + 1)
    
    # Determine which is the useMemo version
    snippet1 = content[idx1:idx1+60]
    snippet2 = content[idx2:idx2+60]
    print(f"INFO   First:  {repr(snippet1)}")
    print(f"INFO   Second: {repr(snippet2)}")
    
    if 'useMemo' in snippet1:
        # First is useMemo -- second is the bad early one
        bad_idx = idx2
    else:
        # First is the bad early one
        bad_idx = idx1
    
    # Find the full block to remove -- go back to find the start of the line
    # and forward to find the end of the statement
    start = content.rfind('\n', 0, bad_idx) + 1
    # Find the semicolon that ends this statement
    end = content.find(';', bad_idx) + 1
    # Also consume the trailing newline
    if end < len(content) and content[end] == '\n':
        end += 1
    
    bad_block = content[start:end]
    print(f"INFO   Removing block: {repr(bad_block[:120])}")
    
    new_content = content[:start] + content[end:]
    write(INTAKE_JSX, new_content)
    print("OK     IntakePage: removed duplicate isDirty declaration")

elif count == 1:
    content2 = read(INTAKE_JSX)
    if 'useMemo' in content2[content2.find('const isDirty'):content2.find('const isDirty')+80]:
        print("OK     IntakePage: only one isDirty (useMemo version) -- no fix needed")
    else:
        # Only the early version exists -- replace it with useMemo
        patch(INTAKE_JSX,
            'const isDirty = plotNumber.trim() !== \'\' ||',
            '// isDirty moved below useState hooks -- see useMemo version\n    // const isDirty removed here',
            "IntakePage: comment out early isDirty"
        )
else:
    print("INFO   No isDirty found or count unexpected -- check file manually")

# Clean up the marker we added earlier (optional, harmless if left)
patch(INTAKE_JSX,
    '\n    // -- plot fields, owners, financials, docs & notes all declared below --',
    '',
    "IntakePage: remove temporary marker comment"
)

print()
print("--- Done ---")
print("Next: git add -A && git commit -m 'fix: remove duplicate isDirty declaration' && git push")