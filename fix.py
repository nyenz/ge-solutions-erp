#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix162: close the money loopholes on the Folder page + apply the Audit/Expenses look (old fix160).
#
# MONEY (backend + folder page):
#  1. AMOUNT PAID is locked in edit mode. The server ignores it too. It moves only via RECORD PAYMENT or REVERSE.
#  2. Changing TOTAL COST needs a written reason (audited); cost cannot go below what is paid; a stale form is refused.
#  3. REVERSE a payment (director/admin, reason, audited). The original stays; a negative REVERSAL line is added.
#  4. REDUCE storage fees to an agreed lower total (reason, audited). WAIVE now needs a reason. Rate/pause audit shows values.
#  5. UNDO a hand-over (director/admin, reason, audited). Hand-over is director/admin-only on the server too,
#     and is blocked while storage fees are still owed.
#  6. TITLE READY: UNDO and CANCEL now really un-tick the last stage (the checklist stays mounted while hidden).
# LOOK (was fix160, never applied): peach hover + alternating rows on Audit and Expenses, thinner Audit border,
#     inner border like Expenses, six basic action colours by group.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix162"
COMMIT_MSG = "fix162: money loopholes closed (locked paid amount, cost reason, reverse payment, reduce/waive fees with reason, undo hand-over) + audit/expenses look"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
AUDIT_CSS = os.path.join(SRC, "pages", "Audit", "AuditPage.module.css")
AUDIT_CAT = os.path.join(SRC, "pages", "Audit", "auditCatalog.js")
EXP_CSS = os.path.join(SRC, "pages", "Financials", "ExpensesPage.module.css")
FOLDER_SVC = os.path.join(SRC, "services", "folderPortalService.js")
LAND_SVC = os.path.join(SRC, "services", "landService.js")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp", "modules", "land")
LAND_SERVICE = os.path.join(JAVA, "service", "LandService.java")
LAND_CTRL = os.path.join(JAVA, "controller", "LandController.java")
PORTAL_CTRL = os.path.join(JAVA, "controller", "FolderPortalController.java")
ENTRY_DTO = os.path.join(JAVA, "dto", "LandEntryRequest.java")
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
LOAD_FILES = (FOLDER_JSX, FOLDER_CSS, AUDIT_CSS, AUDIT_CAT, EXP_CSS, FOLDER_SVC, LAND_SVC,
              LAND_SERVICE, LAND_CTRL, PORTAL_CTRL, ENTRY_DTO)
for _p in LOAD_FILES:
    load(_p)


# =========================== PART A -- BACKEND (money can only move through recorded actions) ===========================

# A1. The edit form can no longer overwrite AMOUNT PAID; a cost change needs a reason; stale forms are refused.
patch(LAND_SERVICE,
"""        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        project.setTotalCost(newTotalCost);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());""",
"""        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal oldTotalCost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal currentPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;

        // fix162 EDIT CONFLICT: the form remembers the cost it was loaded with. If somebody else changed the
        // cost in the meantime, refuse instead of silently overwriting their change.
        if (request.getExpectedTotalCost() != null && request.getExpectedTotalCost().compareTo(oldTotalCost) != 0) {
            throw new BusinessException("EDIT_CONFLICT: The total cost was changed by someone else (it is now UGX "
                    + oldTotalCost.toPlainString() + "). Reload this folder and try again.");
        }
        // fix162 COST CHANGE: needs a written reason, cannot go below what is already paid, and is audited.
        if (newTotalCost.compareTo(oldTotalCost) != 0) {
            String costWhy = request.getCostChangeReason() != null ? request.getCostChangeReason().trim() : "";
            if (costWhy.length() < 5) {
                throw new BusinessException("COST_REASON_REQUIRED: Write why the total cost is changing (at least 5 characters).");
            }
            if (newTotalCost.compareTo(currentPaid) < 0) {
                throw new BusinessException("COST_BELOW_PAID: The new cost (UGX " + newTotalCost.toPlainString()
                        + ") is lower than the UGX " + currentPaid.toPlainString()
                        + " already paid. Reverse the extra payment first.");
            }
            auditService.logAction("COST_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed total cost on " + plotLabel(project)
                + " from UGX " + oldTotalCost.toPlainString() + " to UGX " + newTotalCost.toPlainString()
                + ". Reason: " + costWhy);
        }
        project.setTotalCost(newTotalCost);
        // fix162 AMOUNT PAID is never taken from the edit form. It only moves through RECORD PAYMENT and REVERSE.
        project.setLegacy(request.isLegacy());""",
"Java: edit form cannot overwrite amount paid; cost change needs a reason; stale form refused")

