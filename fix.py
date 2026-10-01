#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix165: FOLDER PAGE NON-NEGOTIABLES + POPUP ERRORS. Apply AFTER fix164.
#
#  1. A PAYMENT CAN NO LONGER EXIST WITHOUT ITS RECEIPT. The payment and the receipt file now travel to the server in
#     ONE request and are saved in ONE step (server refuses: no file, empty file, wrong type, over 10 MB; if the
#     receipt cannot be filed the payment is rolled back). Before, the page saved the payment first and uploaded the
#     receipt after, and the server never checked.
#  2. A payment receipt can never be deleted (button hidden, server refuses). Reverse the payment instead.
#  3. Payments: whole shillings only, never on a deleted project, overpayment checked on the page too.
#  4. POPUP ERRORS CAN BE SEEN. Error toasts used to sit BEHIND popups (same layer, drawn earlier), so a failed note
#     save looked like "nothing happened". Now: toasts sit above popups and stay 12 seconds; every popup (note,
#     payment, reason, problem, upload) also shows a red error box inside itself with the server's own words + the
#     HTTP number; the vague "SAVE FAILED" / "FLAG FAILED" / "INGESTION FAILED" messages now say why. The server's
#     generic "Core error" now names the kind of crash, and missing-file / bad-value requests give a clear 400.
#  5. NOTES: adding a note (or flagging a PROBLEM) on a project that has no title yet CRASHED the server (it read the
#     plot number of a title that does not exist). Fixed. Notes are 2-2000 characters, sent in the request body (a
#     long note in the web address was refused), and the audit line keeps the old words on edit / delete.
#  6. PROBLEM flag needs a reason of 5+ characters (page + server). If the flag saves but its note does not, the
#     page now says so instead of "FLAG FAILED".
#  7. Popups that hold typed text no longer close (and throw the text away) when you click outside them; closing an
#     unsaved note asks first. Uploads only take PDF / JPG / PNG / WEBP, not empty, under 50 MB (page + server).
#  8. The ?action=pay link no longer opens the payment popup for roles that cannot record payments.
#  9. LLM_CONTEXT_GUIDE.md Section 15 records all of this.
#
# NOT in this fix: Intake initial payment (no receipt rule there yet), who-flagged-it display, call logs, history tab.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix165"
COMMIT_MSG = "fix165: payment+receipt saved together (receipt mandatory, undeletable), popup errors visible, note crash fixed, problem needs reason"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
MODAL_JSX = os.path.join(SRC, "components", "common", "HardwareModal.jsx")
LAND_SVC_JS = os.path.join(SRC, "services", "landService.js")
RECOVERY_SVC_JS = os.path.join(SRC, "services", "recoveryService.js")
LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
LAND_CTRL = os.path.join(JAVA, "modules", "land", "controller", "LandController.java")
PORTAL_CTRL = os.path.join(JAVA, "modules", "land", "controller", "FolderPortalController.java")
EXC = os.path.join(JAVA, "common", "exception", "GlobalExceptionHandler.java")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
# ============================= EDIT PART 1 END =============================


# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)



# ============================ EDIT PART 2 START ============================
LOAD_FILES = (FOLDER_JSX, FOLDER_CSS, MODAL_JSX, LAND_SVC_JS, RECOVERY_SVC_JS, LAND_SERVICE, LAND_CTRL, PORTAL_CTRL, EXC, GUIDE)
for _p in LOAD_FILES:
    load(_p)

patch(FOLDER_JSX,
r"""// fix138: every payment needs its receipt scan filed under Payment Receipts.
// Set to false to make the receipt optional.
const RECEIPT_REQUIRED = true;
""",
r"""// fix165: a payment can NEVER be saved without its receipt scan (the server refuses it too).
// Do not set this to false: the server would still refuse the payment.
const RECEIPT_REQUIRED = true;
const NOTE_MAX = 2000;
const SCAN_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];
const fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };
// fix165: ONE place that turns any failed request into a sentence a person can read.
// Always shows the server's own words and the HTTP number, so a popup error is never just "FAILED".
const errText = (err) => {
    const st = err && err.response && err.response.status;
    if (!st) return 'NO REPLY FROM THE SERVER (internet is down, or the server is waking up). Nothing was saved. Wait a few seconds and try again.';
    const d = err.response.data;
    let msg = '';
    if (d && typeof d === 'object') msg = d.message || d.error || '';
    else if (typeof d === 'string' && d.length < 300) msg = d;
    if (!msg) msg = err.message || 'Unknown error';
    return msg + ' (HTTP ' + st + ')';
};
// fix165: red error box that sits INSIDE a popup, so a failure is read where the work is being done.
const ModalError = ({ text }) => (text ? (<div className={styles.modalErr} role="alert">
    <FiAlertCircle className={styles.modalErrIcon} aria-hidden="true" /><span>{text}</span></div>) : null);
""",
'fix165: shared helpers (errText, ModalError, constants)')

patch(FOLDER_JSX,
r"""        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);""",
r"""        // fix165: an error stays on screen for at least 12 seconds (or until closed) so it can be read
        const ms = type === 'error' && duration > 0 ? Math.max(duration, 12000) : duration;
        if (ms > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), ms);""",
'fix165: error toasts stay at least 12 seconds')

