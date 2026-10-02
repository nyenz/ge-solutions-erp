#!/usr/bin/env python3
# PATH: fix171.py
# GOLDEN SEED -- fix171: "Storage fees already paid" at intake, wired through every page and report.
#
# THE PROBLEM: a Legacy Title / receivable project could be entered with an Initial Storage Fee (fees already charged),
# but there was NO way to say how much of it the client had already paid. Anything typed as Initial Payment counted as
# TITLE-work money, so the folder showed too little work owed and too many fees unpaid (e.g. cost 1,000,000 + fees
# 200,000 already paid showed 800,000 work left and 200,000 fees unpaid). The only workaround, recording a STORAGE
# payment afterwards, was dated today, which set the last-payment date and locked the client from recovery calls.
#
#   1. INTAKE: new box "Storage Fees Already Paid" (Legacy Title, under the Storage Fees heading). It is counted as paid
#      toward the FEES (storageFeesPaid), never toward the title work, and it does NOT set the last-payment date.
#      Initial Payment is now clearly labelled as TITLE WORK. The summary shows fees charged, fees paid and an Amount
#      Owed that includes the unpaid fees (before it ignored fees completely).
#   2. SERVER CHECKS: fees paid cannot exceed the initial fee, whole shillings, no negatives, initial payment cannot
#      exceed the total cost, and storage fees on a project that would not be in receivables (title already fully paid)
#      are now REFUSED with a clear message instead of being silently dropped.
#   3. PAYMENT HISTORY: the intake writes two honest lines, "DEPOSIT AT INTAKE / TITLE" and "DEPOSIT AT INTAKE / STORAGE
#      FEES", each with the balance after intake (fees included). Reversing the storage line works like any storage payment.
#   4. EDIT FOLDER: changing the cost of a receivable project compared the new cost with ALL money paid (fees included)
#      and set the frozen debt from it; both now use the TITLE money only, so a paid fee can no longer block a cost
#      change or shrink the debt.
#   5. PROGRESS AND CRITICAL: the Ledger progress bar and the CRITICAL rule now count TITLE money only, so paid fees
#      never make a project look "paid up" (they would have, now that fees can be entered as paid).
#   6. SHOWN EVERYWHERE: Ledger and Client Ledger fee lines say "(UGX x paid)"; Payments page puts intake storage
#      deposits under the receivables card and labels them STORAGE FEES; Report Studio gets Storage Fees Paid / Unpaid
#      for projects and Storage Fees Paid for clients, and its Balance Owed / Percent Paid now include fees correctly;
#      the Receivable Breakdown CSV gets two new last columns (STORAGE_FEES_PAID, STORAGE_FEES_UNPAID).
#
# NOT in this fix: any change to how fees accrue, a date for older payments (listed as an open point), any database
# change (storage_fees_paid already exists).
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix171"
COMMIT_MSG = "fix171: Storage Fees Already Paid at intake, wired through folder/ledger/payments/reports; edit-cost and progress/critical now use title money only"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_LEDGER_JSX = os.path.join(SRC, "pages", "Ledger", "LedgerPage.jsx")
F_CLIENTLEDGER_JSX = os.path.join(SRC, "pages", "Clients", "ClientLedgerPage.jsx")
F_PAYMENTS_JSX = os.path.join(SRC, "pages", "Payments", "PaymentsPage.jsx")
F_REPORTDATA_JS = os.path.join(SRC, "pages", "Reports", "reportData.js")
F_FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
F_ENTRY_DTO = os.path.join(JAVA, "modules", "land", "dto", "LandEntryRequest.java")
F_LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
F_REPORT_SERVICE = os.path.join(JAVA, "modules", "land", "service", "ReportService.java")
F_NOTE_CTRL = os.path.join(JAVA, "modules", "client", "controller", "RecoveryNoteController.java")
F_GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
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
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (F_ENTRY_DTO, F_LAND_SERVICE, F_NOTE_CTRL, F_REPORT_SERVICE, F_INTAKE_JSX, F_LEDGER_JSX, F_CLIENTLEDGER_JSX, F_PAYMENTS_JSX, F_REPORTDATA_JS, F_FOLDER_JSX, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_ENTRY_DTO,
      "\n".join([
          "    private java.math.BigDecimal initialStorageFee;"
      ]),
      "\n".join([
          "    private java.math.BigDecimal initialStorageFee;",
          "    // fix171: how much of the initial storage fee the client has ALREADY paid (counts toward the fees, not the title work)",
          "    private java.math.BigDecimal initialStorageFeePaid;"
      ]),
      "DTO: initialStorageFeePaid")