# A2. Release: directors/admins only on the server too, and storage fees count as money owed.
patch(LAND_SERVICE,
"""    @Transactional
    public void authorizeRelease(UUID id, String managerNote) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }""",
"""    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void authorizeRelease(UUID id, String managerNote) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }
        // fix162: storage fees still owed are arrears too.
        if (project.isReceivable() && project.receivableTotalOwed().compareTo(BigDecimal.ZERO) > 0) {
            throw new BusinessException("RELEASE DENIED: Storage fees are still owed on this project.");
        }""",
"Java: release is director/admin only and blocked while storage fees are owed")

# A3. New: reverse a payment, undo a hand-over (both need a reason, both are audited).
patch(LAND_SERVICE, '    // ─── READ METHODS ─────────────────────────────────────────────────────────',
"""    // fix162: REVERSE A PAYMENT. The original line stays in the history; a negative REVERSAL line is added,
    // so every total, report and the audit trail stay honest.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void reversePayment(UUID projectId, UUID paymentId, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this payment is being reversed (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        PaymentRecord original = paymentRecordRepository.findById(paymentId)
                .orElseThrow(() -> new BusinessException("PAYMENT_NOT_FOUND"));
        if (!projectId.equals(original.getProjectId())) {
            throw new BusinessException("PAYMENT_NOT_FOUND: That payment does not belong to this project.");
        }
        if ("REVERSAL".equals(original.getPaymentType()) || original.getAmountPaid().compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("REVERSAL_BLOCKED: A reversal cannot be reversed. Record a new payment instead.");
        }
        String marker = "[REVERSAL OF " + paymentId + "]";
        for (PaymentRecord r : paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId)) {
            if (r.getNotes() != null && r.getNotes().startsWith(marker)) {
                throw new BusinessException("REVERSAL_BLOCKED: This payment was already reversed.");
            }
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("REVERSAL_BLOCKED: The title has been handed over. Undo the hand-over first.");
        }
        BigDecimal paid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        if (original.getAmountPaid().compareTo(paid) > 0) {
            throw new BusinessException("REVERSAL_BLOCKED: Reversing UGX " + original.getAmountPaid().toPlainString()
                    + " would take the total paid below zero.");
        }
        project.setAmountPaid(paid.subtract(original.getAmountPaid()));
        BigDecimal balanceAfter = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        PaymentRecord reversal = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(original.getAmountPaid().negate())
                .paymentType("REVERSAL")
                .recordedBy(getCurrentOperator())
                .notes(marker + " " + why)
                .balanceAfter(balanceAfter)
                .build();
        paymentRecordRepository.save(reversal);
        projectRepository.save(project);
        auditService.logAction("PAYMENT_REVERSED",
            "Operator [" + getCurrentOperator() + "] reversed UGX " + original.getAmountPaid().toPlainString()
            + " on " + plotLabel(project) + ". Reason: " + why);
    }

    // fix162: UNDO A HAND-OVER (the title goes back to "not handed over"). Reason required, audited.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void undoRelease(UUID id, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the hand-over is being undone (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (project.getLandTitle() == null || !project.getLandTitle().isReleased()) {
            throw new BusinessException("UNDO_DENIED: This title has not been handed over.");
        }
        project.getLandTitle().setReleased(false);
        project.setStatus(project.isReceivable() ? "RECEIVABLE" : "ACTIVE");
        projectRepository.save(project);
        auditService.logAction("TITLE_RELEASE_UNDONE",
            "Operator [" + getCurrentOperator() + "] undid the hand-over of " + plotLabel(project) + ". Reason: " + why);
    }

""" + '    // ─── READ METHODS ─────────────────────────────────────────────────────────',
"Java: reversePayment + undoRelease")