patch(FOLDER_JSX,
r"""    const [noteModal, setNoteModal] = useState({ open: false, id: null, content: '' });""",
r"""    const [noteModal, setNoteModal] = useState({ open: false, id: null, content: '' });
    const [noteErr, setNoteErr] = useState(''); const [noteBusy, setNoteBusy] = useState(false);""",
'fix165: note popup error + busy state')

patch(FOLDER_JSX,
r"""    useEffect(() => { if (!payModal.open) setPayReceipt(null); }, [payModal.open]);""",
r"""    const [payErr, setPayErr] = useState('');
    useEffect(() => { if (!payModal.open) { setPayReceipt(null); setPayErr(''); } }, [payModal.open]);""",
'fix165: payment popup error state, cleared when it closes')

patch(FOLDER_JSX,
r"""    const [probBusy, setProbBusy] = useState(false);""",
r"""    const [probBusy, setProbBusy] = useState(false);
    const [probErr, setProbErr] = useState('');
    const [reasonErr, setReasonErr] = useState('');""",
'fix165: problem + reason popup error state')

patch(FOLDER_JSX,
r"""        if (action === 'pay') { setActiveTab('FINANCIALS');""",
r"""        if (!canEdit && (action === 'pay' || action === 'storage')) { toast('Only a manager or director can record payments.', 'error', 6000); return; }
        if (action === 'pay') { setActiveTab('FINANCIALS');""",
'fix165: the ?action=pay link no longer opens the payment popup for roles that cannot pay')

patch(FOLDER_JSX,
r"""catch (err) { toast('SAVE FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setCommitting(false); }""",
r"""catch (err) { toast('SAVE FAILED: ' + errText(err), 'error', 12000); }
        finally { setCommitting(false); }""",
'fix165: record SAVE error shows server words + HTTP number')

patch(FOLDER_JSX,
r"""} catch { toast('RESUME FAILED', 'error'); } };""",
r"""} catch (err) { toast('RESUME FAILED: ' + errText(err), 'error', 12000); } };""",
'fix165: RESUME FEES error shows the reason')

patch(FOLDER_JSX,
r"""toast(err.response?.data?.message || 'HAND OVER FAILED', 'error', 8000);""",
r"""toast('HAND OVER FAILED: ' + errText(err), 'error', 12000);""",
'fix165: HAND OVER error shows HTTP number')

patch(FOLDER_JSX,
r"""    const runToggleProblem = async (text) => { const was = project.problem; const note = (text || '').trim(); try { await folderPortalService.toggleProblem(id, note); if (!was && note) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); return true; } catch { toast('FLAG FAILED', 'error'); return false; } };""",
r"""    // fix165: a PROBLEM flag must say what the problem is (5+ characters). The flag and its note are saved
    // as two steps; if the note step fails the flag stays and the person is told exactly that.
    const runToggleProblem = async (text) => {
        const was = project.problem; const note = (text || '').trim();
        if (!was && note.length < 5) { const m = 'WRITE WHAT THE PROBLEM IS (AT LEAST 5 CHARACTERS).'; setProbErr(m); toast(m, 'error', 8000); return false; }
        try { await folderPortalService.toggleProblem(id, note); }
        catch (err) { const m = errText(err); setProbErr(m); toast('FLAG FAILED: ' + m, 'error', 12000); return false; }
        let noteSaved = true;
        if (!was && note) { try { await landService.addStandaloneNote(id, '[PROBLEM] ' + note); } catch { noteSaved = false; } }
        await loadFolderData();
        if (!was && !noteSaved) toast('Flagged as PROBLEM, but the note did NOT save. Add it again from the NOTES tab.', 'warn', 12000);
        else toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn');
        return true;
    };""",
'fix165: PROBLEM flag needs a reason, partial failure is reported')

patch(FOLDER_JSX,
r"""const handleToggleProblem = () => { if (project.problem) { runToggleProblem(''); } else { setProblemModal({ open: true, note: '' }); } };
    const closeProblemModal = () => { if (!probBusy) setProblemModal({ open: false, note: '' }); };""",
r"""const handleToggleProblem = () => { if (project.problem) { runToggleProblem(''); } else { setProbErr(''); setProblemModal({ open: true, note: '' }); } };
    const closeProblemModal = () => { if (!probBusy) { setProbErr(''); setProblemModal({ open: false, note: '' }); } };""",
'fix165: problem popup clears its error when opened/closed')

patch(FOLDER_JSX,
r"""    const openReasonModal = (cfg) => setReasonModal({ open: true,""",
r"""    const openReasonModal = (cfg) => { setReasonErr(''); setReasonModal({ open: true,""",
'fix165: reason popup opens with a clean error box (part 1)')

patch(FOLDER_JSX,
r"""paymentId: null, ...cfg });""",
r"""paymentId: null, ...cfg }); };""",
'fix165: reason popup opens with a clean error box (part 2)')

patch(FOLDER_JSX,
r"""    const closeReasonModal = () => { if (!reasonBusy) setReasonModal(m => ({ ...m, open: false })); };""",
r"""    const closeReasonModal = () => { if (!reasonBusy) { setReasonErr(''); setReasonModal(m => ({ ...m, open: false })); } };""",
'fix165: reason popup clears its error on close')

