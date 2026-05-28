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

print("=== STARTING FINAL POLISH FOR RECOVERY CARD SIZES ===")

css_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css')

# 1. Increase Card Header Padding for comfortable vertical spacing
patch(
    css_path,
    '''    padding: clamp(10px,1.2vw,14px) clamp(12px,1.5vw,18px);''',
    '''    padding: clamp(14px, 1.8vw, 22px) clamp(16px, 2.2vw, 28px);''',
    'CSS: Increase Card Header padding'
)

# 2. Increase Plot ID Font Size
patch(
    css_path,
    '''.plotId {
    font-family:\'Space Mono\',monospace;
    color: var(--orange);
    font-size: clamp(12px,1.3vw,15px);''',
    '''.plotId {
    font-family:\'Space Mono\',monospace;
    color: var(--orange);
    font-size: clamp(14px, 1.6vw, 18px);''',
    'CSS: Increase Plot ID font size'
)

# 3. Increase Owner Name Font Size
patch(
    css_path,
    '''.ownerLine {
    font-family:\'DM Sans\',sans-serif; color:rgba(255,255,255,0.9);
    font-size: clamp(12px,1.3vw,14px);''',
    '''.ownerLine {
    font-family:\'DM Sans\',sans-serif; color:rgba(255,255,255,0.9);
    font-size: clamp(14px, 1.5vw, 17px);''',
    'CSS: Increase Owner Name font size'
)

# 4. Increase Phone Number Font Size & Contrast
patch(
    css_path,
    '''.phoneLine {
    font-family:\'Space Mono\',monospace;
    color: rgba(255,255,255,0.75);
    font-size: clamp(11px,1.1vw,13px);''',
    '''.phoneLine {
    font-family:\'Space Mono\',monospace;
    color: rgba(255,255,255,0.85);
    font-size: clamp(13px, 1.4vw, 15px);''',
    'CSS: Increase Phone Number font size'
)

# 5. Increase Debt Value Font Size
patch(
    css_path,
    '''.balanceVal {
    font-family:\'Space Mono\',monospace;
    font-size: clamp(12px,1.3vw,14px); font-weight:900; color:#fff;
}''',
    '''.balanceVal {
    font-family:\'Space Mono\',monospace;
    font-size: clamp(14px, 1.6vw, 18px); font-weight:900; color:#fff;
}''',
    'CSS: Increase Debt Value font size'
)

# 6. Increase Log Call Button Font Size
patch(
    css_path,
    '''.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:\'DM Sans\',sans-serif; font-weight:900;
    font-size: clamp(10px,1vw,12px);''',
    '''.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:\'DM Sans\',sans-serif; font-weight:900;
    font-size: clamp(11px, 1.2vw, 13px);''',
    'CSS: Increase Button font size'
)

print("\n=== FINAL RECOVERY POLISH COMPLETE ===")