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

# ── FIX 1: Manager Financial Lock — disable TOTAL COST and AMOUNT PAID for non-admins ──
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''                                    <div className={styles.inputGrid3}>
                                        <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                        <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />''',
    '''                                    <div className={styles.inputGrid3}>
                                        <CurrencyInput label="TOTAL COST" value={buffer.totalCost} disabled={!isAdmin} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                        <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} disabled={!isAdmin} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />'''
)

# Update CurrencyInput component to accept and use a disabled prop
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''const CurrencyInput = ({ label, value, onChange, error, id }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.currencyTag}>UGX</span>
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                inputMode="numeric" value={display}
                onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
                onChange={e => onChange(e.target.value.replace(/\D/g,''))}
                placeholder="0" aria-invalid={error ? 'true' : 'false'} />
            {error && <span className={styles.fieldError} role="alert">{error}</span>}
        </div>
    );
};''',
    '''const CurrencyInput = ({ label, value, onChange, error, id, disabled }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.currencyTag}>UGX</span>
                {disabled && <span className={styles.autoCalcBadge} style={{color:'rgba(255,255,255,0.4)',background:'rgba(255,255,255,0.05)',borderColor:'rgba(255,255,255,0.1)'}}>LOCKED</span>}
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''} ${disabled ? styles.calcInput : ''}`}
                inputMode="numeric" value={display}
                onFocus={() => { if (!disabled) setFocused(true); }} onBlur={() => setFocused(false)}
                onChange={e => { if (!disabled) onChange(e.target.value.replace(/\D/g,'')); }}
                placeholder="0" aria-invalid={error ? 'true' : 'false'}
                disabled={disabled}
                style={disabled ? {background:'rgba(0,0,0,0.25)',color:'rgba(255,255,255,0.45)',cursor:'not-allowed',border:'1.5px solid rgba(255,255,255,0.08)'} : {}} />
            {error && <span className={styles.fieldError} role="alert">{error}</span>}
        </div>
    );
};'''
)

# ── FIX 2a: FolderPage.jsx — replace window.confirm in handleAbort ──
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn');
        if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); }
    };''',
    '''    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost. This cannot be undone.', 'warn');
        if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); }
    };'''
)

# ── FIX 2b: FolderPage.jsx — replace window.confirm in note modal close ──
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''            <HardwareModal isOpen={noteModal.open} onClose={() => {
                if (noteModal.content.trim() !== '') {
                    if (!window.confirm('Discard unsaved note?')) return;
                }
                setNoteModal({open:false, id:null, content:''});
            }} title="ADD NOTE">''',
    '''            <HardwareModal isOpen={noteModal.open} onClose={async () => {
                if (noteModal.content.trim() !== '') {
                    const ok = await confirm('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                    if (!ok) return;
                }
                setNoteModal({open:false, id:null, content:''});
            }} title="ADD NOTE">'''
)

