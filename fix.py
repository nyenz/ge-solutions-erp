# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("=== ADDING CARD SPACING ON RECOVERY PORTAL ===")

path_recovery_css = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'
data_recovery_css = read(path_recovery_css)

old_section_group = """/* ── SECTION GROUPS ── */
.sectionGroup { margin-bottom:clamp(24px, 3.2vw, 40px); }"""

new_section_group = """/* ── SECTION GROUPS ── */
.sectionGroup {
    margin-bottom: clamp(24px, 3.2vw, 40px);
    display: flex;
    flex-direction: column;
    gap: clamp(12px, 1.8vw, 20px);
}"""

if old_section_group in data_recovery_css:
    data_recovery_css = data_recovery_css.replace(old_section_group, new_section_group)
    write(path_recovery_css, data_recovery_css)
    print("OK: RecoveryPortal.module.css .sectionGroup gap added")
else:
    # Fallback to try a single-line string search in case of carriage return differences
    old_section_group_alt = ".sectionGroup { margin-bottom:clamp(24px, 3.2vw, 40px); }"
    if old_section_group_alt in data_recovery_css:
        data_recovery_css = data_recovery_css.replace(old_section_group_alt, """.sectionGroup {
    margin-bottom: clamp(24px, 3.2vw, 40px);
    display: flex;
    flex-direction: column;
    gap: clamp(12px, 1.8vw, 20px);
}""")
        write(path_recovery_css, data_recovery_css)
        print("OK: RecoveryPortal.module.css .sectionGroup gap added (alt path)")
    else:
        print("WARNING: RecoveryPortal.module.css target .sectionGroup style not found")

print("=== DONE ===")