patch(F_LAND_SERVICE,
      "\n".join([
          "        BigDecimal outstanding = totalCost.subtract(initialPayment);",
          "",
          "        boolean startAsReceivable = request.isStartAsReceivable();"
      ]),
      "\n".join([
          "        BigDecimal outstanding = totalCost.subtract(initialPayment);",
          "",
          "        boolean startAsReceivable = request.isStartAsReceivable();",
          "",
          "        // fix171: storage fees already charged / already paid at intake, checked here because the server must not trust the page",
          "        BigDecimal initialFees = request.getInitialStorageFee() != null ? request.getInitialStorageFee() : BigDecimal.ZERO;",
          "        BigDecimal initialFeesPaid = request.getInitialStorageFeePaid() != null ? request.getInitialStorageFeePaid() : BigDecimal.ZERO;",
          "        if (initialPayment.signum() < 0 || initialFees.signum() < 0 || initialFeesPaid.signum() < 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"AMOUNT_INVALID: Payments and storage fees cannot be negative.\");",
          "        }",
          "        if (initialPayment.compareTo(totalCost) > 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"INITIAL_PAYMENT_TOO_HIGH: The initial payment (UGX \" + initialPayment.toPlainString()",
          "                    + \") is more than the total cost (UGX \" + totalCost.toPlainString() + \").\");",
          "        }",
          "        if (initialFeesPaid.stripTrailingZeros().scale() > 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"STORAGE_PAID_INVALID: Enter whole shillings only for the storage fees already paid.\");",
          "        }",
          "        if (initialFeesPaid.compareTo(initialFees) > 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"STORAGE_PAID_TOO_HIGH: Storage fees already paid (UGX \" + initialFeesPaid.toPlainString()",
          "                    + \") cannot be more than the initial storage fee (UGX \" + initialFees.toPlainString() + \").\");",
          "        }",
          "        if (!(startAsReceivable && outstanding.signum() > 0) && (initialFees.signum() > 0 || initialFeesPaid.signum() > 0)) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"STORAGE_NOT_APPLICABLE: Storage fees only exist on a project in receivables. \"",
          "                    + \"This title work is already fully paid, so clear the storage fee boxes.\");",
          "        }"
      ]),
      "Intake: validate the storage fees charged / already paid")

patch(F_LAND_SERVICE,
      "\n".join([
          "                .totalCost(totalCost)",
          "                .amountPaid(initialPayment)",
          "                .isLegacy(request.isLegacy())"
      ]),
      "\n".join([
          "                .totalCost(totalCost)",
          "                .amountPaid(initialPayment.add(initialFeesPaid))   // fix171: title money + storage-fee money (fees paid is 0 unless receivable)",
          "                .isLegacy(request.isLegacy())"
      ]),
      "Intake: total paid = title payment + storage fees already paid")

patch(F_LAND_SERVICE,
      "\n".join([
          "            BigDecimal initialFees = request.getInitialStorageFee() != null",
          "                    ? request.getInitialStorageFee() : BigDecimal.ZERO;",
          "            builder.isReceivable(true)",
          "                   .receivableStartDate(LocalDateTime.now())",
          "                   .originalDebt(outstanding)",
          "                   .storageFeesAccumulated(initialFees);"
      ]),
      "\n".join([
          "            builder.isReceivable(true)",
          "                   .receivableStartDate(LocalDateTime.now())",
          "                   .originalDebt(outstanding)",
          "                   .storageFeesAccumulated(initialFees)",
          "                   .storageFeesPaid(initialFeesPaid);   // fix171"
      ]),
      "Intake: store the fees already paid on the project")

patch(F_LAND_SERVICE,
      "\n".join([
          "        // Record initial payment if any",
          "        if (initialPayment.compareTo(BigDecimal.ZERO) > 0) {",
          "            PaymentRecord initialRecord = PaymentRecord.builder()",
          "                    .projectId(saved.getId())",
          "                    .amountPaid(initialPayment)",
          "                    .paymentType(\"INITIAL_DEPOSIT\")",
          "                    .recordedBy(getCurrentOperator())",
          "                    .notes(\"Initial deposit at intake\")",
          "                    .balanceAfter(outstanding)",
          "                    .build();",
          "            paymentRecordRepository.save(initialRecord);",
          "            saved.setLastPaymentDate(LocalDateTime.now());",
          "            projectRepository.save(saved);",
          "        }"
      ]),
      "\n".join([
          "        // Record initial payment if any",
          "        // fix171: the balance shown on the history lines includes the storage fees, and the money that was paid",
          "        // toward fees gets its OWN line (allocation STORAGE) so the folder, payments page and reports can tell them apart.",
          "        BigDecimal balanceAtIntake = saved.isReceivable() ? saved.receivableTotalOwed() : outstanding;",
          "        if (initialPayment.compareTo(BigDecimal.ZERO) > 0) {",
          "            PaymentRecord initialRecord = PaymentRecord.builder()",
          "                    .projectId(saved.getId())",
          "                    .amountPaid(initialPayment)",
          "                    .paymentType(\"INITIAL_DEPOSIT\")",
          "                    .recordedBy(getCurrentOperator())",
          "                    .notes(\"Initial deposit at intake\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"TITLE\")",
          "                    .build();",
          "            paymentRecordRepository.save(initialRecord);",
          "            saved.setLastPaymentDate(LocalDateTime.now());",
          "            projectRepository.save(saved);",
          "        }",
          "        if (initialFeesPaid.compareTo(BigDecimal.ZERO) > 0) {",
          "            // deliberately NOT setting lastPaymentDate: this money was paid before the project was entered, on an",
          "            // unknown date, so it must not turn the recovery badge green or lock the client from calls for 30 days.",
          "            PaymentRecord feesRecord = PaymentRecord.builder()",
          "                    .projectId(saved.getId())",
          "                    .amountPaid(initialFeesPaid)",
          "                    .paymentType(\"INITIAL_DEPOSIT\")",
          "                    .recordedBy(getCurrentOperator())",
          "                    .notes(\"Storage fees already paid before entry (recorded at intake)\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"STORAGE\")",
          "                    .build();",
          "            paymentRecordRepository.save(feesRecord);",
          "        }"
      ]),
      "Intake: separate TITLE and STORAGE deposit lines, fees line keeps the last-payment date untouched")

patch(F_LAND_SERVICE,
      "\n".join([
          "                + plotOrIndex + \" as RECEIVABLE at intake. Debt: UGX \" + outstanding);"
      ]),
      "\n".join([
          "                + plotOrIndex + \" as RECEIVABLE at intake. Title debt: UGX \" + outstanding",
          "                + \". Storage fees: UGX \" + initialFees + \" (UGX \" + initialFeesPaid + \" already paid).\");"
      ]),
      "Intake: audit line names the storage fees and what was already paid")

patch(F_LAND_SERVICE,
      "\n".join([
          "            if (newTotalCost.compareTo(currentPaid) < 0) {",
          "                throw new BusinessException(\"COST_BELOW_PAID: The new cost (UGX \" + newTotalCost.toPlainString()",
          "                        + \") is lower than the UGX \" + currentPaid.toPlainString()"
      ]),
      "\n".join([
          "            // fix171: only the money paid toward the TITLE work counts here (paid storage fees are not part of the cost)",
          "            BigDecimal titlePaidNow = currentPaid.subtract(project.storagePaidSafe()).max(BigDecimal.ZERO);",
          "            if (newTotalCost.compareTo(titlePaidNow) < 0) {",
          "                throw new BusinessException(\"COST_BELOW_PAID: The new cost (UGX \" + newTotalCost.toPlainString()",
          "                        + \") is lower than the UGX \" + titlePaidNow.toPlainString()"
      ]),
      "Edit folder: cost cannot go below the TITLE money paid (fees excluded)")

patch(F_LAND_SERVICE,
      "\n".join([
          "            project.setOriginalDebt(newTotalCost.subtract(amtPaid).max(BigDecimal.ZERO));"
      ]),
      "\n".join([
          "            project.setOriginalDebt(newTotalCost.subtract(amtPaid.subtract(project.storagePaidSafe())).max(BigDecimal.ZERO));   // fix171: title money only"
      ]),
      "Edit folder: frozen debt ignores paid storage fees")

patch(F_NOTE_CTRL,
      "\n".join([
          "m.put(\"storage\", storage);"
      ]),
      "\n".join([
          "m.put(\"storage\", storage);",
          "m.put(\"storagePaid\", ps.stream().map(com.gesolutions.erp.modules.land.model.LandProject::storagePaidSafe).reduce(java.math.BigDecimal.ZERO, java.math.BigDecimal::add));"
      ]),
      "Client ledger: storage fees paid per client")

patch(F_REPORT_SERVICE,
      "\n".join([
          "MONTHS_IN_RECEIVABLE,TOTAL_PAID,TOTAL_OWED\").append(NEW_LINE);"
      ]),
      "\n".join([
          "MONTHS_IN_RECEIVABLE,TOTAL_PAID,TOTAL_OWED,STORAGE_FEES_PAID,STORAGE_FEES_UNPAID\").append(NEW_LINE);"
      ]),
      "Receivable CSV: two new last columns (header)")

patch(F_REPORT_SERVICE,
      "\n".join([
          "               .append(totalOwed.max(java.math.BigDecimal.ZERO)).append(NEW_LINE);"
      ]),
      "\n".join([
          "               .append(totalOwed.max(java.math.BigDecimal.ZERO)).append(CSV_DIVIDER)",
          "               .append(p.storagePaidSafe()).append(CSV_DIVIDER)",
          "               .append(p.storageUnpaid()).append(NEW_LINE);"
      ]),
      "Receivable CSV: two new last columns (rows)")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const [initialStorageFee, setInitialStorageFee] = useState(0);"
      ]),
      "\n".join([
          "    const [initialStorageFee, setInitialStorageFee] = useState(0);",
          "    const [initialStorageFeePaid, setInitialStorageFeePaid] = useState(0);   // fix171"
      ]),
      "Intake: state for storage fees already paid")

