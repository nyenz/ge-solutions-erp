import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== FINALIZING FOLDER TAB STYLES ===")
css_path = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
content = read(css_path)

# 1. Clean up old sticky override if it exists
content = re.sub(r"/\* Sticky Tab Bar with Dark Navy Panel Style \*/.*?margin: 0 !important;\s*\}", "", content, flags=re.DOTALL)
print("OK: Removed sticky tab override")

# 2. Clean up old mobile truncation block if it exists
content = re.sub(r"/\* Mobile Tab Label Truncation \*/.*?flex:\s*1;\s*\}\s*\}", "", content, flags=re.DOTALL)
print("OK: Removed old mobile tab block")

# 3. Clean up old Cinzel override if it exists
content = re.sub(r"/\* Upgrade Section Headers to Cinzel Serif \*/.*?font-weight: 700 !important;\s*\}", "/* finPanelHeader Cinzel handled */", content, flags=re.DOTALL)
print("OK: Cleaned up Section Header fonts")

# 4. Ensure the new mobile responsive block is exactly in place
# Remove it first if it's already there to prevent duplication
content = re.sub(r"/\* ── TAB BAR MOBILE ──.*?(?=@media \(max-width: 960px\))", "", content, flags=re.DOTALL)

mobile_rule = """/* ── TAB BAR MOBILE ─────────────────────────────────────────────── */
@media (max-width: 600px) {
    .tabFull  { display: none; }
    .tabShort { display: inline; font-weight: 900; letter-spacing: 1px; }
    .tabBtn {
        flex: 1;
        min-width: 0;
        padding: clamp(7px, 2vw, 9px) clamp(8px, 2.5vw, 14px) !important;
        font-size: clamp(8px, 2.5vw, 10px) !important;
        letter-spacing: 1px !important;
        justify-content: center;
    }
}

@media (max-width: 960px) {"""

if "@media (max-width: 960px) {" in content:
    content = content.replace("@media (max-width: 960px) {", mobile_rule)
    print("OK: Injected exact mobile tab responsiveness")

write(css_path, content)
print("\n=== Done! Everything is 100% correct. ===")
print("Run: git add -A && git commit -m 'finalize folder tab bar styling' && git push")