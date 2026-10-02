#!/usr/bin/env python3
# PATH: fix172.py
# GOLDEN SEED -- fix172: three intake gaps for projects that already existed before they were keyed in.
#
# THE PROBLEMS:
#   1. The title payment typed at intake always stamped TODAY as the last-payment date. A legacy project paid years ago
#      turned green and locked recovery calls for 30 days.
#   2. Fee counting started on the entry date. Months before that only existed if someone typed them into Initial Storage Fee.
#   3. The intake deposit lines did not say which owner paid, so per-owner tracking on joint projects missed that money.
#
# WHAT CHANGES:
#   1. INTAKE: new optional "Date Last Paid" (shows once a payment amount is entered). It becomes the last-payment date and the
#      date on the intake deposit lines in Payment History. Left empty = exactly as before. Refused if in the future or if no
#      payment was entered.
#   2. INTAKE (Legacy Title): new optional "In Receivables Since". The billing clock starts on that date, the whole 30-day months
#      already gone are billed at intake (months x monthly fee) and counted as billed, so the nightly job never bills them
#      twice. The page shows the backlog fees in the summary, and "Storage Fees Already Paid" may now go up to initial fee +
#      backlog fees.
#   3. INTAKE: new "Paid By" owner pick for the initial payment and for the storage fees already paid (required when the
#      project has more than one owner, automatic when it has one). It is written on the deposit lines, so the folder shows
#      "paid by <owner>" for them like for every later payment.
#   4. Receivable Breakdown CSV: MONTHS_IN_RECEIVABLE is counted in the same 30-day periods the fees are billed in.
#
# NOT in this fix: any change to how fees accrue, a way to change these dates after the project is saved, splitting one
# deposit between two owners, any database change (all columns already exist).
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
FIX_NO = "fix172"
COMMIT_MSG = "fix172: intake Date Last Paid, In Receivables Since (backlog fees), and which owner paid the intake money"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_INTAKE_CSS = os.path.join(SRC, "pages", "Intake", "IntakePage.module.css")
F_ENTRY_DTO = os.path.join(JAVA, "modules", "land", "dto", "LandEntryRequest.java")
F_LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
F_REPORT_SERVICE = os.path.join(JAVA, "modules", "land", "service", "ReportService.java")
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
LOAD_FILES = (F_ENTRY_DTO, F_LAND_SERVICE, F_REPORT_SERVICE, F_INTAKE_JSX, F_INTAKE_CSS, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_ENTRY_DTO,
      "\n".join([
          "    // fix171: how much of the initial storage fee the client has ALREADY paid (counts toward the fees, not the title work)",
          "    private java.math.BigDecimal initialStorageFeePaid;"
      ]),
      "\n".join([
          "    // fix171: how much of the initial storage fee the client has ALREADY paid (counts toward the fees, not the title work)",
          "    private java.math.BigDecimal initialStorageFeePaid;",
          "    // fix172: optional date the client last paid (for the money entered as already paid at intake). Empty = today.",
          "    private LocalDate lastPaidDate;",
          "    // fix172: Legacy Title only. The date the project went into receivables; the months since then are billed at intake.",
          "    private LocalDate receivablesSince;",
          "    // fix172: WHICH owner paid the intake money (the NIN typed in the Owners section). Needed when there is more than one owner.",
          "    private String initialPaymentPayerNin;",
          "    private String initialStorageFeePaidPayerNin;"
      ]),
      "DTO: lastPaidDate, receivablesSince, payer of the intake money")