patch(FOLDER_JSX,
r"""        if (why.length < 5) { toast('WRITE THE REASON (AT LEAST 5 CHARACTERS)', 'error'); return; }""",
r"""        if (why.length < 5) { const m = 'WRITE THE REASON (AT LEAST 5 CHARACTERS).'; setReasonErr(m); toast(m, 'error'); return; }""",
'fix165: reason popup shows the missing-reason message inside the popup')

patch(FOLDER_JSX,
r"""{ toast('ENTER A NEW TOTAL THAT IS LOWER THAN THE CURRENT FEES', 'error', 6000); return; }""",
r"""{ const m = 'ENTER A NEW TOTAL THAT IS LOWER THAN THE CURRENT FEES.'; setReasonErr(m); toast(m, 'error', 6000); return; }""",
'fix165: reduce-fees validation message inside the popup')

patch(FOLDER_JSX,
r"""        setReasonBusy(true);
        try {
            if (m.kind === 'REVERSE')""",
r"""        setReasonBusy(true); setReasonErr('');
        try {
            if (m.kind === 'REVERSE')""",
'fix165: reason popup clears old error before sending')

patch(FOLDER_JSX,
r"""catch (err) { toast('FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setReasonBusy(false); }""",
r"""catch (err) { const m = errText(err); setReasonErr(m); toast('NOT DONE: ' + m, 'error', 12000); }
        finally { setReasonBusy(false); }""",
'fix165: reason popup shows the server error inside the popup')

patch(FOLDER_JSX,
r"""    const handleNoteSave = async () => { if (!noteModal.content.trim()) return; try { if (noteModal.id) await landService.editStandaloneNote(noteModal.id, noteModal.content); else await landService.addStandaloneNote(id, noteModal.content); setNoteModal({ open: false, id: null, content: '' }); await loadFolderData(); toast('Note saved', 'success', 3000); } catch { toast('SAVE FAILED', 'error'); } };""",
r"""    // fix165: the note popup shows its own errors (the server's words), cannot be thrown away by a stray click
    // outside it, asks before discarding typed text, and a note over 2000 characters is refused before sending.
    const noteOriginal = () => (noteModal.id ? ((binder?.notes || []).find(n => n.id === noteModal.id) || {}).notes || '' : '');
    const closeNoteModal = async () => {
        if (noteBusy) return;
        const dirty = noteModal.content.trim() !== '' && noteModal.content !== noteOriginal();
        if (dirty) { const ok = await confirm('DISCARD NOTE', 'This note is not saved. Close it and lose what you typed?', 'warn'); if (!ok) return; }
        setNoteErr(''); setNoteModal({ open: false, id: null, content: '' });
    };
    const handleNoteSave = async () => {
        if (noteBusy) return;
        const text = noteModal.content.trim();
        if (text.length < 2) { setNoteErr('WRITE THE NOTE FIRST (AT LEAST 2 CHARACTERS).'); return; }
        if (text.length > NOTE_MAX) { setNoteErr('TOO LONG: ' + text.length + ' CHARACTERS. THE LIMIT IS ' + NOTE_MAX + '.'); return; }
        setNoteBusy(true); setNoteErr('');
        try {
            if (noteModal.id) await landService.editStandaloneNote(noteModal.id, text); else await landService.addStandaloneNote(id, text);
            setNoteModal({ open: false, id: null, content: '' });
            await loadFolderData(); toast('Note saved', 'success', 3000);
        } catch (err) { const m = errText(err); setNoteErr(m); toast('NOTE NOT SAVED: ' + m, 'error', 12000); }
        finally { setNoteBusy(false); }
    };""",
'fix165: note popup errors, discard guard, length check')

patch(FOLDER_JSX,
r"""try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };""",
r"""try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch (err) { toast('NOTE NOT DELETED: ' + errText(err), 'error', 12000); } };""",
'fix165: delete-note error shows reason')

patch(FOLDER_JSX,
r"""try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };""",
r"""try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch (err) { toast('DOCUMENT NOT DELETED: ' + errText(err), 'error', 12000); } };""",
'fix165: delete-document error shows reason')

patch(FOLDER_JSX,
r"""{isEditing && canEdit && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>""",
r"""{isEditing && canEdit && doc.category !== 'PAYMENT_RECEIPT' && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>""",
'fix165: payment receipts have no delete button')

patch(FOLDER_JSX,
r"""    const handleVaultAction = (files) => { if (!files?.length) return; setUploadDraft({ batch: '', files: files.map(file => ({ file, category: '' })) }); };""",
r"""    // fix165: wrong type / empty / oversized files are turned away here with the reason, before any upload starts
    const handleVaultAction = (files) => {
        if (!files?.length) return;
        const ok = []; const bad = [];
        files.forEach(f => {
            if (!SCAN_EXT.includes(fileExt(f.name))) bad.push(f.name + ' (use PDF, JPG, PNG or WEBP)');
            else if (!f.size) bad.push(f.name + ' (the file is empty)');
            else if (f.size > 50 * 1024 * 1024) bad.push(f.name + ' (over 50 MB)');
            else ok.push(f);
        });
        if (bad.length) toast('NOT ADDED: ' + bad.join('; '), 'error', 12000);
        if (!ok.length) return;
        setUploadDraft({ batch: '', error: '', files: ok.map(file => ({ file, category: '' })) });
    };""",
'fix165: upload picker refuses wrong type / empty / oversized files with the reason')