# A4. Controller: release locked to directors/admins; new endpoints.
patch(LAND_CTRL,
"""    @PatchMapping("/projects/{id}/release")
    public ResponseEntity<Void> authorizeRelease(""",
"""    @PatchMapping("/projects/{id}/release")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> authorizeRelease(""",
"Controller: release is director/admin only")
patch(LAND_CTRL,
"""    @PostMapping("/projects/{id}/receivable")
""",
"""    @PatchMapping("/projects/{id}/undo-release")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> undoRelease(@PathVariable UUID id, @RequestParam String reason) {
        landService.undoRelease(id, reason);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/payments/{paymentId}/reverse")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> reversePayment(@PathVariable UUID id, @PathVariable UUID paymentId,
                                               @RequestParam String reason) {
        landService.reversePayment(id, paymentId, reason);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/receivable")
""",
"Controller: undo-release + reverse-payment endpoints")

# A5. Request DTO: the two new fields.
patch(ENTRY_DTO,
"""    private BigDecimal totalCost;
    private BigDecimal initialPayment;
""",
"""    private BigDecimal totalCost;
    private BigDecimal initialPayment;

    // fix162 money safety: why the total cost changed, and the cost this form was loaded with (edit-conflict guard)
    private String costChangeReason;
    private BigDecimal expectedTotalCost;
""",
"DTO: costChangeReason + expectedTotalCost")

# A6. Fees: waive needs a reason; new REDUCE-FEES action; rate/pause changes show their values in the audit.
patch(PORTAL_CTRL,
"""        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        if ("WAIVE".equals(action)) {
            auditService.logAction("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + fees + " on #" + p.getProjectIndex() + ".");""",
"""        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        String reason = body.get("reason") != null ? body.get("reason").trim() : "";
        if ("WAIVE".equals(action)) {
            if (reason.length() < 5) {
                throw new BusinessException("REASON_REQUIRED: Write why these fees are being waived (at least 5 characters).");
            }
            auditService.logAction("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + fees + " on #" + p.getProjectIndex() + ". Reason: " + reason);""",
"Portal: waive needs a reason")
patch(PORTAL_CTRL,
"""    @PostMapping("/receivable/settings")
""",
"""    // fix162: REDUCE the accumulated storage fees to an agreed lower total (negotiation). Reason required, audited.
    @PostMapping("/receivable/reduce-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> reduceFees(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String why = body.get("reason") != null ? body.get("reason").trim() : "";
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the fees are being reduced (at least 5 characters).");
        }
        BigDecimal current = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        BigDecimal target;
        try {
            target = new BigDecimal(String.valueOf(body.get("newFees")).trim());
        } catch (Exception e) {
            throw new BusinessException("FEES_INVALID: Enter the new total storage fees as a number.");
        }
        if (target.compareTo(BigDecimal.ZERO) < 0) {
            throw new BusinessException("FEES_INVALID: The new total cannot be below zero.");
        }
        if (target.compareTo(current) >= 0) {
            throw new BusinessException("FEES_INVALID: The new total must be lower than the current UGX " + current.toPlainString() + ".");
        }
        p.setStorageFeesAccumulated(target);
        projectRepository.save(p);
        auditService.logAction("FEES_REDUCED", "Operator [" + op() + "] reduced storage fees on #" + p.getProjectIndex()
                + " from UGX " + current.toPlainString() + " to UGX " + target.toPlainString() + ". Reason: " + why);
        return receivable(id);
    }

    @PostMapping("/receivable/settings")
""",
"Portal: reduce-fees endpoint")
patch(PORTAL_CTRL,
"""auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex() + ".");""",
"""auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex()
                + " (monthly rate: " + (p.getStorageFeeOverride() != null ? "UGX " + p.getStorageFeeOverride().toPlainString() : "default")
                + ", fees paused until: " + (p.getNegotiationDeadline() != null ? p.getNegotiationDeadline().toString() : "not paused") + ").");""",
"Portal: settings audit shows the values")

