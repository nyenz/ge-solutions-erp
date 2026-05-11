import os, re

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

# ================================================================
# LoginPage: remove all guard-related code (it was never fully wired)
# ================================================================
LOGIN = 'erp-frontend/src/pages/login/LoginPage.jsx'
content = read(LOGIN)

# Remove the UnsavedChangesModal JSX if it references undefined vars
content = re.sub(
    r'\s*<UnsavedChangesModal[^/]*/>\n?',
    '\n',
    content
)

# Remove guard hook calls that produce unused/undefined vars
content = re.sub(
    r'\s*const isDirty\s*=.*?;\n',
    '\n',
    content
)
content = re.sub(
    r'\s*const \{ blocked: guardOpen.*?\} = useRouterBlock\(.*?\);\n',
    '\n',
    content
)
content = re.sub(
    r'\s*const \{ blocked: guardOpen.*?\}.*?useRouterBlock.*?;\n',
    '\n',
    content
)

# Remove beforeunload effect that references isDirty
content = re.sub(
    r'    useEffect\(\(\) => \{\s*if \(!isDirty.*?return.*?\}.*?\}, \[isDirty.*?\]\);\n',
    '',
    content,
    flags=re.DOTALL
)

# Remove unused imports
for imp in [
    "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n",
    "import { useRouterBlock } from '../../components/common/RouterBlocker';\n",
]:
    content = content.replace(imp, '')

write(LOGIN, content)
print("LoginPage: cleaned up undefined guard vars")

# ================================================================
# LedgerPage: same cleanup
# ================================================================
LEDGER = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'
content = read(LEDGER)

content = re.sub(r'\s*<UnsavedChangesModal[^/]*/>\n?', '\n', content)
content = re.sub(r'\s*const isDirty\s*=.*?;\n', '\n', content)
content = re.sub(r'\s*const \{ blocked: guardOpen.*?\} = useRouterBlock\(.*?\);\n', '\n', content)
content = re.sub(
    r'    useEffect\(\(\) => \{\s*if \(!isDirty.*?return.*?\}.*?\}, \[isDirty.*?\]\);\n',
    '', content, flags=re.DOTALL
)
for imp in [
    "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n",
    "import { useRouterBlock } from '../../components/common/RouterBlocker';\n",
]:
    content = content.replace(imp, '')

write(LEDGER, content)
print("LedgerPage: cleaned up undefined guard vars")

# ================================================================
# PaymentsPage: same cleanup
# ================================================================
PAYMENTS = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
content = read(PAYMENTS)

content = re.sub(r'\s*<UnsavedChangesModal[^/]*/>\n?', '\n', content)
content = re.sub(r'\s*const isDirty\s*=.*?;\n', '\n', content)
content = re.sub(r'\s*const \{ blocked: guardOpen.*?\} = useRouterBlock\(.*?\);\n', '\n', content)
for imp in [
    "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n",
    "import { useRouterBlock } from '../../components/common/RouterBlocker';\n",
]:
    content = content.replace(imp, '')

write(PAYMENTS, content)
print("PaymentsPage: cleaned up undefined guard vars")

print("\nAll done. Run: git add -A && git commit -m 'fix: remove broken guard vars causing app crash' && git push")