patch(FOLDER_JSX,
r"""        if (uploadDraft.files.some(f => !f.category)) { toast('Pick a category for every file', 'warn', 4000); return; }""",
r"""        if (uploadDraft.files.some(f => !f.category)) { const m = 'PICK A CATEGORY FOR EVERY FILE.'; setUploadDraft(d => d && ({ ...d, error: m })); toast(m, 'warn', 6000); return; }""",
'fix165: upload popup shows the missing-category message inside the popup')

patch(FOLDER_JSX,
r"""        } catch { toast('INGESTION FAILED', 'error', 8000); } finally { setCommitting(false); }""",
r"""        } catch (err) { const m = errText(err); setUploadDraft(d => d && ({ ...d, error: m })); toast('UPLOAD FAILED: ' + m, 'error', 12000); } finally { setCommitting(false); }""",
'fix165: upload popup shows the server error inside the popup')

patch(FOLDER_JSX,
r"""} catch { toast('COULD NOT ADD CATEGORY', 'error', 6000); } finally { setCatBusy(false); }""",
r"""} catch (err) { const m = errText(err); setUploadDraft(d => d && ({ ...d, error: 'COULD NOT ADD CATEGORY: ' + m })); toast('COULD NOT ADD CATEGORY: ' + m, 'error', 12000); } finally { setCatBusy(false); }""",
'fix165: add-category error shows reason')

patch(FOLDER_JSX,
r"""    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        if (RECEIPT_REQUIRED && !payReceipt) { toast('ATTACH THE PAYMENT RECEIPT', 'error'); return; }
        setPaying(true);
        try {
            const fullNotes = payType === 'STORAGE' ? ('[STORAGE FEE PAYMENT] ' + payNotes).trim() : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            // fix138: file the receipt in Documents > Payment Receipts (payment is already saved at this point)
            let receiptOk = true;
            if (payReceipt) {
                try {
                    const ext = (payReceipt.name.match(/\.[A-Za-z0-9]{1,6}$/) || [''])[0];
                    const stamp = new Date().toISOString().slice(0, 10);
                    const receiptName = 'Receipt - ' + (payType === 'STORAGE' ? 'Storage Fee' : 'Title Payment') + ' - UGX ' + Number(payAmount) + ' - ' + stamp + ext;
                    await landService.addExtraDocuments(id, [new File([payReceipt], receiptName, { type: payReceipt.type })], ['PAYMENT_RECEIPT']);
                } catch { receiptOk = false; }
            }
            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            if (receiptOk) toast(payReceipt ? 'Payment recorded. Receipt filed under Payment Receipts.' : 'Payment recorded successfully', 'success', 4500);
            else toast('Payment recorded, but the RECEIPT DID NOT UPLOAD. Add it from Documents > Payment Receipts.', 'warn', 9000);
        } catch (err) { toast('PAYMENT FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setPaying(false); }
    };""",
r"""    // fix165: the payment and its receipt travel to the server TOGETHER and are saved in ONE step. The server refuses a
    // payment with no receipt (wrong type, empty, over 10 MB) and rolls the payment back if the receipt cannot be filed.
    const handleRecordPayment = async () => {
        if (paying) return;
        const amt = Number(payAmount);
        const fail = (m) => { setPayErr(m); toast(m, 'error', 8000); };
        if (!payAmount || !Number.isFinite(amt) || amt <= 0) { fail('ENTER A VALID AMOUNT.'); return; }
        if (!Number.isInteger(amt)) { fail('ENTER WHOLE SHILLINGS ONLY (NO DECIMALS).'); return; }
        if (amt > Math.max(0, amountOwed)) { fail('OVERPAYMENT: THIS PROJECT ONLY OWES UGX ' + fmt(amountOwed) + '. YOU TYPED UGX ' + fmt(amt) + '.'); return; }
        if (RECEIPT_REQUIRED && !payReceipt) { fail('ATTACH THE PAYMENT RECEIPT. A PAYMENT CANNOT BE SAVED WITHOUT IT.'); return; }
        if (!SCAN_EXT.includes(fileExt(payReceipt.name))) { fail('THE RECEIPT MUST BE A PDF, JPG, PNG OR WEBP FILE.'); return; }
        if (!payReceipt.size) { fail('THE RECEIPT FILE IS EMPTY. SCAN OR PHOTOGRAPH IT AGAIN.'); return; }
        if (payReceipt.size > 10 * 1024 * 1024) { fail('THE RECEIPT IS OVER 10 MB. USE A SMALLER SCAN.'); return; }
        setPaying(true); setPayErr('');
        try {
            const fullNotes = payType === 'STORAGE' ? ('[STORAGE FEE PAYMENT] ' + payNotes).trim() : payNotes;
            const stamp = new Date().toISOString().slice(0, 10);
            const receiptName = 'Receipt - ' + (payType === 'STORAGE' ? 'Storage Fee' : 'Title Payment') + ' - UGX ' + amt + ' - ' + stamp + '.' + fileExt(payReceipt.name);
            await recoveryService.recordPayment(id, amt, fullNotes, new File([payReceipt], receiptName, { type: payReceipt.type }));
            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('Payment recorded. Receipt filed under Payment Receipts.', 'success', 4500);
        } catch (err) { const m = errText(err); setPayErr(m); toast('PAYMENT NOT SAVED: ' + m, 'error', 12000); }
        finally { setPaying(false); }
    };""",
'fix165: payment + receipt saved together; every check shown inside the popup')

