# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("=== REFINING COCKPIT SPACING & MOBILE LAYERING ===")

# 1. RecoveryPortal.module.css - Reduce gap & prevent label stretching
path_recovery_css = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'
data_recovery_css = read(path_recovery_css)

old_section_group_layout = """/* ── SECTION GROUPS ── */
.sectionGroup {
    margin-bottom: clamp(24px, 3.2vw, 40px);
    display: flex;
    flex-direction: column;
    gap: clamp(12px, 1.8vw, 20px);
}"""

new_section_group_layout = """/* ── SECTION GROUPS ── */
.sectionGroup {
    margin-bottom: clamp(24px, 3.2vw, 40px);
    display: flex;
    flex-direction: column;
    gap: clamp(8px, 1.1vw, 12px);
}"""

if old_section_group_layout in data_recovery_css:
    data_recovery_css = data_recovery_css.replace(old_section_group_layout, new_section_group_layout)
    print("OK: RecoveryPortal.module.css gap reduced")
else:
    print("WARNING: RecoveryPortal.module.css target sectionGroup layout not found")

old_section_header = """.sectionHeader {
    font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.95vw,11px);
    font-weight:900; color:#fff; text-transform:uppercase; letter-spacing:2px;
    margin-bottom:var(--gap-md);
    display:inline-flex; align-items:center; gap:8px;
    padding:clamp(5px,0.7vw,8px) clamp(10px,1.3vw,16px);
    border-radius:6px; background:rgba(26,46,48,0.75);
    border:1px solid rgba(238,140,58,0.25);
}"""

new_section_header = """.sectionHeader {
    font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.95vw,11px);
    font-weight:900; color:#fff; text-transform:uppercase; letter-spacing:2px;
    margin-bottom:var(--gap-md);
    display:inline-flex; align-items:center; gap:8px;
    padding:clamp(5px,0.7vw,8px) clamp(10px,1.3vw,16px);
    border-radius:6px; background:rgba(26,46,48,0.75);
    border:1px solid rgba(238,140,58,0.25);
    align-self: flex-start; /* Prevent stretching */
}"""

if old_section_header in data_recovery_css:
    data_recovery_css = data_recovery_css.replace(old_section_header, new_section_header)
    print("OK: RecoveryPortal.module.css label stretch fixed")
else:
    print("WARNING: RecoveryPortal.module.css target sectionHeader not found")

write(path_recovery_css, data_recovery_css)


# 2. AuditPage.module.css - High stack focus layering
path_audit_css = 'erp-frontend/src/pages/Audit/AuditPage.module.css'
data_audit_css = read(path_audit_css)

old_audit_select_wrap = """.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    overflow: visible !important;
}"""

new_audit_select_wrap = """.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    overflow: visible !important;
}
.hwSelectWrap:focus-within {
    z-index: 10000 !important;
}"""

if old_audit_select_wrap in data_audit_css:
    data_audit_css = data_audit_css.replace(old_audit_select_wrap, new_audit_select_wrap)
    write(path_audit_css, data_audit_css)
    print("OK: AuditPage.module.css active focus z-index added")
else:
    print("WARNING: AuditPage.module.css target hwSelectWrap not found")

print("=== REFINEMENT COMPLETED ===")