patch(F_INTAKE_JSX,
      "\n".join([
          "        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) { toast('Initial Payment is required (0 or more).', 'error'); return false; }"
      ]),
      "\n".join([
          "        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) { toast('Initial Payment is required (0 or more).', 'error'); return false; }",
          "        // fix171: the same checks the server makes, so the message shows before anything is sent",
          "        if (Number(initialPayment) > Number(totalCost)) { toast('Initial Payment cannot be more than the Total Cost.', 'error'); return false; }",
          "        if (isLegacy) {",
          "            const feeCharged = Number(initialStorageFee) || 0;",
          "            const feePaid = Number(initialStorageFeePaid) || 0;",
          "            if (feeCharged < 0 || feePaid < 0) { toast('Storage fees cannot be negative.', 'error'); return false; }",
          "            if (!Number.isInteger(feePaid)) { toast('Storage Fees Already Paid: whole shillings only.', 'error'); return false; }",
          "            if (feePaid > feeCharged) { toast('Storage Fees Already Paid cannot be more than the Initial Storage Fee.', 'error'); return false; }",
          "            if (Number(initialPayment) >= Number(totalCost) && (feeCharged > 0 || feePaid > 0)) {",
          "                toast('The title work is already fully paid, so this project will not be in receivables and cannot carry storage fees. Clear the storage fee boxes.', 'error'); return false;",
          "            }",
          "        }"
      ]),
      "Intake: validation for the new field")