patch(FOLDER_JSX,
r"""<HardwareModal isOpen={!!uploadDraft} onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
                {uploadDraft && (<>""",
r"""<HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
                {uploadDraft && (<>
                    <ModalError text={uploadDraft.error} />""",
'fix165: upload popup: error box + backdrop click no longer closes it')

patch(FOLDER_JSX,
r"""            <HardwareModal isOpen={noteModal.open} onClose={() => { setNoteModal({ open: false, id: null, content: '' }); }} title={noteModal.id ? 'EDIT NOTE' : 'ADD NOTE'}>
                <div className={modalStyles.modalField}><textarea className={modalStyles.modalTextarea} value={noteModal.content} onChange={e => setNoteModal({ ...noteModal, content: e.target.value })} placeholder="Enter interaction note..." aria-label="Note content" /></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}><FiSave aria-hidden="true" /> SAVE ENTRY</button>
                </div>""",
r"""            <HardwareModal isOpen={noteModal.open} lockBackdrop onClose={closeNoteModal} title={noteModal.id ? 'EDIT NOTE' : 'ADD NOTE'}>
                <ModalError text={noteErr} />
                <div className={modalStyles.modalField}><textarea className={modalStyles.modalTextarea} value={noteModal.content} onChange={e => { setNoteModal({ ...noteModal, content: e.target.value }); if (noteErr) setNoteErr(''); }} placeholder="Enter interaction note..." aria-label="Note content" />
                    <span className={styles.probCount}>{noteModal.content.trim().length}/{NOTE_MAX}</span></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave} disabled={noteBusy}><FiSave aria-hidden="true" /> {noteBusy ? 'SAVING...' : 'SAVE ENTRY'}</button>
                </div>""",
'fix165: note popup layout (error box, counter, no double submit)')

patch(FOLDER_JSX,
r"""<HardwareModal isOpen={payModal.open} onClose=""",
r"""<HardwareModal isOpen={payModal.open} lockBackdrop onClose=""",
'fix165: payment popup: backdrop click no longer closes it')

patch(FOLDER_JSX,
r"""<input type="number" className={modalStyles.modalInput} placeholder={'e.g. ' + fmt(Math.max(0, amountOwed))} value={payAmount} onChange={e => setPayAmount(e.target.value)} />""",
r"""<input type="text" inputMode="numeric" className={modalStyles.modalInput} placeholder={'e.g. ' + fmt(Math.max(0, amountOwed))} value={payAmount} onChange={e => { setPayAmount(e.target.value.replace(/[^0-9]/g, '')); if (payErr) setPayErr(''); }} />""",
'fix165: payment amount accepts whole shillings only')

patch(FOLDER_JSX,
r"""<span className={styles.recHint}>Saved in this folder's Documents under Payment Receipts.</span></div>""",
r"""<span className={styles.recHint}>Saved in this folder's Documents under Payment Receipts. PDF, JPG, PNG or WEBP, up to 10 MB. The payment is NOT saved without it.</span></div>
                <ModalError text={payErr} />""",
'fix165: payment popup error box + receipt hint')

patch(FOLDER_JSX,
r"""<HardwareModal isOpen={reasonModal.open} onClose={closeReasonModal}""",
r"""<HardwareModal isOpen={reasonModal.open} lockBackdrop onClose={closeReasonModal}""",
'fix165: reason popup: backdrop click no longer closes it')

patch(FOLDER_JSX,
r"""<span className={styles.probCount}>{reasonModal.reason.length}/300</span></div>""",
r"""<span className={styles.probCount}>{reasonModal.reason.length}/300</span></div>
                <ModalError text={reasonErr} />""",
'fix165: reason popup error box')

patch(FOLDER_JSX,
r"""<HardwareModal isOpen={problemModal.open} onClose={closeProblemModal}""",
r"""<HardwareModal isOpen={problemModal.open} lockBackdrop onClose={closeProblemModal}""",
'fix165: problem popup: backdrop click no longer closes it')

patch(FOLDER_JSX,
r"""WHAT IS THE PROBLEM? (OPTIONAL)""",
r"""WHAT IS THE PROBLEM? (REQUIRED)""",
'fix165: problem description is now required')

patch(FOLDER_JSX,
r"""<span className={styles.probCount}>{problemModal.note.length}/500</span></div>""",
r"""<span className={styles.probCount}>{problemModal.note.length}/500</span></div>
                <ModalError text={probErr} />""",
'fix165: problem popup error box')