# =========================== PART B -- FOLDER PAGE ===========================

# B1. services
patch(FOLDER_SVC,
"""  exit: (id, action) => api.post(`/land/portal/${id}/receivable/exit`, { action }).then(r => r.data),""",
"""  exit: (id, action, reason) => api.post(`/land/portal/${id}/receivable/exit`, reason ? { action, reason } : { action }).then(r => r.data),
  reduceFees: (id, newFees, reason) => api.post(`/land/portal/${id}/receivable/reduce-fees`, { newFees: String(newFees), reason }).then(r => r.data),""",
"Service: exit takes a reason; reduceFees")
patch(LAND_SVC,
"""    // PHASE 7: Director's Dashboard -- period is 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'""",
"""    // fix162: money safety
    reversePayment: async (projectId, paymentId, reason) => {
        await api.post(`/land/projects/${projectId}/payments/${paymentId}/reverse`, null, { params: { reason } });
    },

    undoRelease: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/undo-release`, null, { params: { reason } });
    },

    // PHASE 7: Director's Dashboard -- period is 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'""",
"Service: reversePayment + undoRelease")

# B2. one reason window for: reverse payment / reduce fees / waive fees / undo hand-over
patch(FOLDER_JSX,
"const [problemModal, setProblemModal] = useState({ open: false, note: '' });",
"""const [problemModal, setProblemModal] = useState({ open: false, note: '' });
    // fix162: ONE reason window for the money actions that need a written reason
    const [reasonModal, setReasonModal] = useState({ open: false, kind: '', title: '', info: '', confirmLabel: '', amountLabel: '', amount: '', reason: '', paymentId: null });
    const [reasonBusy, setReasonBusy] = useState(false);""",
"Folder: reason window state")
patch(FOLDER_JSX,
"    const handleUnlock = async () => { touchedRef.current = false;",
"""    const openReasonModal = (cfg) => setReasonModal({ open: true, kind: '', title: '', info: '', confirmLabel: 'CONFIRM', amountLabel: '', amount: '', reason: '', paymentId: null, ...cfg });
    const closeReasonModal = () => { if (!reasonBusy) setReasonModal(m => ({ ...m, open: false })); };
    const submitReasonModal = async () => {
        if (reasonBusy) return;
        const m = reasonModal; const why = (m.reason || '').trim();
        if (why.length < 5) { toast('WRITE THE REASON (AT LEAST 5 CHARACTERS)', 'error'); return; }
        if (m.kind === 'REDUCE' && (m.amount === '' || Number(m.amount) < 0 || Number(m.amount) >= storageFees)) { toast('ENTER A NEW TOTAL THAT IS LOWER THAN THE CURRENT FEES', 'error', 6000); return; }
        setReasonBusy(true);
        try {
            if (m.kind === 'REVERSE') { await landService.reversePayment(id, m.paymentId, why); toast('Payment reversed.', 'warn'); }
            else if (m.kind === 'REDUCE') { await folderPortalService.reduceFees(id, m.amount, why); toast('Storage fees reduced.', 'success'); }
            else if (m.kind === 'WAIVE') { await folderPortalService.exit(id, 'WAIVE', why); toast('Storage fees waived.', 'success'); }
            else if (m.kind === 'UNDO_RELEASE') { await landService.undoRelease(id, why); toast('Hand-over undone.', 'warn'); }
            await loadFolderData();
            setReasonModal(x => ({ ...x, open: false }));
        } catch (err) { toast('FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setReasonBusy(false); }
    };
    const handleUnlock = async () => { touchedRef.current = false;""",
"Folder: reason window handlers")

