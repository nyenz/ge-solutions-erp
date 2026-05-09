import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK  {label}")
    else:
        print(f"MISSING  {label}")

fp = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Fix the note modal title - was "ARCHIVE LOG ENTRY", should be "ADD NOTE"
patch(fp,
    'title="ARCHIVE LOG ENTRY"',
    'title="ADD NOTE"',
    "FolderPage: note modal title")

print("\nDone.")
print("git add -A && git commit -m 'fix note modal title' && git push")