# PATH: fix.py
import os

def patch(path, old, new, label):
    if not os.path.isfile(path):
        print(f"MISSING: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: {label}")
    elif new in content:
        print(f"SKIP (already applied): {label}")
    else:
        print(f"FAIL: {label}")

# ── 1. PATCH JSX ──
JSX_PATH = "erp-frontend/src/pages/login/LoginPage.jsx"
OLD_JSX = """                    {recoverySuccess ? (
                        <div className={styles.successScreen}>
                            <FiCheckCircle size={50} color="#10b981" />
                            <p className={styles.successMsg}>{recoverySuccess}</p>
                            <HardwareButton onClick={() => setIsRecovering(false)}>Return to Login</HardwareButton>
                        </div>
                    ) : ("""

NEW_JSX = """                    {recoverySuccess ? (
                        <div className={styles.successScreen}>
                            <div className={styles.successIconWrap}>
                                <FiCheckCircle size={32} color="#10b981" />
                            </div>
                            <p className={styles.successMsg}>{recoverySuccess}</p>
                            <div className={styles.btnWrap} style={{ marginTop: '10px' }}>
                                <HardwareButton onClick={() => { setIsRecovering(false); setRecoverySuccess(''); }}>Return to Login</HardwareButton>
                            </div>
                        </div>
                    ) : ("""
patch(JSX_PATH, OLD_JSX, NEW_JSX, "PATCH 1/2: Update LoginPage.jsx layout")


# ── 2. PATCH CSS ──
CSS_PATH = "erp-frontend/src/pages/login/LoginPage.module.css"
with open(CSS_PATH, "r", encoding="utf-8") as f:
    css_content = f.read()

NEW_CSS = """
/* --- RECOVERY SUCCESS SCREEN --- */
.successScreen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(14px, 2vw, 20px);
    padding: clamp(20px, 3vw, 30px) 10px;
    text-align: center;
    background: rgba(16, 185, 129, 0.05);
    border: 1.5px solid rgba(16, 185, 129, 0.25);
    border-radius: var(--input-radius, 8px);
    box-shadow: inset 0 0 30px rgba(16, 185, 129, 0.05);
    animation: successFadeIn 0.4s cubic-bezier(0.2, 1, 0.3, 1) both;
}
@keyframes successFadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
.successIconWrap {
    width: clamp(50px, 7vw, 64px);
    height: clamp(50px, 7vw, 64px);
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    margin-bottom: 5px;
    border: 1px solid rgba(16, 185, 129, 0.4);
}
.successMsg {
    font-family: 'Space Mono', monospace;
    font-size: clamp(10px, 1.2vw, 12px);
    font-weight: 700;
    color: #34d399;
    line-height: 1.6;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0;
    text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}
"""
if ".successScreen {" not in css_content:
    with open(CSS_PATH, "a", encoding="utf-8", newline="\n") as f:
        f.write(NEW_CSS)
    print("OK: PATCH 2/2: Appended success styling to LoginPage.module.css")
else:
    print("SKIP: PATCH 2/2: CSS already present.")