import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== STARTING FINANCIAL WORKFLOW REWIRE ===")

# ============================================================
# 1. FOLDER PAGE (Row ID + Hash Scroll Logic)
# ============================================================
fp_path = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
fp_content = read(fp_path)

# Update the hash check to allow 'payment-'
fp_content = re.sub(
    r"if \(hash === 'payments' \|\| hash === 'finance' \|\| hash === 'financials'\) \{",
    "if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-')) {",
    fp_content
)

# Inject the smart scroll-and-highlight logic
scroll_logic = """if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }"""
fp_content = re.sub(
    r"const el = document\.getElementById\('paymentHistorySection'\);\s*if \(el\) el\.scrollIntoView\(\{ behavior: 'smooth', block: 'start' \}\);",
    scroll_logic,
    fp_content
)

# Add the HTML ID to the payment row
fp_content = fp_content.replace(
    "<div key={pay.id || i} className={styles.paymentRow}",
    "<div key={pay.id || i} id={`payment-${pay.id}`} className={styles.paymentRow}"
)
write(fp_path, fp_content)

# Add highlight CSS class
css_path = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
css_content = read(css_path)
if '.highlightRow' not in css_content:
    css_content += "\n/* --- HIGHLIGHT ROW --- */\n.highlightRow {\n    background: rgba(238, 140, 58, 0.25) !important;\n    border-left-color: var(--orange) !important;\n    box-shadow: 0 0 15px rgba(238, 140, 58, 0.4);\n    transition: background 0.5s ease-out, box-shadow 0.5s ease-out;\n}\n"
    write(css_path, css_content)


# ============================================================
# 2. PAYMENTS PAGE (Point links to specific payment rows)
# ============================================================
pp_path = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
pp_content = read(pp_path)

# Change #payments to #payment-{id}
pp_content = pp_content.replace(
    "navigate(`/folder/${pay.projectId}#payments`)",
    "navigate(`/folder/${pay.projectId}#payment-${pay.id}`)"
)
# Change Enter key navigation
pp_content = pp_content.replace(
    "navigate(`/folder/${pay.projectId}`); }}}>",
    "navigate(`/folder/${pay.projectId}#payment-${pay.id}`); }}}>"
)
write(pp_path, pp_content)


# ============================================================
# 3. RECOVERY PORTAL (Remove modals, navigate to Financials)
# ============================================================
rp_path = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
rp_content = read(rp_path)

# Point all PAY buttons to the folder's financials tab
rp_content = rp_content.replace(
    "onClick={() => setPayModal({ open: true, plot })}",
    "onClick={() => navigate(`/folder/${plot.projectId}#financials`)}"
)
rp_content = rp_content.replace(
    "onClick={() => setMonthlyModal({ open: true, plot })}",
    "onClick={() => navigate(`/folder/${plot.projectId}#financials`)}"
)

# Remove local states for paying/modals
rp_content = re.sub(r"const \[payModal,\s*setPayModal\].*?\n", "", rp_content)
rp_content = re.sub(r"const \[paying,\s*setPaying\].*?\n", "", rp_content)
rp_content = re.sub(r"const \[monthlyModal,\s*setMonthlyModal\].*?\n", "", rp_content)

# Remove the handleRecordPayment function completely
rp_content = re.sub(r"const handleRecordPayment = async.*?finally \{\s*setPaying\(false\);\s*\}\s*\};", "", rp_content, flags=re.DOTALL)

# Remove the JSX Modal tags from the bottom of the return statement
rp_content = re.sub(r"\{\/\* PAYMENT MODAL \*\/\}.*?</HardwareModal>", "", rp_content, flags=re.DOTALL)
rp_content = re.sub(r"\{\/\* MONTHLY INSTALMENT MODAL \*\/\}.*?</HardwareModal>", "", rp_content, flags=re.DOTALL)
rp_content = re.sub(r"<PaymentModal[\s\S]*?paying=\{paying\}[\s\S]*?/>", "", rp_content)
rp_content = re.sub(r"<MonthlyInstallmentModal[\s\S]*?paying=\{paying\}[\s\S]*?/>", "", rp_content)

# Remove the actual definitions of the Modal components at the top of the file
# We slice out everything from "PAYMENT TYPE MODAL" up to "STORAGE FEE INLINE CONTROLS"
rp_content = re.sub(r"// ── PAYMENT TYPE MODAL ──.*?// ── STORAGE FEE INLINE CONTROLS ──", "// ── STORAGE FEE INLINE CONTROLS ──", rp_content, flags=re.DOTALL)

write(rp_path, rp_content)

print("\n=== Done! Everything has been securely wired. ===")
print("Run: git add -A && git commit -m 'wire all financial actions to FolderPage Financials tab' && git push")