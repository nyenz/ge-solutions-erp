import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    data = read(path)
    if old in data:
        write(path, data.replace(old, new, 1))
    else:
        print(f"MISSING patch target in: {path}")

# ── FIX 1a: IntakePage.jsx — phone regex + hint ──────────────────
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''const PhoneInput = ({ label='PHONE NUMBER', value, onChange, onBlur, id, required, fieldError }) => {
    const inputId = id || 'phi';
    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
            </div>
            <input id={inputId} type="tel" value={value}
                onChange={e => onChange(e.target.value.replace(/[^0-9\s/]/g, ''))}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                placeholder="0712 345 678"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`} />
            {fieldError && <span className={styles.fieldError}>{fieldError}</span>}
        </div>
    );
};''',
    '''const PhoneInput = ({ label='PHONE NUMBER', value, onChange, onBlur, id, required, fieldError }) => {
    const inputId = id || 'phi';
    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
            </div>
            <input id={inputId} type="tel" value={value}
                onChange={e => onChange(e.target.value.replace(/[^0-9\s/]/g, ''))}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                placeholder="0712 345 678"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`} />
            {fieldError && <span className={styles.fieldError}>{fieldError}</span>}
            <span className={styles.fieldHint}>Use &#39;/&#39; to separate multiple numbers (e.g. 077... / 075...)</span>
        </div>
    );
};'''
)

# ── FIX 1b: FolderPage.jsx — phone regex + hint ──────────────────
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, onBlur, id, required, fieldError }) => {
    const [raw, setRaw] = useState(() => value || '');
    const inputId = id || 'phi_phone';
    const isDual  = raw.includes('/');
    const handleChange = (e) => {
        let v = e.target.value.replace(/[^0-9\s/]/g, '').replace(/[/]+/g, '/');
        if (v.startsWith('/')) v = v.slice(1);
        setRaw(v); onChange(v);
    };''',
    '''const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, onBlur, id, required, fieldError }) => {
    const [raw, setRaw] = useState(() => value || '');
    const inputId = id || 'phi_phone';
    const isDual  = raw.includes('/');
    const handleChange = (e) => {
        let v = e.target.value.replace(/[^0-9\s/]/g, '').replace(/[/]+/g, '/');
        if (v.startsWith('/')) v = v.slice(1);
        setRaw(v); onChange(v);
    };'''
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};

const NINInput''',
    '''            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
            <span className={styles.inputHint}>Use &#39;/&#39; to separate multiple numbers (e.g. 077... / 075...)</span>
        </div>
    );
};

