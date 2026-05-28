# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.strip() + '\n')
    print(f"OK (OVERWRITTEN): {path}")

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK (PATCHED): {label}")
    else:
        print(f"MISSING: {label}")

BASE = os.path.dirname(os.path.abspath(__file__))

print("=== ENFORCING UNIFORM FONT SIZES ON RECOVERY PORTAL ===")

css_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css')
content = read(css_path)

# 1. Replace all local font variables with the official Ledger/App variables
old_vars = """    --fs-h1:    clamp(17px,2.4vw,23px);
    --fs-sm:    clamp(9px,0.9vw,11px);
    --fs-xs:    clamp(8px,0.8vw,9px);
    --fs-2xs:   clamp(7px,0.72vw,8px);
    --fs-mono:  clamp(10px,1vw,12px);
    --fs-btn:   clamp(8px,0.85vw,10px);
    --fs-note:  clamp(9px,0.9vw,11px);"""

new_vars = """    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-th:     clamp(8px,  0.85vw, 10px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);"""

if old_vars in content:
    content = content.replace(old_vars, new_vars)
    print("OK: Replaced with official App-wide font variables")
else:
    print("MISSING: Font variables block mismatch")

# 2. Map Plot ID to the official Plot ID variable
content = content.replace(
    "font-size: clamp(14px, 1.6vw, 18px);",
    "font-size: var(--fs-value);"
)

# 3. Map Owner Name to the official Row Text variable
content = content.replace(
    "font-size: clamp(14px, 1.5vw, 17px);",
    "font-size: var(--fs-td);"
)

# 4. Map Phone Number to the official Metadata variable
content = content.replace(
    "font-size: clamp(13px, 1.4vw, 15px);",
    "font-size: var(--fs-meta);"
)

# 5. Map Debt Value to the official Row Text variable
content = content.replace(
    "font-size: clamp(14px, 1.6vw, 18px);",
    "font-size: var(--fs-td);"
)

# 6. Map Button Font to the official Button variable
content = content.replace(
    "font-size: clamp(11px, 1.2vw, 13px);",
    "font-size: var(--fs-btn);"
)

write(css_path, content)
print("=== UNIFORMITY RESTORED ===")