patch(FOLDER_CSS,
r"""    z-index: 99999;
    display: flex;
    flex-direction: column-reverse;""",
r"""    z-index: 100002; /* fix165: above every popup (popups are 99999), so an error is never hidden behind one */
    display: flex;
    flex-direction: column-reverse;""",
'fix165: error toasts now sit ABOVE popups')

patch(FOLDER_CSS,
r"""    z-index: 99998; /* below saving overlay (99000) but above all page content */""",
r"""    z-index: 100001; /* fix165: above popups so a confirm opened from inside a popup is visible */""",
'fix165: confirm window sits above popups')

patch(FOLDER_CSS,
r""".toast {
    display: flex;""",
r""".modalErr {
    display: flex; align-items: flex-start; gap: 8px;
    background: rgba(239, 68, 68, 0.14); border: 1.5px solid rgba(239, 68, 68, 0.6); border-radius: 8px;
    padding: 10px 12px; margin: 0 0 14px;
    color: #fecaca; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 800; line-height: 1.5;
    word-break: break-word;
}
.modalErrIcon { flex: 0 0 auto; margin-top: 2px; color: #f87171; }

.toast {
    display: flex;""",
'fix165: red error box style for popups')

patch(MODAL_JSX,
r"""const HardwareModal = ({ isOpen, onClose, title, children }) => {""",
r"""const HardwareModal = ({ isOpen, onClose, title, children, lockBackdrop = false }) => {""",
'fix165: HardwareModal can ignore backdrop clicks (lockBackdrop)')

patch(MODAL_JSX,
r"""<div className={styles.backdrop} onClick={onClose}>""",
r"""<div className={styles.backdrop} onClick={lockBackdrop ? undefined : onClose}>""",
'fix165: backdrop click closes only popups that are not locked')

patch(LAND_SVC_JS,
r"""        await api.post(`/land/projects/${projectId}/notes`, null, { params: { content } });""",
r"""        // fix165: the note travels in the request body (a long note in the web address was refused by the server)
        await api.post(`/land/projects/${projectId}/notes`, { content });""",
'fix165: add note sends the text in the body')

patch(LAND_SVC_JS,
r"""        await api.put(`/land/notes/${noteId}`, null, { params: { content } });""",
r"""        await api.put(`/land/notes/${noteId}`, { content });""",
'fix165: edit note sends the text in the body')

patch(RECOVERY_SVC_JS,
r"""  recordPayment: (projectId, amount, notes) => api.post(`/land/projects/${projectId}/payment`, null, { params: { amount, notes } }),""",
r"""  // fix165: a payment is sent TOGETHER with its receipt file; the server refuses it without one.
  recordPayment: (projectId, amount, notes, receipt) => {
    const fd = new FormData();
    fd.append('amount', String(amount));
    if (notes) fd.append('notes', notes);
    if (receipt) fd.append('receipt', receipt, receipt.name);
    return api.post(`/land/projects/${projectId}/payment`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },""",
'fix165: recordPayment sends the receipt file with the payment')

patch(LAND_SERVICE,
r"""    @Transactional
    public void logNewNote(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("NOTE_ADDED",
            "Operator [" + getCurrentOperator() + "] added note to plot: "
            + project.getLandTitle().getPlotNumber());
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        FollowUpLog log = followUpRepository.findById(noteId).orElseThrow();
        log.setNotes(content);
        followUpRepository.save(log);
        auditService.logAction("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated a log entry.");
    }

    @Transactional
    public void removeNote(UUID noteId) {
        followUpRepository.deleteById(noteId);
        auditService.logAction("NOTE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted a log entry.");
    }""",
r"""    // fix165: notes. A note on a project that has no title yet used to crash the server (it read the plot number of a
    // title that did not exist), so adding a note or flagging a PROBLEM on a folder failed. Text is now checked and
    // the audit line keeps the old words when a note is edited or deleted.
    private static final int NOTE_MAX_CHARS = 2000;

    private String cleanNoteText(String content) {
        String c = content == null ? "" : content.trim();
        if (c.length() < 2) {
            throw new BusinessException("NOTE_REQUIRED: Write the note first (at least 2 characters).");
        }
        if (c.length() > NOTE_MAX_CHARS) {
            throw new BusinessException("NOTE_TOO_LONG: A note can be at most " + NOTE_MAX_CHARS
                    + " characters (this one is " + c.length() + ").");
        }
        return c;
    }

    private String shortText(String s) {
        if (s == null) return "";
        String t = s.replace('\n', ' ').trim();
        return t.length() > 160 ? t.substring(0, 160) + "..." : t;
    }

    @Transactional
    public void logNewNote(UUID projectId, String content) {
        String text = cleanNoteText(content);
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(text)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("NOTE_ADDED",
            "Operator [" + getCurrentOperator() + "] added note to " + plotLabel(project) + ": " + shortText(text));
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        String text = cleanNoteText(content);
        FollowUpLog log = followUpRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        String before = log.getNotes();
        log.setNotes(text);
        followUpRepository.save(log);
        auditService.logAction("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] edited a note. WAS: " + shortText(before) + " | NOW: " + shortText(text));
    }

    @Transactional
    public void removeNote(UUID noteId) {
        FollowUpLog log = followUpRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        String before = log.getNotes();
        followUpRepository.delete(log);
        auditService.logAction("NOTE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted a note: " + shortText(before));
    }""",
'fix165: notes: no crash without a title, validated, old words kept in the audit')