# ── FIX 2c: IntakePage.jsx — replace window.confirm in note modal overlay close ──
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''            {noteModalOpen && (
                <div className={styles.noteModalOverlay} onClick={() => {
                    if (noteModalText.trim() !== '') {
                        if (!window.confirm('Discard unsaved note?')) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>
                    <div className={styles.noteModalBox} onClick={e => e.stopPropagation()}>
                        <div className={styles.noteModalHeader}>
                            <span>{editingNoteIdx !== null ? 'EDIT NOTE' : 'ADD NOTE'}</span>
                            <button type="button" className={styles.noteModalClose} onClick={() => {
                                if (noteModalText.trim() !== '') {
                                    if (!window.confirm('Discard unsaved note?')) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>''',
    '''            {noteModalOpen && (
                <div className={styles.noteModalOverlay} onClick={async () => {
                    if (noteModalText.trim() !== '') {
                        const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                        if (!ok) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>
                    <div className={styles.noteModalBox} onClick={e => e.stopPropagation()}>
                        <div className={styles.noteModalHeader}>
                            <span>{editingNoteIdx !== null ? 'EDIT NOTE' : 'ADD NOTE'}</span>
                            <button type="button" className={styles.noteModalClose} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''
)

# ── FIX 2d: IntakePage.jsx — replace window.confirm in note modal Cancel button ──
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
                    '''                        <button type="button" className={styles.noteModalCancel} onClick={() => {
                                if (noteModalText.trim() !== '') {
                                    if (!window.confirm('Discard unsaved note?')) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>''',
    '''                        <button type="button" className={styles.noteModalCancel} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''
)

# ── FIX 2e: IntakePage.jsx — add useConfirm hook and ConfirmModal import/usage ──
# Add the useConfirm hook inside IntakePage (after the component opens)
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''// ── MAIN COMPONENT ────────────────────────────────────────────────
const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const IntakePage = () => {
    const navigate = useNavigate();
    const { toasts, toast, dismissToast } = useToast();''',
    '''// ── CONFIRM HOOK (mirrors FolderPage pattern) ─────────────────────
const useIntakeConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') =>
        new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback((answer) => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState: state, confirm, handleAnswer };
};

const IntakeConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    return (
        <div style={{
            position:'fixed',inset:0,zIndex:99998,
            background:'rgba(10,20,22,0.82)',backdropFilter:'blur(6px)',
            display:'flex',alignItems:'center',justifyContent:'center',padding:24
        }} role="dialog" aria-modal="true">
            <div style={{
                background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                border:'1.5px solid rgba(238,140,58,0.35)',borderRadius:12,
                maxWidth:460,width:'100%',overflow:'hidden',
                boxShadow:'0 20px 60px rgba(0,0,0,0.6)'
            }}>
                <div style={{
                    display:'flex',alignItems:'center',gap:12,
                    padding:'14px 20px',borderBottom:'1px solid rgba(255,255,255,0.08)',
                    background:'rgba(245,158,11,0.14)'
                }}>
                    <span style={{fontSize:20,color:'#f59e0b'}}>⚠</span>
                    <span style={{fontFamily:'Space Mono,monospace',fontSize:11,fontWeight:900,textTransform:'uppercase',letterSpacing:1.5,color:'#fcd34d'}}>{state.title}</span>
                </div>
                <p style={{padding:'16px 20px',fontFamily:'DM Sans,sans-serif',fontSize:13,fontWeight:800,lineHeight:1.6,color:'rgba(255,255,255,0.8)',margin:0}}>{state.message}</p>
                <div style={{display:'flex',justifyContent:'flex-end',gap:10,padding:'12px 20px',background:'rgba(0,0,0,0.2)',borderTop:'1px solid rgba(255,255,255,0.06)'}}>
                    <button onClick={() => onAnswer(false)} autoFocus style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                        CANCEL
                    </button>
                    <button onClick={() => onAnswer(true)} style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'#EE8C3A',border:'none',color:'#1a2e30',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                        DISCARD
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── MAIN COMPONENT ────────────────────────────────────────────────
const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const IntakePage = () => {
    const navigate = useNavigate();
    const { toasts, toast, dismissToast } = useToast();'''
)

# Add confirmNote destructure inside IntakePage body
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''    const fileInputRef = useRef(null);

    const [saving, setSaving] = useState(false);''',
    '''    const fileInputRef = useRef(null);
    const { confirmState: noteConfirmState, confirm: confirmNote, handleAnswer: handleNoteAnswer } = useIntakeConfirm();

    const [saving, setSaving] = useState(false);'''
)

# Render the IntakeConfirmModal inside the IntakePage return, before closing div
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />''',
    '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />

            {/* NOTE DISCARD CONFIRM MODAL */}
            <IntakeConfirmModal state={noteConfirmState} onAnswer={handleNoteAnswer} />'''
)

print("=== ALL FIXES APPLIED ===")