patch(F_INTAKE_JSX,
      "\n".join([
          "                payload.initialStorageFee = Number(initialStorageFee) || 0;"
      ]),
      "\n".join([
          "                payload.initialStorageFee = Number(initialStorageFee) || 0;",
          "                payload.initialStorageFeePaid = Number(initialStorageFeePaid) || 0;"
      ]),
      "Intake: send the new field")

patch(F_INTAKE_JSX,
      "\n".join([
          "setInitialStorageFee(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);"
      ]),
      "\n".join([
          "setInitialStorageFee(0); setInitialStorageFeePaid(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);"
      ]),
      "Intake: clear the new field on reset")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));"
      ]),
      "\n".join([
          "    // fix171: Amount Owed now includes the storage fees still unpaid (Legacy Title only, and only while the title work is not fully paid)",
          "    const titleLeft = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));",
          "    const feesCharged = isLegacy ? Math.max(0, Number(initialStorageFee) || 0) : 0;",
          "    const feesPaidNow = Math.min(feesCharged, Math.max(0, Number(initialStorageFeePaid) || 0));",
          "    const amountOwed = titleLeft + (titleLeft > 0 ? feesCharged - feesPaidNow : 0);"
      ]),
      "Intake: Amount Owed includes unpaid storage fees")

patch(F_INTAKE_JSX,
      "\n".join([
          "                            <label className={`${styles.label} ${styles.required}`}>Initial Payment</label>",
          "                            <input type=\"number\" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />"
      ]),
      "\n".join([
          "                            <label className={`${styles.label} ${styles.required}`}>{isLegacy ? 'Initial Payment (Title Work)' : 'Initial Payment'}</label>",
          "                            <input type=\"number\" min=\"0\" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />",
          "                            {isLegacy && <p className={styles.hint}>Money paid toward the title work only. Storage fees already paid go in the Storage Fees box below.</p>}"
      ]),
      "Intake: Initial Payment is labelled as title work")