patch(FOLDER_JSX,
"<HardwareModal isOpen={problemModal.open}",
"""<HardwareModal isOpen={reasonModal.open} onClose={closeReasonModal} title={reasonModal.title}>
                <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>{reasonModal.info}</div>
                {reasonModal.kind === 'REDUCE' && (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>{reasonModal.amountLabel}</label>
                    <input type="number" min="0" className={modalStyles.modalInput} value={reasonModal.amount} autoFocus aria-label="New total storage fees"
                        onChange={e => setReasonModal(m => ({ ...m, amount: e.target.value }))} /></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>REASON (REQUIRED - SAVED IN THE AUDIT LOG)</label>
                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={reasonModal.reason} maxLength={300} autoFocus={reasonModal.kind !== 'REDUCE'} placeholder="e.g. Client paid in the wrong account..." aria-label="Reason"
                        onChange={e => setReasonModal(m => ({ ...m, reason: e.target.value }))} />
                    <span className={styles.probCount}>{reasonModal.reason.length}/300</span></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeReasonModal} disabled={reasonBusy}>CANCEL</button>
                    <HardwareButton type="button" variant="danger" onClick={submitReasonModal} loading={reasonBusy} icon={FiAlertTriangle}>{reasonModal.confirmLabel}</HardwareButton>
                </div>
            </HardwareModal>
<HardwareModal isOpen={problemModal.open}""",
"Folder: reason window markup")

# B3. Payment History: REVERSE + REVERSED / REVERSAL labels
patch(FOLDER_JSX,
"    const paymentCount = payments.length;",
"""    const paymentCount = payments.length;
    // fix162: which payments have been reversed (a REVERSAL line points at its original by id)
    const reversedIds = new Set(payments.filter(p => p.paymentType === 'REVERSAL' && p.notes)
        .map(p => { const m = String(p.notes).match(/^\\[REVERSAL OF ([0-9a-fA-F-]{36})\\]/); return m ? m[1] : null; }).filter(Boolean));""",
"Folder: reversed payments set")
patch(FOLDER_JSX,
"""<div className={styles.payMeta}><span className={styles.payType}>{pay.paymentType}</span><span className={styles.payBy}>by {pay.recordedBy}</span></div></div>
                                    <div className={styles.payRowRight}><div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div></div>""",
"""<div className={styles.payMeta}><span className={styles.payType}>{pay.paymentType}</span><span className={styles.payBy}>by {pay.recordedBy}</span>
                                        {reversedIds.has(pay.id) && <span className={styles.payReversed}>REVERSED</span>}
                                        {pay.paymentType === 'REVERSAL' && pay.notes && <span className={styles.payBy}>{String(pay.notes).replace(/^\\[REVERSAL OF [^\\]]*\\]\\s*/, '')}</span>}</div></div>
                                    <div className={styles.payRowRight}><div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                        {canMoney && pay.paymentType !== 'REVERSAL' && Number(pay.amountPaid) > 0 && !reversedIds.has(pay.id) && !project.landTitle?.isReleased && (
                                            <button type="button" className={styles.reverseBtn} title="Cancel this payment. The original line stays; a negative REVERSAL line is added."
                                                onClick={() => openReasonModal({ kind: 'REVERSE', paymentId: pay.id, title: 'REVERSE PAYMENT', confirmLabel: 'REVERSE PAYMENT',
                                                    info: 'This cancels UGX ' + fmt(pay.amountPaid) + ' paid on ' + new Date(pay.timestamp).toLocaleDateString() + '. The original line stays in the history, a negative REVERSAL line is added, and the amount paid goes down by the same amount.' })}>REVERSE</button>)}
                                    </div>""",
"Folder: payment rows show REVERSE / REVERSED / REVERSAL")

