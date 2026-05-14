# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def delete_file(path):
    try:
        os.remove(path)
        print(f"DELETED: {path}")
    except FileNotFoundError:
        print(f"ALREADY DELETED (Not Found): {path}")
    except Exception as e:
        print(f"FAILED TO DELETE {path}: {e}")

print("=== STARTING DEAD CODE CLEANUP AND LANGUAGE FIXES ===")

# ============================================================
# 1. DELETE UNUSED/DEAD FRONTEND COMPONENTS
# ============================================================
# These files are defined but never imported anywhere.
dead_files = [
    'erp-frontend/src/pages/Dashboard/SharedWidgets.jsx',
    'erp-frontend/src/pages/Dashboard/SharedWidgets.module.css',
    'erp-frontend/src/components/ui/HardwareField.jsx',
    'erp-frontend/src/components/ui/HardwareField.module.css'
]

for file_path in dead_files:
    delete_file(file_path)


# ============================================================
# 2. MANAGER TERMINAL LANGUAGE FIX
# ============================================================
path_mgr = 'erp-frontend/src/pages/Dashboard/ManagerTerminal.jsx'
content_mgr = read(path_mgr)

# Change 'NEW INTAKE' to 'NEW PLOT' to match standard naming
if 'NEW INTAKE</button>' in content_mgr:
    content_mgr = content_mgr.replace('NEW INTAKE</button>', 'NEW PLOT</button>')
    write(path_mgr, content_mgr)
else:
    print(f"MISSING OR ALREADY APPLIED: Language fix in {path_mgr}")


print("\n=== CLEANUP COMPLETED SUCCESSFULLY ===")
print("Run: git add -A && git commit -m 'chore: remove dead UI components and unify New Plot language' && git push")