patch(F_INTAKE_JSX,
      "\n".join([
          "                                    <p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>",
          "                                </div>",
          "                            </div>",
          "                        </>"
      ]),
      "\n".join([
          "                                    <p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>",
          "                                </div>",
          "                                <div className={styles.field}>",
          "                                    <label className={styles.label}>Storage Fees Already Paid</label>",
          "                                    <input type=\"number\" min=\"0\" className={styles.input} value={initialStorageFeePaid} onChange={e => { setInitialStorageFeePaid(e.target.value); markDirty(); }} />",
          "                                    <p className={styles.hint}>Part of the Initial Storage Fee the client has already paid. Counted toward the fees, not the title work, and it does not count as a recent payment.</p>",
          "                                </div>",
          "                            </div>",
          "                        </>"
      ]),
      "Intake: the new Storage Fees Already Paid box")

patch(F_INTAKE_JSX,
      "\n".join([
          "                        <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>",
          "                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}"
      ]),
      "\n".join([
          "                        <div className={styles.finRow}><span>{isLegacy ? 'Initial Payment (Title Work)' : 'Initial Payment'}</span><span>{Number(initialPayment) || 0}</span></div>",
          "                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}",
          "                        {isLegacy && <div className={styles.finRow}><span>Storage Fees Already Paid</span><span>{Number(initialStorageFeePaid) || 0}</span></div>}"
      ]),
      "Intake: summary shows the fees paid")

