# fix.py -- fix68: simple STORAGE FEES section, freeze button flow, totals, constructor injection
import re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)
res = []

fp = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
s = read(fp)

NEW_SECTION = '''<section className={styles.hwPanel} aria-label="Storage Fees" id="receivable-controls">
                    <DrawerHeader label="STORAGE FEES" isOpen={drawers.recv} onClick={() => toggleDrawer('recv')} icon={FiAlertOctagon} />
                    <div className={`${styles.panelBody} ${drawers.recv ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {!isReceivable ? (
                            <div className={styles.recvActionRow}>
                                {canEdit && <HardwareButton type="button" icon={FiAlertOctagon} loading={recvBusy} onClick={() => askReceivable('ENTER')}>+ RECEIVABLES</HardwareButton>}
                                <span className={styles.inputHint}>Storage fees apply only after a project is moved to receivables.</span>
                            </div>
                        ) : (<>
                            <div className={styles.moneyStatsRow}>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>STORAGE FEES</label><strong>UGX {fmt(storageFees)}</strong></div>
                                <div className={styles.statBox}><label>COMBINED TOTAL</label><strong>UGX {fmt(totalValue + storageFees)}</strong></div>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>TOTAL OWED</label><strong>UGX {fmt(receivableAmountOwed)}</strong></div>
                            </div>
                            {canMoney && (<div className={styles.storageBlock}>
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="MONTHLY STORAGE RATE" value={rateFee} onChange={v => setRateFee(v)} hint="Blank = default 50,000" />
                                    <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>&nbsp;</label></div>
                                        <HardwareButton type="button" icon={FiSave} loading={recvBusy} onClick={() => askReceivable('SETTINGS')}>SAVE RATE</HardwareButton></div>
                                </div>
                                <div className={styles.recvActionRow}>
                                    {project.negotiationDeadline ? (<>
                                        <span className={styles.frozenChip}>FROZEN UNTIL {String(project.negotiationDeadline).slice(0, 10)}</span>
                                        <button type="button" className={styles.ghostBtn} onClick={handleUnfreeze}><FiUnlock aria-hidden="true" /> UNFREEZE</button>
                                    </>) : freezeOpen ? (<>
                                        <input type="datetime-local" className={styles.dtInput} value={rateDeadline} onChange={e => setRateDeadline(e.target.value)} />
                                        <HardwareButton type="button" icon={FiCheckCircle} loading={recvBusy} onClick={() => askReceivable('SETTINGS')}>CONFIRM FREEZE</HardwareButton>
                                        <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(false)}><FiX aria-hidden="true" /> CANCEL</button>
                                    </>) : (
                                        <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(true)}><FiClock aria-hidden="true" /> FREEZE FEES</button>
                                    )}
                                </div>
                            </div>)}
                            <div className={styles.recvActionRow}>
                                {canMoney && (<>
                                    <HardwareButton type="button" icon={FiArchive} loading={recvBusy} onClick={() => askReceivable('SET_ASIDE')}>SET ASIDE</HardwareButton>
                                    <button type="button" className={styles.ghostBtn} onClick={() => askReceivable('CAPITALIZE')} disabled={recvBusy}><FiCreditCard aria-hidden="true" /> CAPITALIZE</button>
                                    <button type="button" className={styles.dangerBtn} onClick={() => askReceivable('WAIVE')} disabled={recvBusy}><FiTrash2 aria-hidden="true" /> WAIVE</button>
                                </>)}
                            </div>
                        </>)}
                    </div></div>
                </section>'''

# ---- replace the whole Receivables & Portfolio section via depth scan ----
marker = 'aria-label="Receivables and Portfolio"'
i = s.find(marker)
if i != -1:
    start = s.rfind("<section", 0, i)
    depth = 0; k = start; end = -1
    while k < len(s):
        no = s.find("<section", k); nc = s.find("</section>", k)
        if nc == -1: break
        if no != -1 and no < nc: depth += 1; k = no + 8
        else:
            depth -= 1; k = nc + 10
            if depth == 0: end = k; break
    if end != -1:
        s = s[:start] + NEW_SECTION + s[end:]
        res.append("OK storage-fees section replaced")
else:
    res.append("MISS section marker")

# ---- add freezeOpen state + handleUnfreeze ----
if "const [freezeOpen, setFreezeOpen]" not in s:
    s = s.replace("const [recvBusy, setRecvBusy] = useState(false);",
                  "const [recvBusy, setRecvBusy] = useState(false);\n    const [freezeOpen, setFreezeOpen] = useState(false);", 1)
    res.append("OK freezeOpen state")
if "const handleUnfreeze" not in s:
    s = s.replace("const handleRelease = async () => {",
                  "const handleUnfreeze = async () => { try { await folderPortalService.settings(id, { deadline: '' }); setRateDeadline(''); setFreezeOpen(false); await loadFolderData(); toast('Fees unfrozen.', 'info'); } catch { toast('UNFREEZE FAILED', 'error'); } };\n    const handleRelease = async () => {", 1)
    res.append("OK handleUnfreeze")
write(fp, s)

# ---- CSS frozenChip ----
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
c = read(cssp)
if ".frozenChip" not in c:
    c += "\n.frozenChip{display:inline-flex;align-items:center;gap:5px;background:rgba(6,182,212,0.12);border:1px solid rgba(6,182,212,0.4);color:#06b6d4;border-radius:999px;padding:4px 12px;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;}\n"
    write(cssp, c); res.append("OK frozenChip css")

# ---- RecoveryNoteController: @Autowired(required=false) -> final constructor injection ----
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
lines = read(rc).split("\n")
out = []; i = 0; changed = False
while i < len(lines):
    l = lines[i]
    if re.match(r'^\s*@org\.springframework\.beans\.factory\.annotation\.Autowired\(required = false\)\s*$', l):
        # skip annotation; make next field final
        if i + 1 < len(lines) and re.match(r'^\s*private\s+', lines[i+1]) and " final " not in lines[i+1]:
            lines[i+1] = lines[i+1].replace("private ", "private final ", 1)
            changed = True
        i += 1; continue
    out.append(l); i += 1
if changed:
    write(rc, "\n".join(out)); res.append("OK constructor injection")
else:
    res.append("skip injection (already final or pattern absent)")

for r in res: print(r)
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix68: STORAGE FEES section + freeze button flow + totals + constructor injection"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")