patch(F_LAND_SERVICE,
      "\n".join([
          "        if (initialFeesPaid.compareTo(initialFees) > 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"STORAGE_PAID_TOO_HIGH: Storage fees already paid (UGX \" + initialFeesPaid.toPlainString()",
          "                    + \") cannot be more than the initial storage fee (UGX \" + initialFees.toPlainString() + \").\");",
          "        }"
      ]),
      "\n".join([
          "        // fix172: \"in receivables since\". The months that went by before today are billed NOW (counted the same way the nightly",
          "        // fee job counts them: whole 30-day periods) and the billing clock starts at that date, so nothing is billed twice.",
          "        LocalDate receivablesSince = request.getReceivablesSince();",
          "        BigDecimal feeRate = (request.getMonthlyStorageFee() != null && request.getMonthlyStorageFee().signum() > 0)",
          "                ? request.getMonthlyStorageFee() : new BigDecimal(\"50000\");",
          "        int backlogMonths = 0;",
          "        LocalDateTime receivableClock = LocalDateTime.now();",
          "        if (receivablesSince != null) {",
          "            if (!(startAsReceivable && outstanding.signum() > 0)) {",
          "                throw new com.gesolutions.erp.common.exception.BusinessException(\"SINCE_NOT_APPLICABLE: An In Receivables Since date only applies to a project that goes into receivables. \"",
          "                        + \"This title work is already fully paid, so clear the date.\");",
          "            }",
          "            if (receivablesSince.isAfter(LocalDate.now().plusDays(1))) {",
          "                throw new com.gesolutions.erp.common.exception.BusinessException(\"SINCE_IN_FUTURE: The In Receivables Since date cannot be in the future.\");",
          "            }",
          "            long daysGone = Math.max(0L, java.time.temporal.ChronoUnit.DAYS.between(receivablesSince, LocalDate.now()));",
          "            if (daysGone > 10950L) {",
          "                throw new com.gesolutions.erp.common.exception.BusinessException(\"SINCE_TOO_OLD: The In Receivables Since date is more than 30 years ago. Check the year.\");",
          "            }",
          "            backlogMonths = (int) (daysGone / 30L);",
          "            receivableClock = receivablesSince.atStartOfDay();",
          "        }",
          "        BigDecimal backlogFees = feeRate.multiply(BigDecimal.valueOf(backlogMonths));",
          "        if (initialFeesPaid.compareTo(initialFees.add(backlogFees)) > 0) {",
          "            throw new com.gesolutions.erp.common.exception.BusinessException(\"STORAGE_PAID_TOO_HIGH: Storage fees already paid (UGX \" + initialFeesPaid.toPlainString()",
          "                    + \") cannot be more than the fees charged (UGX \" + initialFees.add(backlogFees).toPlainString() + \": initial storage fee UGX \"",
          "                    + initialFees.toPlainString() + \" plus UGX \" + backlogFees.toPlainString() + \" backlog).\");",
          "        }",
          "",
          "        // fix172: optional \"date last paid\" for the money entered as already paid. Empty keeps the old behaviour (paid today).",
          "        LocalDate lastPaidDate = request.getLastPaidDate();",
          "        LocalDateTime paidAt = null;",
          "        if (lastPaidDate != null) {",
          "            if (lastPaidDate.isAfter(LocalDate.now().plusDays(1))) {",
          "                throw new com.gesolutions.erp.common.exception.BusinessException(\"DATE_PAID_IN_FUTURE: The date last paid cannot be in the future.\");",
          "            }",
          "            if (initialPayment.signum() == 0 && initialFeesPaid.signum() == 0) {",
          "                throw new com.gesolutions.erp.common.exception.BusinessException(\"DATE_PAID_NO_PAYMENT: A date last paid needs a payment amount. Enter the payment, or clear the date.\");",
          "            }",
          "            paidAt = lastPaidDate.isBefore(LocalDate.now()) ? lastPaidDate.atTime(12, 0) : LocalDateTime.now();",
          "        }"
      ]),
      "Intake: In Receivables Since (backlog months billed) and Date Last Paid checks")

patch(F_LAND_SERVICE,
      "\n".join([
          "            builder.isReceivable(true)",
          "                   .receivableStartDate(LocalDateTime.now())",
          "                   .originalDebt(outstanding)",
          "                   .storageFeesAccumulated(initialFees)",
          "                   .storageFeesPaid(initialFeesPaid);   // fix171"
      ]),
      "\n".join([
          "            builder.isReceivable(true)",
          "                   .receivableStartDate(receivableClock)   // fix172: the In Receivables Since date, or now",
          "                   .receivableMonthsBilled(backlogMonths)   // fix172: those months are billed below, so the nightly job must not bill them again",
          "                   .originalDebt(outstanding)",
          "                   .storageFeesAccumulated(initialFees.add(backlogFees))   // fix172: typed fee + the backlog months",
          "                   .storageFeesPaid(initialFeesPaid);   // fix171"
      ]),
      "Intake: billing clock starts at the In Receivables Since date, backlog fees added")

patch(F_LAND_SERVICE,
      "\n".join([
          "        if (request.getOwners() != null) {",
          "            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {"
      ]),
      "\n".join([
          "        // fix172: the owners by NIN, so the owner who paid the intake money can be named",
          "        java.util.Map<String, Client> ownersByNin = new java.util.LinkedHashMap<>();",
          "        if (request.getOwners() != null) {",
          "            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {"
      ]),
      "Intake: remember each owner by NIN")

patch(F_LAND_SERVICE,
      "\n".join([
          "                c.setHomeAddress(o.getAddress());",
          "                project.addProprietor(c);"
      ]),
      "\n".join([
          "                c.setHomeAddress(o.getAddress());",
          "                project.addProprietor(c);",
          "                ownersByNin.put(o.getNationalId().trim().toUpperCase(), c);   // fix172"
      ]),
      "Intake: fill the owner-by-NIN list")

patch(F_LAND_SERVICE,
      "\n".join([
          "        LandProject saved = projectRepository.save(project);",
          "",
          "        // Record initial payment if any",
          ""
      ]),
      "\n".join([
          "        // fix172: WHO paid the money entered at intake. Same rule as a normal payment: a single owner is the payer,",
          "        // joint owners must say which one paid. Checked before anything is saved.",
          "        Client titlePayer = fix172ResolvePayer(ownersByNin, request.getInitialPaymentPayerNin(), initialPayment, \"initial payment\");",
          "        Client feesPayer = fix172ResolvePayer(ownersByNin, request.getInitialStorageFeePaidPayerNin(), initialFeesPaid, \"storage fees already paid\");",
          "        StringBuilder fix172Note = new StringBuilder();",
          "        if (titlePayer != null) fix172Note.append(\" | Initial payment paid by \").append(titlePayer.getFullName());",
          "        if (feesPayer != null) fix172Note.append(\" | Storage fees paid by \").append(feesPayer.getFullName());",
          "        if (lastPaidDate != null) fix172Note.append(\" | Date last paid \").append(lastPaidDate);",
          "        if (receivablesSince != null) fix172Note.append(\" | In receivables since \").append(receivablesSince)",
          "                .append(\" (\").append(backlogMonths).append(\" month(s) of fees billed at intake)\");",
          "",
          "        LandProject saved = projectRepository.save(project);",
          "",
          "        // Record initial payment if any",
          ""
      ]),
      "Intake: find who paid the title money and the fees money")

patch(F_LAND_SERVICE,
      "\n".join([
          "                    .notes(\"Initial deposit at intake\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"TITLE\")",
          "                    .build();",
          "            paymentRecordRepository.save(initialRecord);",
          "            saved.setLastPaymentDate(LocalDateTime.now());",
          "            projectRepository.save(saved);"
      ]),
      "\n".join([
          "                    .notes(paidAt != null ? \"Initial deposit at intake (paid on \" + lastPaidDate + \")\" : \"Initial deposit at intake\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"TITLE\")",
          "                    .payerClientId(titlePayer != null ? titlePayer.getId() : null)   // fix172: which owner paid",
          "                    .payerName(titlePayer != null ? titlePayer.getFullName() : null)",
          "                    .timestamp(paidAt != null ? paidAt : LocalDateTime.now())   // fix172: the date it was really paid",
          "                    .build();",
          "            paymentRecordRepository.save(initialRecord);",
          "            saved.setLastPaymentDate(paidAt != null ? paidAt : LocalDateTime.now());   // fix172: not always today any more",
          "            projectRepository.save(saved);"
      ]),
      "Intake: title deposit line carries the payer and the real payment date")

patch(F_LAND_SERVICE,
      "\n".join([
          "                    .notes(\"Storage fees already paid before entry (recorded at intake)\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"STORAGE\")",
          "                    .build();",
          "            paymentRecordRepository.save(feesRecord);"
      ]),
      "\n".join([
          "                    .notes(paidAt != null ? \"Storage fees already paid before entry (paid on \" + lastPaidDate + \")\" : \"Storage fees already paid before entry (recorded at intake)\")",
          "                    .balanceAfter(balanceAtIntake)",
          "                    .allocation(\"STORAGE\")",
          "                    .payerClientId(feesPayer != null ? feesPayer.getId() : null)   // fix172: which owner paid",
          "                    .payerName(feesPayer != null ? feesPayer.getFullName() : null)",
          "                    .timestamp(paidAt != null ? paidAt : LocalDateTime.now())",
          "                    .build();",
          "            paymentRecordRepository.save(feesRecord);",
          "            if (paidAt != null) {",
          "                // fix172: only when the operator gave a date. No date = still unknown = the recovery badge stays untouched.",
          "                saved.setLastPaymentDate(paidAt);",
          "                projectRepository.save(saved);",
          "            }"
      ]),
      "Intake: storage-fees line carries the payer and the real payment date")

patch(F_LAND_SERVICE,
      "\n".join([
          "            + plotOrIndex + receivableNote);"
      ]),
      "\n".join([
          "            + plotOrIndex + receivableNote + fix172Note);"
      ]),
      "Intake: audit line names the payers and the dates")

patch(F_LAND_SERVICE,
      "\n".join([
          "                + \". Storage fees: UGX \" + initialFees + \" (UGX \" + initialFeesPaid + \" already paid).\");"
      ]),
      "\n".join([
          "                + \". Storage fees: UGX \" + initialFees.add(backlogFees)",
          "                + (backlogMonths > 0 ? \" (incl. UGX \" + backlogFees + \" backlog for \" + backlogMonths + \" month(s) since \" + receivablesSince + \")\" : \"\")",
          "                + \" (UGX \" + initialFeesPaid + \" already paid).\");"
      ]),
      "Intake: receivable audit line shows the backlog fees")

patch(F_LAND_SERVICE,
      "\n".join([
          "    // fix166: one-line descriptions of the title and the owners, used to write OLD -> NEW into the audit log."
      ]),
      "\n".join([
          "    // fix172: finds the owner who paid money entered at intake. One owner = that owner. Joint owners = the payer must be",
          "    // named, and must be one of the owners typed on the form. No money entered = no payer needed.",
          "    private Client fix172ResolvePayer(java.util.Map<String, Client> ownersByNin, String payerNin, BigDecimal amount, String what) {",
          "        if (amount == null || amount.signum() <= 0) return null;",
          "        String key = payerNin == null ? \"\" : payerNin.trim().toUpperCase();",
          "        if (!key.isEmpty()) {",
          "            Client hit = ownersByNin.get(key);",
          "            if (hit == null) {",
          "                throw new BusinessException(\"PAYER_INVALID: The owner who paid the \" + what + \" must be one of the owners on this form.\");",
          "            }",
          "            return hit;",
          "        }",
          "        if (ownersByNin.size() == 1) return ownersByNin.values().iterator().next();",
          "        if (ownersByNin.size() > 1) {",
          "            throw new BusinessException(\"PAYER_REQUIRED: This project has \" + ownersByNin.size() + \" owners. Pick which owner paid the \" + what + \".\");",
          "        }",
          "        return null;",
          "    }",
          "",
          "    // fix166: one-line descriptions of the title and the owners, used to write OLD -> NEW into the audit log."
      ]),
      "Intake: helper that finds the paying owner")

patch(F_REPORT_SERVICE,
      "\n".join([
          "            long months = p.getReceivableStartDate() != null",
          "                ? java.time.temporal.ChronoUnit.MONTHS.between(p.getReceivableStartDate(), java.time.LocalDateTime.now())",
          "                : 0;"
      ]),
      "\n".join([
          "            // fix172: counted in the same whole 30-day periods the nightly fee job bills (calendar months drifted from it)",
          "            long months = p.getReceivableStartDate() != null",
          "                ? java.time.temporal.ChronoUnit.DAYS.between(p.getReceivableStartDate(), java.time.LocalDateTime.now()) / 30L",
          "                : 0;"
      ]),
      "Receivable CSV: months in receivables counted in 30-day periods like the billing")

patch(F_INTAKE_JSX,
      "\n".join([
          "const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';"
      ]),
      "\n".join([
          "// fix172: today as yyyy-mm-dd in the user's own time zone (todayISO above is UTC and can be yesterday early in the morning)",
          "const localISO = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };",
          "// fix172: whole 30-day months between an \"in receivables since\" date (yyyy-mm-dd) and today, the same count the nightly fee job uses",
          "const monthsSince = (iso) => {",
          "    const m = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(iso || '');",
          "    if (!m) return 0;",
          "    const start = new Date(+m[1], +m[2] - 1, +m[3]);",
          "    const t = new Date();",
          "    const today = new Date(t.getFullYear(), t.getMonth(), t.getDate());",
          "    return Math.max(0, Math.floor(Math.round((today - start) / 86400000) / 30));",
          "};",
          "const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';"
      ]),
      "Intake page: date helpers")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const [initialStorageFeePaid, setInitialStorageFeePaid] = useState(0);   // fix171"
      ]),
      "\n".join([
          "    const [initialStorageFeePaid, setInitialStorageFeePaid] = useState(0);   // fix171",
          "    const [lastPaidDate, setLastPaidDate] = useState('');           // fix172: optional, empty = paid today",
          "    const [receivablesSince, setReceivablesSince] = useState('');   // fix172: optional, Legacy Title only",
          "    const [titlePayerIdx, setTitlePayerIdx] = useState('');         // fix172: which owner (row number) paid the initial payment",
          "    const [feesPayerIdx, setFeesPayerIdx] = useState('');           // fix172: which owner paid the storage fees"
      ]),
      "Intake page: new fields")

