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

print("=== STARTING STICKY TAB FIX ===")

path_css = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
content_css = read(path_css)

# 1. Strip ALL stickiness from the pipelineHUD
content_css = re.sub(r'(?<=pipelineHUD \{)([\s\S]*?)position:\s*sticky;[\s\S]*?-webkit-backdrop-filter:[^;]+;', r'\1', content_css)

# 2. Strip ALL stickiness from the terminalHeader 
content_css = re.sub(r'(?<=terminalHeader \{)([\s\S]*?)position:\s*sticky;[\s\S]*?z-index:\s*49;', r'\1', content_css)

# 3. Strip out the huge scroll-margins from the previous fix
content_css = re.sub(r'scroll-margin-top:\s*clamp[^;]+;', '', content_css)
content_css = re.sub(r'scroll-margin-top:\s*60px;', '', content_css)

# 4. Strictly configure the TabBar to be the ONLY sticky element
content_css = re.sub(r'\.tabBar\s*\{[^}]*\}', 
'''.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 8px;
    padding-top: 8px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: -15px; /* Sticks precisely to the top edge when scrolling */
    z-index: 100;
    background: rgba(244, 242, 239, 0.98); /* Blends perfectly with cream background */
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 0 0 8px 8px;
}''', content_css)

# 5. Add a subtle margin so when it auto-scrolls to the Financials section, 
# the new sticky tab bar doesn't cover the title.
content_css = re.sub(r'(\.hwPanel\s*\{[^}]*)', r'\1\n    scroll-margin-top: 50px;', content_css)

# Clean up any potential duplicate scroll-margins just in case
content_css = re.sub(r'(scroll-margin-top:\s*50px;\s*){2,}', 'scroll-margin-top: 50px;\n', content_css)

write(path_css, content_css)

print("\n=== STICKY TABS FIXED SUCCESSFULLY ===")
print("Run: git add -A && git commit -m 'fix: isolate stickiness to tab bar only' && git push")