# B4. AMOUNT PAID is locked in edit mode; a changed TOTAL COST asks for a reason
patch(FOLDER_JSX,
"""<CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({ ...buffer, initialPayment: v })} />""",
"""<div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT PAID</label><span className={styles.autoCalcBadge}>LOCKED</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={(Number(buffer.initialPayment) || 0).toLocaleString()} disabled />
                                    <span className={styles.inputHint}>Changes only through RECORD PAYMENT, or REVERSE in Payment History.</span></div>""",
"Folder: amount paid locked in edit mode")
patch(FOLDER_JSX,
"    const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);",
"""    const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);
    const costChanged = isEditing && (Number(buffer?.totalCost) || 0) !== (Number(project?.totalCost) || 0);""",
"Folder: costChanged flag")
patch(FOLDER_JSX,
"""<input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                            </div>) : isReceivable""",
"""<input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                                {costChanged && (<SmartInput label="REASON FOR COST CHANGE" value={buffer.costChangeReason || ''} required error={fieldErrors.costChangeReason}
                                    onChange={e => touchedSetBuffer({ ...buffer, costChangeReason: e.target.value })} />)}
                            </div>) : isReceivable""",
"Folder: reason field appears when the cost changes")
patch(FOLDER_JSX,
"        setFieldErrors({}); setCommitting(true);",
"""        if ((Number(buffer.totalCost) || 0) !== (Number(project.totalCost) || 0) && (buffer.costChangeReason || '').trim().length < 5) {
            setFieldErrors({ costChangeReason: 'Required' }); toast('WRITE WHY THE TOTAL COST CHANGED (AT LEAST 5 CHARACTERS)', 'error', 6000); return;
        }
        setFieldErrors({}); setCommitting(true);""",
"Folder: block save until the cost-change reason is written")
patch(FOLDER_JSX,
"await landService.updateMasterFolder(id, { ...buffer, totalCost: Number(buffer.totalCost) || 0, initialPayment: Number(buffer.initialPayment) || 0 });",
"await landService.updateMasterFolder(id, { ...buffer, totalCost: Number(buffer.totalCost) || 0, initialPayment: Number(buffer.initialPayment) || 0, costChangeReason: (buffer.costChangeReason || '').trim(), expectedTotalCost: Number(project.totalCost) || 0 });",
"Folder: save sends the reason and the cost this form was loaded with")

# B5. Storage: WAIVE goes through the reason window; REDUCE FEES button
patch(FOLDER_JSX,
"""onClick={() => askReceivable('WAIVE')} disabled={recvBusy}><FiTrash2 aria-hidden="true" /> WAIVE FEES</button>""",
"""onClick={() => openReasonModal({ kind: 'WAIVE', title: 'WAIVE STORAGE FEES', confirmLabel: 'WAIVE FEES',
                                        info: 'This forgives ALL UGX ' + fmt(storageFees) + ' of storage fees and takes this project out of receivables. It cannot be undone.' })} disabled={recvBusy}><FiTrash2 aria-hidden="true" /> WAIVE FEES</button>
                                    {storageFees > 0 && <button type="button" className={styles.ghostBtn} onClick={() => openReasonModal({ kind: 'REDUCE', title: 'REDUCE STORAGE FEES', confirmLabel: 'REDUCE FEES', amountLabel: 'NEW TOTAL STORAGE FEES (UGX)',
                                        info: 'The client negotiated a lower fee. Current fees are UGX ' + fmt(storageFees) + '. Type the agreed lower total; the project stays in receivables.' })} disabled={recvBusy}><FiDollarSign aria-hidden="true" /> REDUCE FEES</button>}""",
"Folder: waive uses the reason window; REDUCE FEES button")
patch(FOLDER_JSX,
"SET ASIDE, ADD FEES TO COST and WAIVE FEES each take this project OUT of receivables.",
"SET ASIDE, ADD FEES TO COST and WAIVE FEES each take this project OUT of receivables. REDUCE FEES keeps it in.",
"Folder: exits hint mentions REDUCE FEES")