patch(F_INTAKE_JSX,
      "\n".join([
          "        if (Number(initialPayment) > Number(totalCost)) { toast('Initial Payment cannot be more than the Total Cost.', 'error'); return false; }"
      ]),
      "\n".join([
          "        if (Number(initialPayment) > Number(totalCost)) { toast('Initial Payment cannot be more than the Total Cost.', 'error'); return false; }",
          "        // fix172: the optional dates, and which owner paid the intake money",
          "        const paidAny = (Number(initialPayment) || 0) > 0 || (isLegacy && (Number(initialStorageFeePaid) || 0) > 0);",
          "        if (lastPaidDate && lastPaidDate > localISO()) { toast('Date Last Paid cannot be in the future.', 'error'); return false; }",
          "        if (lastPaidDate && !paidAny) { toast('Date Last Paid needs a payment amount. Enter the payment, or clear the date.', 'error'); return false; }",
          "        if (isLegacy && receivablesSince && receivablesSince > localISO()) { toast('In Receivables Since cannot be in the future.', 'error'); return false; }",
          "        if (owners.length > 1) {",
          "            if ((Number(initialPayment) || 0) > 0 && titlePayerIdx === '') { toast('Pick which owner paid the Initial Payment.', 'error'); return false; }",
          "            if (isLegacy && (Number(initialStorageFeePaid) || 0) > 0 && feesPayerIdx === '') { toast('Pick which owner paid the Storage Fees Already Paid.', 'error'); return false; }",
          "        }"
      ]),
      "Intake page: checks for the dates and the payer")