patch(F_LEDGER_JSX,
      "\n".join([
          "const isCriticalProject = (p) => (p.totalCost || 0) > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25;"
      ]),
      "\n".join([
          "// fix171: progress and CRITICAL count only the money paid toward the TITLE work (paid storage fees are not part of the cost)",
          "const titlePaidOf = (p) => Math.max(0, (p.amountPaid || 0) - (p.storageFeesPaid || 0));",
          "const isCriticalProject = (p) => (p.totalCost || 0) > 0 && (titlePaidOf(p) / p.totalCost) < 0.25;"
      ]),
      "Ledger: critical rule uses title money only")

patch(F_LEDGER_JSX,
      "\n".join([
          "const pct = proj.totalCost > 0 ? Math.min(((proj.amountPaid || 0) / proj.totalCost) * 100, 100) : 0;"
      ]),
      "\n".join([
          "const pct = proj.totalCost > 0 ? Math.min((titlePaidOf(proj) / proj.totalCost) * 100, 100) : 0;"
      ]),
      "Ledger: progress bar uses title money only")

patch(F_LEDGER_JSX,
      "\n".join([
          "<div className={styles.feesLine}>+UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees</div>"
      ]),
      "\n".join([
          "<div className={styles.feesLine}>+UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees{Number(proj.storageFeesPaid || 0) > 0 ? ' (UGX ' + Number(proj.storageFeesPaid).toLocaleString() + ' paid)' : ''}</div>"
      ]),
      "Ledger: fee line says how much is paid")

patch(F_CLIENTLEDGER_JSX,
      "\n".join([
          "                                const storageFees = Number(c.storage || 0);"
      ]),
      "\n".join([
          "                                const storageFees = Number(c.storage || 0);",
          "                                const storagePaid = Number(c.storagePaid || 0);"
      ]),
      "Client Ledger: storage paid per client")

patch(F_CLIENTLEDGER_JSX,
      "\n".join([
          "<div className={styles.feesLine}>+UGX {storageFees.toLocaleString()} storage fees</div>"
      ]),
      "\n".join([
          "<div className={styles.feesLine}>+UGX {storageFees.toLocaleString()} storage fees{storagePaid > 0 ? ' (UGX ' + storagePaid.toLocaleString() + ' paid)' : ''}</div>"
      ]),
      "Client Ledger: fee line says how much is paid")

patch(F_PAYMENTS_JSX,
      "\n".join([
          "    const titleTotal     = useMemo(() => filtered.filter(p => p.paymentType !== 'RECEIVABLE_PARTIAL').reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);",
          "    const storageTotal   = useMemo(() => filtered.filter(p => p.paymentType === 'RECEIVABLE_PARTIAL').reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);"
      ]),
      "\n".join([
          "    // fix171: a payment belongs to the RECEIVABLES card when it was made in receivables OR is storage-fee money (this",
          "    // includes storage fees recorded at intake, and a reversal of a storage payment)",
          "    const inReceivables  = (p) => p.paymentType === 'RECEIVABLE_PARTIAL' || p.allocation === 'STORAGE';",
          "    const titleTotal     = useMemo(() => filtered.filter(p => !inReceivables(p)).reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);",
          "    const storageTotal   = useMemo(() => filtered.filter(p => inReceivables(p)).reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);"
      ]),
      "Payments: cards classify storage money correctly")

patch(F_PAYMENTS_JSX,
      "\n".join([
          "<span>{filtered.filter(p => p.paymentType !== 'RECEIVABLE_PARTIAL').length} records</span>"
      ]),
      "\n".join([
          "<span>{filtered.filter(p => !inReceivables(p)).length} records</span>"
      ]),
      "Payments: title card record count")

patch(F_PAYMENTS_JSX,
      "\n".join([
          "<span>{filtered.filter(p => p.paymentType === 'RECEIVABLE_PARTIAL').length} records</span>"
      ]),
      "\n".join([
          "<span>{filtered.filter(p => inReceivables(p)).length} records</span>"
      ]),
      "Payments: receivables card record count")