# B6. Hand-over: greyed until NOTHING is owed (fees count), and an UNDO for directors
patch(FOLDER_JSX,
"""                            ? <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled title="The client has received the title deed."><FiCheckCircle aria-hidden="true" /> HANDED OVER</button>
                            : <button className={styles.releaseBtn} onClick={handleRelease} disabled={amountPaid < totalValue}
                                title={amountPaid < totalValue ? 'Cannot hand over yet: UGX ' + fmt(totalValue - amountPaid) + ' is still owed.' : 'Record that the client has received the title deed.'}><FiCheckCircle aria-hidden="true" /> HAND OVER TITLE</button>)}""",
"""                            ? (<>
                                <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled title="The client has received the title deed."><FiCheckCircle aria-hidden="true" /> HANDED OVER</button>
                                <button type="button" className={styles.ghostBtn} title="Mark the title as NOT handed over again (reason required)."
                                    onClick={() => openReasonModal({ kind: 'UNDO_RELEASE', title: 'UNDO HAND-OVER', confirmLabel: 'UNDO HAND-OVER',
                                        info: 'This marks the title as NOT handed over again and puts the plot back to ACTIVE. Use it only if the hand-over was recorded by mistake.' })}><FiUnlock aria-hidden="true" /> UNDO</button>
                              </>)
                            : <button className={styles.releaseBtn} onClick={handleRelease} disabled={amountOwed > 0}
                                title={amountOwed > 0 ? 'Cannot hand over yet: UGX ' + fmt(amountOwed) + ' is still owed.' : 'Record that the client has received the title deed.'}><FiCheckCircle aria-hidden="true" /> HAND OVER TITLE</button>)}""",
"Folder: hand-over waits for storage fees too; UNDO button")

# B7. Stage panel stays mounted while TITLE READY is on, so UNDO / CANCEL can really un-tick the last stage
patch(FOLDER_JSX,
"""                {!project.landTitle && !buffer.convertToTitle && (
<section className={styles.hwPanel} aria-label="Stage Checklist" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>""",
"""                {!project.landTitle && (
<section className={styles.hwPanel} aria-label="Stage Checklist" style={(activeTab !== 'OVERVIEW' || buffer.convertToTitle) ? { display: 'none' } : {}}>""",
"Folder: stage checklist stays mounted (hidden) while TITLE READY is on")
patch(FOLDER_JSX,
"if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); } };",
"if (ok) { if (buffer.convertToTitle && !project.landTitle) { try { await stageChecklistRef.current?.setLastStageCompletion(false); } catch {} } touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); } };",
"Folder: CANCEL also un-ticks the last stage if TITLE READY was switched on")

# B8. styles
patch(FOLDER_CSS,
".releaseBtnDone{background:#10b981;border-color:#10b981;color:#fff;opacity:0.9;cursor:default;}",
""".releaseBtnDone{background:#10b981;border-color:#10b981;color:#fff;opacity:0.9;cursor:default;}
.payReversed{margin-left:8px;padding:1px 6px;border-radius:4px;background:rgba(239,68,68,0.16);border:1px solid rgba(239,68,68,0.5);color:#fca5a5;font-size:9px;font-weight:900;letter-spacing:1px;}
.reverseBtn{margin-top:6px;padding:3px 9px;border-radius:5px;background:transparent;border:1px solid rgba(239,68,68,0.45);color:#fca5a5;font-size:9px;font-weight:900;letter-spacing:1px;cursor:pointer;}
.reverseBtn:hover{background:#ef4444;color:#fff;border-color:#ef4444;}""",
"Folder CSS: reverse button + REVERSED tag")

# =========================== PART C -- LOOK (Audit + Expenses; skipped automatically if already applied) ===========================
# ---- 1. Audit: subtler outer border, inner border = Expenses table's (2px #f2ede4) ----
patch(AUDIT_CSS,
      "background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius);",
      "background: var(--panel-bg); border: 1px solid var(--orange-border); border-radius: var(--radius);",
      "Audit CSS: outer border thinner (2px -> 1px)")