patch(F_INTAKE_JSX,
      "\n".join([
          "            if (feePaid > feeCharged) { toast('Storage Fees Already Paid cannot be more than the Initial Storage Fee.', 'error'); return false; }",
          "            if (Number(initialPayment) >= Number(totalCost) && (feeCharged > 0 || feePaid > 0)) {",
          "                toast('The title work is already fully paid, so this project will not be in receivables and cannot carry storage fees. Clear the storage fee boxes.', 'error'); return false;",
          "            }"
      ]),
      "\n".join([
          "            const backlogNow = receivablesSince ? monthsSince(receivablesSince) * (Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE) : 0;",
          "            if (feePaid > feeCharged + backlogNow) { toast('Storage Fees Already Paid cannot be more than the fees charged (Initial Storage Fee plus the backlog fees).', 'error'); return false; }",
          "            if (Number(initialPayment) >= Number(totalCost) && (feeCharged > 0 || feePaid > 0 || receivablesSince)) {",
          "                toast('The title work is already fully paid, so this project will not be in receivables and cannot carry storage fees. Clear the storage fee boxes and the In Receivables Since date.', 'error'); return false;",
          "            }"
      ]),
      "Intake page: fees paid may include the backlog fees; fully paid title refuses the since date")

patch(F_INTAKE_JSX,
      "\n".join([
          "            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));"
      ]),
      "\n".join([
          "            // fix172: the optional dates, and which owner paid the intake money (sent as that owner's NIN)",
          "            if (lastPaidDate) payload.lastPaidDate = lastPaidDate;",
          "            if (isLegacy && receivablesSince) payload.receivablesSince = receivablesSince;",
          "            const ninOf = (idx) => (idx !== '' && owners[idx]) ? owners[idx].nationalId.trim().toUpperCase() : '';",
          "            if ((Number(initialPayment) || 0) > 0 && ninOf(titlePayerIdx)) payload.initialPaymentPayerNin = ninOf(titlePayerIdx);",
          "            if (isLegacy && (Number(initialStorageFeePaid) || 0) > 0 && ninOf(feesPayerIdx)) payload.initialStorageFeePaidPayerNin = ninOf(feesPayerIdx);",
          "            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));"
      ]),
      "Intake page: send the dates and the payer")