const NINInput'''
)

# ── FIX 2: LedgerPage.module.css — clean jointBadge ─────────────
patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.module.css',
    '''.jointBadge {
    background: var(--orange-dim);
    border: 1.5px solid var(--orange);
    color: var(--orange);
    padding: clamp(3px, 0.4vw, 5px) clamp(5px, 0.7vw, 8px);
    border-radius: var(--radius-sm);
    display: flex;
    flex-direction: column;
    gap: 4px;
    gap: clamp(4px, 0.5vw, 6px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    letter-spacing: 1px;
    white-space: nowrap;
    flex-shrink: 0;
    box-shadow: 0 0 10px rgba(238, 140, 58, 0.2);
    animation: badgePulse 2.2s ease-in-out infinite;
}''',
    '''.jointBadge {
    background: transparent;
    border: none;
    color: var(--orange);
    padding: clamp(2px, 0.3vw, 4px) 0;
    display: flex;
    align-items: center;
    gap: clamp(4px, 0.5vw, 6px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    letter-spacing: 1px;
    white-space: nowrap;
    flex-shrink: 0;
}'''
)

# ── FIX 3: LedgerPage.jsx — add ACTIVE TITLES filter + fix UNPAID ─
patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.jsx',
    '''    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES' },
        { key: 'PAID',     label: 'PAID TITLES'  },
        { key: 'BACKLOG',  label: 'BACKLOG'       },
        { key: 'DEBTORS',  label: 'UNPAID'        },
        { key: 'CRITICAL', label: 'CRITICAL'      },
    ];''',
    '''    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES'  },
        { key: 'PAID',     label: 'PAID TITLES'   },
        { key: 'BACKLOG',  label: 'BACKLOG'        },
        { key: 'ACTIVE',   label: 'ACTIVE TITLES'  },
        { key: 'DEBTORS',  label: 'UNPAID'         },
        { key: 'CRITICAL', label: 'CRITICAL'       },
    ];'''
)

patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.jsx',
    '''        if (activeFilter === 'PAID')    filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isBacklog);
        if (activeFilter === 'BACKLOG') filtered = filtered.filter(p => p.isBacklog);
        if (activeFilter === 'DEBTORS')   filtered = filtered.filter(p => p.amountPaid < p.totalCost && !p.isBacklog);
        if (activeFilter === 'CRITICAL')  filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25 && !p.isBacklog);''',
    '''        if (activeFilter === 'PAID')     filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isBacklog);
        if (activeFilter === 'BACKLOG')  filtered = filtered.filter(p => p.isBacklog);
        if (activeFilter === 'ACTIVE')   filtered = filtered.filter(p => !p.isBacklog);
        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.amountPaid < p.totalCost);
        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25 && !p.isBacklog);'''
)

# ── FIX 4: StaffController.java — allow ROLE_ADMIN to getAllOperators ──
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/StaffController.java',
    '''    /**
     * OPERATOR DIRECTORY
     * Returns the full list of staff for the Governance Ledger.
     */
    @GetMapping("/all")
    public ResponseEntity<List<User>> getAllOperators() {
        return ResponseEntity.ok(staffService.getAllOperators());
    }''',
    '''    /**
     * OPERATOR DIRECTORY
     * Returns the full list of staff for the Governance Ledger.
     * ACCESS: Root and Admin (Admins need this to filter audit logs).
     */
    @GetMapping("/all")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<List<User>> getAllOperators() {
        return ResponseEntity.ok(staffService.getAllOperators());
    }'''
)

# ── FIX 5a: SettingsPage.jsx — fix isActive check on operator cards ──
patch(
    'erp-frontend/src/pages/settings/SettingsPage.jsx',
    '''                                            <div className={styles.opAvatar} aria-hidden="true">
                                                    {op.username.charAt(0).toUpperCase()}
                                                    <div className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} />
                                                </div>''',
    '''                                            <div className={styles.opAvatar} aria-hidden="true">
                                                    {op.username.charAt(0).toUpperCase()}
                                                    <div className={`${styles.statusDot} ${(op.isActive || op.active) ? styles.dotGreen : styles.dotRed}`} />
                                                </div>'''
)

patch(
    'erp-frontend/src/pages/settings/SettingsPage.jsx',
    '''                                                    <button className={`${styles.killSwitchBtn} ${op.active ? styles.killSwitchActive : styles.killSwitchInactive}`} onClick={() => handleStatusToggle(op.username, op.active)} aria-label={op.active ? `Suspend ${op.username}` : `Restore ${op.username}`}>''',
    '''                                                    <button className={`${styles.killSwitchBtn} ${(op.isActive || op.active) ? styles.killSwitchActive : styles.killSwitchInactive}`} onClick={() => handleStatusToggle(op.username, (op.isActive || op.active))} aria-label={(op.isActive || op.active) ? `Suspend ${op.username}` : `Restore ${op.username}`}>'''
)

patch(
    'erp-frontend/src/pages/settings/SettingsPage.jsx',
    '''    const handleStatusToggle = async (opUsername, isActive) => {
        const action = isActive ? 'SUSPEND' : 'RESTORE';
        const ok = await confirm(`${action} OPERATOR`, `Physically ${action.toLowerCase()} access for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.toggleOperator(opUsername, !isActive); fetchOperators(); }
        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }
    };''',
    '''    const handleStatusToggle = async (opUsername, currentlyActive) => {
        const action = currentlyActive ? 'SUSPEND' : 'RESTORE';
        const ok = await confirm(`${action} OPERATOR`, `Physically ${action.toLowerCase()} access for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.toggleOperator(opUsername, !currentlyActive); fetchOperators(); }
        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }
    };'''
)

# ── FIX 5b: SettingsPage.jsx — fix dimmed card class check ──────
patch(
    'erp-frontend/src/pages/settings/SettingsPage.jsx',
    '''                                    <div key={op.id} className={`${styles.opCard} ${!op.active ? styles.cardDimmed : ''}`} role="listitem">''',
    '''                                    <div key={op.id} className={`${styles.opCard} ${!(op.isActive || op.active) ? styles.cardDimmed : ''}`} role="listitem">'''
)

print("=== ALL 5 FIXES APPLIED ===")