patch(AUDIT_CSS,
      "background: #ebe5d8; border: 1px solid #fff; border-radius: 10px;",
      "background: #ebe5d8; border: 2px solid #f2ede4; border-radius: 10px;",
      "Audit CSS: inner border same thickness/colour as Expenses table")

# ---- 2. Audit: zebra rows + peach hover (zebra BEFORE hover BEFORE .expanded so the order of wins is right) ----
patch(AUDIT_CSS,
      ".logRow:hover { background: rgba(26, 46, 48, 0.09); }",
      ".logRow:nth-child(even) { background: rgba(26, 46, 48, 0.09); }\n.logRow:hover { background: rgba(238, 140, 58, 0.26); }",
      "Audit CSS: alternating rows + peach hover")

# ---- 3. Expenses: stronger zebra + peach hover ----
patch(EXP_CSS,
      ".ledgerTable tbody tr.row:nth-child(even) td { background: rgba(26,46,48,0.075); }",
      ".ledgerTable tbody tr.row:nth-child(even) td { background: rgba(26,46,48,0.12); }",
      "Expenses CSS: alternating rows a little stronger")
patch(EXP_CSS,
      ".ledgerTable tbody tr.row:hover td { background: rgba(26,46,48,0.14); }",
      ".ledgerTable tbody tr.row:hover td { background: rgba(238,140,58,0.26); }",
      "Expenses CSS: peach hover")

# ---- 4. Colour by group ----
CAT_OLD = "/* fix159: simple basic colours. Colour by how often an action happens.\n   COMMON = the actions staff do all day, each with its OWN basic colour (blue, green, yellow, purple, orange, cyan, pink).\n   RARE   = everything else, one shared colour per TYPE: red = destructive / privileged, brown = changes money or a\n            record, teal = contact history, grey = minor. An unlisted code counts as rare / minor. */\nconst COMMON_COLOR = {\n    RECORD_UPDATED:          '#2563eb',  // blue\n    EDIT_MODE_OPENED:        '#9333ea',  // purple\n    DOCUMENT_UPLOADED:       '#eab308',  // yellow\n    DOCUMENT_CATEGORY_ADDED: '#06b6d4',  // cyan\n    RECEIVABLE_ENTER:        '#f97316',  // orange\n    PAYMENT_RECORDED:        '#16a34a',  // green\n    EXPENSE_LOGGED:          '#ec4899',  // pink\n};\nconst RARE_COLOR = {\n    high:  '#dc2626',  // red\n    med:   '#92400e',  // brown\n    intel: '#0d9488',  // teal\n    low:   '#6b7280',  // grey\n};\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (COMMON_COLOR[key]) return COMMON_COLOR[key];\n    return RARE_COLOR[severityOf(key)] || RARE_COLOR.low;\n};\n"
CAT_NEW = "/* fix160: colour by GROUP. Six basic colours, one per family of actions:\n   blue   = RECORDS + DOCUMENTS   green  = MONEY          orange = RECEIVABLES\n   purple = PIPELINE              yellow = CONTACT & NOTES  red    = ACCESS & STAFF\n   An unlisted code is neutral grey. */\nconst GROUP_COLOR = {\n    'RECORDS':         '#2563eb',\n    'DOCUMENTS':       '#2563eb',\n    'MONEY':           '#16a34a',\n    'RECEIVABLES':     '#f97316',\n    'PIPELINE':        '#9333ea',\n    'CONTACT & NOTES': '#eab308',\n    'ACCESS & STAFF':  '#dc2626',\n};\nconst GROUP_OF = {};\nACTION_GROUPS.forEach(g => g.actions.forEach(a => { GROUP_OF[a.code] = g.group; }));\nexport const actionColor = (code) => GROUP_COLOR[GROUP_OF[String(code || '')]] || '#6b7280';\n"
patch(AUDIT_CAT, CAT_OLD, CAT_NEW, "Catalogue: six basic colours, one per group")


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