patch(F_INTAKE_JSX,
      "\n".join([
          "setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setInitialStorageFeePaid(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);"
      ]),
      "\n".join([
          "setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setInitialStorageFeePaid(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);",
          "        setLastPaidDate(''); setReceivablesSince(''); setTitlePayerIdx(''); setFeesPayerIdx('');   // fix172"
      ]),
      "Intake page: Save + duplicate clears the new fields")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const feesCharged = isLegacy ? Math.max(0, Number(initialStorageFee) || 0) : 0;"
      ]),
      "\n".join([
          "    // fix172: backlog fees = whole 30-day months since the In Receivables Since date x the monthly fee (only while the title work is not fully paid)",
          "    const backlogMonths = isLegacy && titleLeft > 0 && receivablesSince ? monthsSince(receivablesSince) : 0;",
          "    const backlogRate = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;",
          "    const backlogFees = backlogMonths * backlogRate;",
          "    const feesCharged = isLegacy ? Math.max(0, Number(initialStorageFee) || 0) + backlogFees : 0;"
      ]),
      "Intake page: backlog fees in the summary maths")

patch(F_INTAKE_JSX,
      "\n".join([
          "    let n = 0;",
          "    const nIndex = ++n, nOwners = ++n;"
      ]),
      "\n".join([
          "    // fix172: removing an owner must not leave a payer pointing at the wrong person",
          "    const removeOwner = (idx) => {",
          "        setOwners(p => p.filter((_, i) => i !== idx));",
          "        const shift = (cur) => (cur === '' || cur === idx ? '' : cur > idx ? cur - 1 : cur);",
          "        setTitlePayerIdx(shift); setFeesPayerIdx(shift);",
          "        markDirty();",
          "    };",
          "    const ownerLabels = owners.map((o, i) => (i + 1) + '. ' + (o.fullName.trim() ? o.fullName.trim().toUpperCase() : 'OWNER ' + (i + 1)));",
          "    const pickOwner = (setter) => (label) => { setter(ownerLabels.indexOf(label)); markDirty(); };",
          "    const titlePaidNow = (Number(initialPayment) || 0) > 0;",
          "    const feesPaidEntered = isLegacy && (Number(initialStorageFeePaid) || 0) > 0;",
          "    let n = 0;",
          "    const nIndex = ++n, nOwners = ++n;"
      ]),
      "Intake page: owner list helpers for the payer pick")

