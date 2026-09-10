# fix.py -- fix121: inconsistency sweep (racing chips effect, restore confirm, icon/tone fixes, dead code)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
SVC = FE / "services" / "stageTemplateService.js"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)
def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1
def sub_in_line(lines, needle, old, new, label):
    i = find(lines, needle)
    if i < 0 or old not in lines[i]: print("SKIP", label); return lines
    lines[i] = lines[i].replace(old, new, 1); print("OK", label); return lines

L = read(JSX).split("\n")

# 1. delete the unfiltered recovery-chips effect (keep only the RECOVERY-filtered one)
if "source === 'RECOVERY'" in "\n".join(L):
    i = find(L, '.then(lists => setRecoveryChips(lists.flat().sort(')
    if i >= 0:
        a = i
        while a > 0 and 'useEffect(() => {' not in L[a]:
            a -= 1
        b = i
        while b < len(L) - 1 and L[b].strip() != '}, [binder]);':
            b += 1
        if 'useEffect(() => {' in L[a] and L[b].strip() == '}, [binder]);':
            del L[a:b + 1]
            print("OK removed unfiltered recovery chips effect")
        else:
            print("MISSING chips effect bounds")
    else:
        print("SKIP unfiltered chips effect already gone")
else:
    print("SKIP filtered chips effect not found, keeping both for safety")

# 2. dead BackToTopButton import (component replaced by scroll-top button in fix117)
hits = [n for n, ln in enumerate(L) if 'BackToTopButton' in ln]
if len(hits) == 1 and 'import BackToTopButton' in L[hits[0]]:
    del L[hits[0]]
    print("OK removed dead BackToTopButton import")
else:
    print("SKIP BackToTopButton import (still used or already gone)")

# 3. RESTORE DEFAULTS gets the standard confirm modal
L = sub_in_line(L, 'const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {',
    'toast }) => {', 'toast, confirm }) => {', "panel accepts confirm prop")
if 'Replace the current stage list' not in "\n".join(L):
    i = find(L, 'const handleRestoreDefaults = async () => {')
    if i >= 0:
        L.insert(i + 1, "if (confirm) { const ok = await confirm('RESTORE DEFAULTS', 'Replace the current stage list with the master checklist? Current ticks and custom stages will be lost.', 'warn'); if (!ok) return; }")
        print("OK restore defaults confirm guard")
    else:
        print("SKIP handleRestoreDefaults anchor")
else:
    print("SKIP restore confirm already present")
L = sub_in_line(L, '<StageChecklistPanel projectId={id}', 'toast={toast} />', 'toast={toast} confirm={confirm} />', "pass confirm into panel")
write(JSX, "\n".join(L))

# 4. Client Ledger: shield icon -> mail icon on the email row
C = read(CLP).split("\n")
C = sub_in_line(C, "from 'react-icons/fi';", 'FiShield', 'FiMail', "client ledger import FiMail")
C = sub_in_line(C, '{c.email', '<FiShield aria-hidden="true" />', '<FiMail aria-hidden="true" />', "client ledger email icon")

# 5. tone dot only for POSITIVE / NEGATIVE tags
C = sub_in_line(C, 'styles.toneDot', '{c.lastTag ?', "{(c.lastTone === 'POSITIVE' || c.lastTone === 'NEGATIVE') ?", "tone dot condition")
C = sub_in_line(C, 'styles.toneDot', "c.lastTone === 'POSITIVE' ? styles.tonePos : styles.toneNeg", "c.lastTone === 'NEGATIVE' ? styles.toneNeg : styles.tonePos", "tone dot colour logic")
write(CLP, "\n".join(C))

# 6. dead updateStageCost service function (no callers left since fix116)
if 'updateStageCost' not in read(JSX):
    S = read(SVC).split("\n")
    i = find(S, 'updateStageCost:')
    if i >= 0:
        b = i
        while b < len(S) - 1 and S[b].strip() != '},':
            b += 1
        del S[i:b + 1]
        write(SVC, "\n".join(S))
        print("OK removed dead updateStageCost service function")
    else:
        print("SKIP updateStageCost already gone")
else:
    print("SKIP updateStageCost still referenced somewhere")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix121: inconsistency sweep - single recovery chips effect, restore-defaults confirm, mail icon + tone dot fixes, dead code removal"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")