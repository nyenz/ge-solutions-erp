import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== STARTING RECOVERY PORTAL FIXES ===")

path_recovery = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content_rec = read(path_recovery)

# 1. Completely remove the INSTALMENT button
# This uses regex to find the entire {isAdmin && ( ... INSTALMENT ... )} block and erase it
content_rec = re.sub(
    r'\{isAdmin && \(\s*<button className=\{styles\.payBtnMonthly\}[^>]+>\s*<FiRepeat[^>]+>\s*INSTALMENT\s*</button>\s*\)\}',
    '',
    content_rec,
    flags=re.IGNORECASE | re.DOTALL
)

# 2. Ensure "PAY" button for ACTIVE plots correctly navigates to ?action=pay
content_rec = re.sub(
    r'<button className=\{styles\.payBtnTitle\}\s+onClick=\{\(\) => navigate\([^)]+\)\}>\s*<FiDollarSign size=\{12\} /> PAY\s*</button>',
    '''<button className={styles.payBtnTitle}
                                                        onClick={() => navigate(`/folder/${plot.projectId}?action=pay#financials`)}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>''',
    content_rec,
    flags=re.IGNORECASE | re.DOTALL
)

# 3. Ensure "PAY" button for BACKLOG plots correctly navigates to ?action=pay
content_rec = re.sub(
    r'<button className=\{\`\$\{styles\.payBtnTitle\} \$\{styles\.payBtnBacklog\}\`\}\s+onClick=\{\(\) => navigate\([^)]+\)\}>\s*<FiZap size=\{12\} /> PAY\s*</button>',
    '''<button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => navigate(`/folder/${plot.projectId}?action=pay#financials`)}>
                                                        <FiZap size={12} /> PAY
                                                    </button>''',
    content_rec,
    flags=re.IGNORECASE | re.DOTALL
)

write(path_recovery, content_rec)

print("\n=== RECOVERY PORTAL FIXED SUCCESSFULLY ===")
print("Run: git add -A && git commit -m 'fix: remove instalment btn and link pay to folder modal' && git push")