patch(F_INTAKE_JSX,
      "\n".join([
          "                                onClick={() => setOwners(p => p.filter((_, i) => i !== idx))}"
      ]),
      "\n".join([
          "                                onClick={() => removeOwner(idx)}"
      ]),
      "Intake page: removing an owner keeps the payer pick right")

patch(F_INTAKE_JSX,
      "\n".join([
          "                            {isLegacy && <p className={styles.hint}>Money paid toward the title work only. Storage fees already paid go in the Storage Fees box below.</p>}",
          "                        </div>",
          "                    </div>",
          "                    {isLegacy && ("
      ]),
      "\n".join([
          "                            {isLegacy && <p className={styles.hint}>Money paid toward the title work only. Storage fees already paid go in the Storage Fees box below.</p>}",
          "                        </div>",
          "                    </div>",
          "                    {(titlePaidNow || feesPaidEntered) && (",
          "                        <div className={styles.grid2}>",
          "                            {owners.length > 1 && titlePaidNow && (",
          "                                <div className={styles.field}>",
          "                                    <HardwareSelect label=\"Initial Payment Paid By\" required placeholder=\"Choose the owner\" options={ownerLabels} value={ownerLabels[titlePayerIdx] || ''} onChange={pickOwner(setTitlePayerIdx)} />",
          "                                    <p className={styles.hint}>The owner who paid the title work money. Each owner's payments are tracked on a joint project.</p>",
          "                                </div>",
          "                            )}",
          "                            <div className={styles.field}>",
          "                                <label className={styles.label}>Date Last Paid</label>",
          "                                <HardwareDatePicker block className={styles.input} value={lastPaidDate} ariaLabel=\"Date last paid\" onChange={v => { setLastPaidDate(v); markDirty(); }} />",
          "                                {lastPaidDate && <button type=\"button\" className={styles.clearLink} onClick={() => { setLastPaidDate(''); markDirty(); }}>Clear date</button>}",
          "                                <p className={styles.hint}>Optional. The day the client last paid. Left empty it counts as paid today, which locks recovery calls for 30 days.</p>",
          "                            </div>",
          "                        </div>",
          "                    )}",
          "                    {isLegacy && ("
      ]),
      "Intake page: Date Last Paid and Paid By (initial payment)")

