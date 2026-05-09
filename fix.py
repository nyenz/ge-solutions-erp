import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK     {label}")
    else:
        print(f"MISSING  {label}")


# =============================================================================
# FIX 1: FolderPage.jsx -- duplicate onBlur on PhoneInput
# The PhoneInput component already has onBlur built-in.
# The JSX was passing onBlur twice which causes a build error.
# =============================================================================

FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

old_phone_input = '''                <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />'''

new_phone_input = '''                <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} required />'''

# The real fix: remove the duplicate onBlur from PhoneInput definition in FolderPage
# The PhoneInput component adds onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
# but the prop name conflicts. Let's look at the actual PhoneInput in FolderPage and fix the duplicate.

content = read(FOLDER_JSX)

# Fix the duplicate onBlur in the PhoneInput component definition inside FolderPage
old_phone_component = '''    const handleBlur = () => {
        if (!raw.trim()) return;
        const f = formatPhoneEntry(raw);
        if (f) { setRaw(f); onChange(f); }
    };
    return (
        <div className={`${styles.hwInputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={`${styles.assistBadge} ${isDual ? styles.assistBadgeDual : ''}`}>{isDual ? 'DUAL' : 'TEL'}</span>
            </div>
            <input id={inputId} type="tel" value={raw} onChange={handleChange} onBlur={handleBlur}
                placeholder="0712 345 678  ·  dual: 0712.../0701..." inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                autoComplete="tel-national" />
            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );'''

new_phone_component = '''    const handleBlur = () => {
        if (!raw.trim()) return;
        const f = formatPhoneEntry(raw);
        if (f) { setRaw(f); onChange(f); }
        if (onBlur) onBlur(raw);
    };
    return (
        <div className={`${styles.hwInputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={`${styles.assistBadge} ${isDual ? styles.assistBadgeDual : ''}`}>{isDual ? 'DUAL' : 'TEL'}</span>
            </div>
            <input id={inputId} type="tel" value={raw} onChange={handleChange} onBlur={handleBlur}
                placeholder="0712 345 678  ·  dual: 0712.../0701..." inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                autoComplete="tel-national" />
            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );'''

patch(FOLDER_JSX, old_phone_component, new_phone_component, "FolderPage.jsx: fix duplicate onBlur on PhoneInput")


# =============================================================================
# FIX 2: FolderPage.jsx + IntakePage.jsx
# react-router-dom v7 exports useBlocker directly (no unstable_ prefix).
# Replace: unstable_useBlocker as useBlocker  ->  useBlocker
# =============================================================================

INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Fix FolderPage import
patch(FOLDER_JSX,
    "import { useParams, useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';",
    "import { useParams, useNavigate, useBeforeUnload, useBlocker } from 'react-router-dom';",
    "FolderPage.jsx: remove unstable_ prefix from useBlocker"
)

# Fix IntakePage import
patch(INTAKE_JSX,
    "import { useNavigate, useBeforeUnload, unstable_useBlocker as useBlocker } from 'react-router-dom';",
    "import { useNavigate, useBeforeUnload, useBlocker } from 'react-router-dom';",
    "IntakePage.jsx: remove unstable_ prefix from useBlocker"
)

print("\n--- All patches applied ---")
print()
print("git add -A && git commit -m 'fix: duplicate onBlur + useBlocker v7 compat' && git push")