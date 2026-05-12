import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING (patch target not found): {path}")
        return
    write(path, content.replace(old, new, 1))

# ============================================================
# FIX: FiHome and FiArchive missing from FolderPage.jsx import
# Root cause: icons used in payment modal JSX but not imported
# ============================================================

print("=== FIX: FolderPage.jsx missing icon imports ===")

FOLDER_PAGE = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

patch(
    FOLDER_PAGE,
    "    FiDollarSign, FiActivity\n} from 'react-icons/fi';",
    "    FiDollarSign, FiActivity, FiHome, FiArchive\n} from 'react-icons/fi';"
)

print("\n=== ALL FIXES DONE ===")
print("Now run: git add -A && git commit -m 'fix: add missing FiHome FiArchive imports in FolderPage' && git push")