patch(F_INTAKE_JSX,
      "\n".join([
          "                                    <p className={styles.hint}>Part of the Initial Storage Fee the client has already paid. Counted toward the fees, not the title work, and it does not count as a recent payment.</p>",
          "                                </div>",
          "                            </div>",
          "                        </>",
          "                    )}"
      ]),
      "\n".join([
          "                                    <p className={styles.hint}>Part of the fees charged (Initial Storage Fee plus backlog fees) that the client has already paid. Counted toward the fees, not the title work. It only counts as a recent payment if you set a Date Last Paid.</p>",
          "                                </div>",
          "                                {owners.length > 1 && feesPaidEntered && (",
          "                                    <div className={styles.field}>",
          "                                        <HardwareSelect label=\"Storage Fees Paid By\" required placeholder=\"Choose the owner\" options={ownerLabels} value={ownerLabels[feesPayerIdx] || ''} onChange={pickOwner(setFeesPayerIdx)} />",
          "                                        <p className={styles.hint}>The owner who paid these storage fees.</p>",
          "                                    </div>",
          "                                )}",
          "                                <div className={styles.field}>",
          "                                    <label className={styles.label}>In Receivables Since</label>",
          "                                    <HardwareDatePicker block className={styles.input} value={receivablesSince} ariaLabel=\"In receivables since\" onChange={v => { setReceivablesSince(v); markDirty(); }} />",
          "                                    {receivablesSince && <button type=\"button\" className={styles.clearLink} onClick={() => { setReceivablesSince(''); markDirty(); }}>Clear date</button>}",
          "                                    <p className={styles.hint}>",
          "                                        Optional. If this project was already unpaid before today, pick the day it went into receivables.{' '}",
          "                                        {backlogMonths > 0",
          "                                            ? `${backlogMonths} month(s) x UGX ${backlogRate.toLocaleString()} = UGX ${backlogFees.toLocaleString()} backlog fees are added now. If you already typed those months into Initial Storage Fee, lower it so they are not counted twice.`",
          "                                            : 'Fees are counted from that date. Empty = counted from today.'}",
          "                                    </p>",
          "                                </div>",
          "                            </div>",
          "                        </>",
          "                    )}"
      ]),
      "Intake page: In Receivables Since and Paid By (storage fees)")