patch(F_PAYMENTS_JSX,
      "\n".join([
          "                                                {TYPE_LABELS[pay.paymentType] || pay.paymentType}",
          "                                            </span>"
      ]),
      "\n".join([
          "                                                {TYPE_LABELS[pay.paymentType] || pay.paymentType}",
          "                                                {pay.allocation === 'STORAGE' ? ' - STORAGE FEES' : ''}",
          "                                            </span>"
      ]),
      "Payments: storage lines are labelled")

patch(F_REPORTDATA_JS,
      "\n".join([
          "  f('balance', 'Balance Owed', 'money', p => Math.max(0, num(p.totalCost) - num(p.amountPaid)), { money: true }),",
          "  f('storage', 'Storage Fees', 'money', p => num(p.storageFeesAccumulated), { money: true }),"
      ]),
      "\n".join([
          "  // fix171: a project in receivables also owes its storage fees, and paid fees are not part of the title cost",
          "  f('balance', 'Balance Owed', 'money', p => Math.max(0, num(p.totalCost) + (p.isReceivable ? num(p.storageFeesAccumulated) : 0) - num(p.amountPaid)), { money: true }),",
          "  f('storage', 'Storage Fees', 'money', p => num(p.storageFeesAccumulated), { money: true }),",
          "  f('storagePaid', 'Storage Fees Paid', 'money', p => num(p.storageFeesPaid), { money: true }),",
          "  f('storageUnpaid', 'Storage Fees Unpaid', 'money', p => Math.max(0, num(p.storageFeesAccumulated) - num(p.storageFeesPaid)), { money: true }),"
      ]),
      "Reports: project balance includes fees; paid / unpaid fee fields")

patch(F_REPORTDATA_JS,
      "\n".join([
          "  f('pctPaid', 'Percent Paid', 'percent', p => (num(p.totalCost) > 0 ? Math.round((num(p.amountPaid) / num(p.totalCost)) * 100) : 0), { money: true }),"
      ]),
      "\n".join([
          "  f('pctPaid', 'Percent Paid', 'percent', p => (num(p.totalCost) > 0 ? Math.round(((num(p.amountPaid) - num(p.storageFeesPaid)) / num(p.totalCost)) * 100) : 0), { money: true }),"
      ]),
      "Reports: project percent paid counts title money only")

patch(F_REPORTDATA_JS,
      "\n".join([
          "  f('storage', 'Storage Fees', 'money', c => num(c.storage), { money: true }),"
      ]),
      "\n".join([
          "  f('storage', 'Storage Fees', 'money', c => num(c.storage), { money: true }),",
          "  f('storagePaid', 'Storage Fees Paid', 'money', c => num(c.storagePaid), { money: true }),"
      ]),
      "Reports: client storage fees paid")

patch(F_FOLDER_JSX,
      "\n".join([
          "initialPayment: String(data.project?.amountPaid || 0),"
      ]),
      "\n".join([
          "initialPayment: String(Math.max(0, Number(data.project?.amountPaid || 0) - Number(data.project?.storageFeesPaid || 0))),"
      ]),
      "Folder edit form: the paid figure shown is the TITLE money (fees excluded)")

patch(F_GUIDE,
      "\n".join([
          "- **Storage fee rules (fix167):**"
      ]),
      "\n".join([
          "- **Storage fees already paid at intake (fix171):** a Legacy Title entry has `Initial Payment (Title Work)`, `Initial Storage Fee` (fees already charged) and `Storage Fees Already Paid` (`initialStorageFeePaid`). The paid fees go to `storageFeesPaid` and into `amountPaid`, never into the title work, and do NOT set `lastPaymentDate` (the date is unknown, so the recovery badge / 30-day lock are not triggered). Two history lines are written (INITIAL_DEPOSIT, allocation TITLE and STORAGE). Server rules: fees paid <= initial fee, whole shillings, initial payment <= total cost, and storage fees are refused when the title is already fully paid (no receivable). Anything that shows progress or CRITICAL must use TITLE money = `amountPaid - storageFeesPaid`.",
          "- **Storage fee rules (fix167):**"
      ]),
      "Guide: storage fees already paid")


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

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


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
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
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
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
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

if not changed:
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