patch(LAND_SERVICE,
r"""        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        // STAGE 1 FIX: block overpayment""",
r"""        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        // fix165: no money can be recorded against a deleted project, and no fractions of a shilling.
        if (project.isDeleted()) {
            throw new BusinessException("PAYMENT_BLOCKED: This project is deleted. Restore it first.");
        }
        if (amount.stripTrailingZeros().scale() > 0) {
            throw new BusinessException("PAYMENT_FAULT: Enter whole shillings only (no decimals).");
        }

        // STAGE 1 FIX: block overpayment""",
'fix165: payments refused on deleted projects and for fractions of a shilling')

patch(LAND_SERVICE,
r"""            + " | Amount owed after: UGX " + balanceAfter);
    }
""",
r"""            + " | Amount owed after: UGX " + balanceAfter);
    }

    // fix165: A PAYMENT CAN NEVER EXIST WITHOUT ITS RECEIPT. The receipt is checked first, the payment is recorded,
    // then the receipt is filed under Payment Receipts -- all in ONE transaction. If the receipt cannot be filed
    // (storage down, bad file) the payment is rolled back too, so there is never a payment with no receipt.
    @Transactional(rollbackFor = Exception.class)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPaymentWithReceipt(UUID projectId, BigDecimal amount, String notes, MultipartFile receipt) throws Exception {
        if (receipt == null || receipt.isEmpty()) {
            throw new BusinessException("RECEIPT_REQUIRED: A payment cannot be saved without its receipt. Attach the receipt scan (PDF, JPG, PNG or WEBP).");
        }
        if (receipt.getSize() > 10L * 1024L * 1024L) {
            throw new BusinessException("RECEIPT_TOO_LARGE: The receipt must be under 10 MB.");
        }
        requireScanFiles(new MultipartFile[] { receipt });
        recordPayment(projectId, amount, notes);
        addScansToProject(projectId, new MultipartFile[] { receipt }, "PAYMENT_RECEIPT", null);
    }

    // fix165: only real scans (PDF / JPG / PNG / WEBP), never an empty file, can be filed into a folder.
    public void requireScanFiles(MultipartFile[] scans) {
        if (scans == null || scans.length == 0) {
            throw new BusinessException("FILE_REQUIRED: Choose at least one file.");
        }
        for (MultipartFile f : scans) {
            if (f == null || f.isEmpty()) {
                throw new BusinessException("FILE_EMPTY: One of the files is empty (0 bytes). Scan or photograph it again.");
            }
            String name = f.getOriginalFilename() == null ? "" : f.getOriginalFilename().toLowerCase();
            int dot = name.lastIndexOf('.');
            String ext = dot >= 0 ? name.substring(dot + 1) : "";
            if (!Set.of("pdf", "jpg", "jpeg", "png", "webp").contains(ext)) {
                throw new BusinessException("FILE_TYPE_BLOCKED: \"" + f.getOriginalFilename() + "\" is not allowed. Use PDF, JPG, PNG or WEBP.");
            }
        }
    }
""",
'fix165: recordPaymentWithReceipt (payment + receipt, one transaction) and scan-file check')

patch(LAND_SERVICE,
r"""        ProjectDocument doc = documentRepository.findById(docId).orElseThrow();
        fileStorageService.deleteFile(doc.getFilePath());""",
r"""        ProjectDocument doc = documentRepository.findById(docId)
                .orElseThrow(() -> new BusinessException("DOCUMENT_NOT_FOUND: This document no longer exists."));
        // fix165: a payment receipt is evidence of money received. It can never be deleted (reverse the payment instead).
        if ("PAYMENT_RECEIPT".equals(doc.getCategory())) {
            throw new BusinessException("RECEIPT_LOCKED: A payment receipt cannot be deleted. If the payment was a mistake, REVERSE it in Payment History; the receipt stays as proof.");
        }
        fileStorageService.deleteFile(doc.getFilePath());""",
'fix165: payment receipts cannot be deleted')

patch(LAND_CTRL,
r"""    @PostMapping("/projects/{id}/payment")
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes) {
        landService.recordPayment(id, amount, notes);
        return ResponseEntity.ok().build();
    }""",
r"""    // fix165: the ONLY way to record a payment is with its receipt file (multipart). The old no-receipt form is gone.
    @PostMapping(value = "/projects/{id}/payment", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes,
                                               @RequestParam(value = "receipt", required = false) MultipartFile receipt) throws Exception {
        landService.recordPaymentWithReceipt(id, amount, notes, receipt);
        return ResponseEntity.ok().build();
    }""",
'fix165: payment endpoint requires the receipt file')

patch(LAND_CTRL,
r"""    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);""",
r"""    public ResponseEntity<Void> addNote(@PathVariable UUID id,
                                        @RequestParam(required = false) String content,
                                        @RequestBody(required = false) java.util.Map<String, String> body) {
        // fix165: the text normally arrives in the body; the old ?content= form still works
        landService.logNewNote(id, content != null ? content : (body == null ? null : body.get("content")));""",
'fix165: add note accepts the text in the body')