patch(F_INTAKE_JSX,
      "\n".join([
          "                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}"
      ]),
      "\n".join([
          "                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}",
          "                        {isLegacy && backlogMonths > 0 && <div className={styles.finRow}><span>Backlog Storage Fees ({backlogMonths} mo)</span><span>{backlogFees}</span></div>}"
      ]),
      "Intake page: backlog fees row in the summary")

patch(F_INTAKE_CSS,
      "\n".join([
          ".finRow.total { color: var(--orange); font-size: clamp(13px,1.4vw,17px); border-top: 1px solid rgba(238,140,58,0.25); padding-top: var(--gap-md); }"
      ]),
      "\n".join([
          ".finRow.total { color: var(--orange); font-size: clamp(13px,1.4vw,17px); border-top: 1px solid rgba(238,140,58,0.25); padding-top: var(--gap-md); }",
          "/* fix172: small \"clear\" link under an optional date */",
          ".clearLink { background: none; border: none; padding: 2px 0; margin-top: 2px; color: var(--orange); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; text-align: left; cursor: pointer; }",
          ".clearLink:hover { text-decoration: underline; }"
      ]),
      "Intake CSS: clear-date link")

patch(F_GUIDE,
      "\n".join([
          "- **Storage fees already paid at intake (fix171):**"
      ]),
      "\n".join([
          "- **Intake dates and payer (fix172):** (1) `lastPaidDate` (optional): the day the client last paid. It sets `lastPaymentDate` and the timestamp of the intake deposit lines; empty keeps the old rule (title deposit = today, fees-only = no date). Refused when in the future or when no payment amount was entered. (2) `receivablesSince` (Legacy Title only, optional): `receivableStartDate` becomes that date, the whole 30-day months since then are billed at intake (months x monthly fee, added to `storageFeesAccumulated`) and `receivableMonthsBilled` is set to that count so the nightly job does not bill them again. `Storage Fees Already Paid` may now be up to initial fee + backlog fees. If staff already typed those months into Initial Storage Fee they must lower it (the page says so). (3) `initialPaymentPayerNin` / `initialStorageFeePaidPayerNin`: which owner (by NIN) paid the intake money; written to `payerClientId` / `payerName` on the deposit lines. One owner = automatic, joint owners = required (`PAYER_REQUIRED`). One payer per line; a deposit split between owners is not supported at intake. The server allows a date one day ahead of its own clock (server time zone vs Kampala). The Receivable Breakdown CSV now counts MONTHS_IN_RECEIVABLE in 30-day periods like the billing.",
          "- **Storage fees already paid at intake (fix171):**"
      ]),
      "Guide: intake dates and payer")


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