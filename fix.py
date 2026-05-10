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
        print(f"OK       {label}")
    else:
        print(f"MISSING  {label}")

INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Remove the unused state variables that were added but whose JSX never got patched in
patch(INTAKE,
'''    // Docs & notes
    const [fileQueue,    setFileQueue]    = useState([]);
    const [noteText,     setNoteText]     = useState('');
    const [notesList,    setNotesList]    = useState([]); // multi-note list
    const [noteModal,    setNoteModal]    = useState(false);
    const [noteDraft,    setNoteDraft]    = useState('');

    // Backlog late entry
    const [backfillMonths, setBackfillMonths] = useState('');''',
'''    // Docs & notes
    const [fileQueue,    setFileQueue]    = useState([]);
    const [noteText,     setNoteText]     = useState('');''',
    "IntakePage -- Remove unused state variables (notesList, noteModal, noteDraft, backfillMonths)"
)

# Also fix the payload which references notesList and backfillMonths
patch(INTAKE,
'''                notes: [
                    ...notesList.map(n => ({ content: n })),
                    ...(noteText.trim() ? [{ content: noteText.trim() }] : []),
                    ...(isBacklog && backfillMonths && Number(backfillMonths) > 0
                        ? [{ content: `BACKFILL NOTE: ${backfillMonths} month(s) of pre-existing storage fees (UGX ${(Number(backfillMonths) * 50000).toLocaleString()}) recorded at intake. Admin should adjust accumulated fees via folder page.` }]
                        : [])
                ],''',
'''                notes: noteText.trim() ? [{ content: noteText.trim() }] : [],''',
    "IntakePage -- Fix payload notes back to simple form"
)

print()
print("=== ALL PATCHES COMPLETE ===")
print()
print("git add -A && git commit -m 'fix: remove unused state vars in IntakePage -- ESLint errors' && git push")