patch(LAND_CTRL,
r"""    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId, @RequestParam String content) {
        landService.updateNote(noteId, content);""",
r"""    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId,
                                           @RequestParam(required = false) String content,
                                           @RequestBody(required = false) java.util.Map<String, String> body) {
        landService.updateNote(noteId, content != null ? content : (body == null ? null : body.get("content")));""",
'fix165: edit note accepts the text in the body')

patch(LAND_CTRL,
r"""        landService.addScansToProject(id, scans, category, categories);""",
r"""        landService.requireScanFiles(scans);
        landService.addScansToProject(id, scans, category, categories);""",
'fix165: uploads refuse empty / wrong-type files with a clear message')

patch(PORTAL_CTRL,
r"""        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setProblem(!p.isProblem());""",
r"""        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        // fix165: flagging a PROBLEM must say what the problem is. Clearing it needs no words.
        if (!p.isProblem() && (note == null || note.trim().length() < 5)) {
            throw new BusinessException("REASON_REQUIRED: Write what the problem is (at least 5 characters).");
        }
        p.setProblem(!p.isProblem());""",
'fix165: server refuses a PROBLEM flag with no reason')

patch(EXC,
r"""    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParams(MissingServletRequestParameterException ex) {
        System.err.println(">>> [PROTOCOL_FAULT]: Missing mandatory parameter: " + ex.getParameterName());
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required data missing.");
    }""",
r"""    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParams(MissingServletRequestParameterException ex) {
        System.err.println(">>> [PROTOCOL_FAULT]: Missing mandatory parameter: " + ex.getParameterName());
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required data missing: " + ex.getParameterName() + ".");
    }

    // fix165: a missing file part and a wrongly typed value used to fall into the generic 500 "Core error".
    @ExceptionHandler(org.springframework.web.multipart.support.MissingServletRequestPartException.class)
    public ResponseEntity<Map<String, Object>> handleMissingPart(org.springframework.web.multipart.support.MissingServletRequestPartException ex) {
        System.err.println(">>> [PROTOCOL_FAULT]: Missing file part: " + ex.getRequestPartName());
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required file missing: " + ex.getRequestPartName() + ".");
    }

    @ExceptionHandler(org.springframework.web.method.annotation.MethodArgumentTypeMismatchException.class)
    public ResponseEntity<Map<String, Object>> handleTypeMismatch(org.springframework.web.method.annotation.MethodArgumentTypeMismatchException ex) {
        System.err.println(">>> [DATA_FAULT]: Bad value for " + ex.getName());
        return buildResponse(HttpStatus.BAD_REQUEST, "DATA_FORMAT_ERROR", "Invalid value for " + ex.getName() + ".");
    }""",
'fix165: missing file / bad value return a clear 400 instead of a generic 500')

patch(EXC,
r"""Core error. Look at Render Logs""",
r"""Core error (" + ex.getClass().getSimpleName() + "). Look at Render Logs""",
'fix165: the generic 500 message now names the kind of crash')

patch(GUIDE,
r"""5 RELEASE + PROBLEM improvements (show reason and who flagged it) = TO DO. 6 per-plot history tab = TO DO.""",
r"""5 RELEASE + PROBLEM improvements = PARTLY (fix165: a PROBLEM flag needs a reason of 5+ characters, page + server; still TO DO: show who flagged it and when, and a reason on hand-over). 6 per-plot history tab = TO DO.
- FOLDER PAGE NON-NEGOTIABLES (fix165): (1) a payment is saved ONLY together with its receipt file: `POST /land/projects/{id}/payment` is multipart, `LandService.recordPaymentWithReceipt` checks the file (PDF/JPG/PNG/WEBP, not empty, under 10 MB), records the payment and files the receipt under PAYMENT_RECEIPT in ONE transaction (receipt fails = payment rolled back). (2) a PAYMENT_RECEIPT document can never be deleted (reverse the payment instead). (3) whole shillings only; nothing can be paid on a deleted project. (4) every popup shows its own errors inside the popup using `errText(err)` + `<ModalError/>` in FolderPage.jsx (server words + HTTP number); error toasts sit above popups (z-index 100002) and stay 12 s. (5) popups with typed text (note, payment, reason, problem, upload) do not close on a backdrop click (`lockBackdrop` prop on HardwareModal); closing an unsaved note asks first. (6) notes: 2-2000 characters, sent in the request body, the audit line keeps the old words on edit/delete; adding a note to a project with no title no longer crashes the server. (7) uploads only accept PDF/JPG/PNG/WEBP, not empty, under 50 MB (page + server).""",
'fix165: guide records the new non-negotiables')

# ============================= EDIT PART 2 END =============================


# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True


def working_tree_dirty():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return bool((r.stdout or "").strip())


# active = this script wrote something, OR files were already changed by hand (commit-only mode)
active = changed or working_tree_dirty()
if not changed and active:
    print("note: commit-only mode -- no patches defined, committing the changes already in the working tree")
if not active:
    print("note: nothing changed and the working tree is clean -- nothing to do")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file this script touched was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if active and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if active and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif active and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif active:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not active:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")