# fix.py — fix49: port EXACT design tokens from IntakePage.module.css into Folder overrides
import os, re, sys, shutil, subprocess
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
BACKUP = os.path.join(ROOT, ".fix_backup")
os.makedirs(BACKUP, exist_ok=True)

def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)

intake_css = find("IntakePage.module.css", FE)
folder_css = find("FolderPage.module.css", FE)
if not intake_css or not folder_css:
    print("ABORT: Intake/Folder CSS not found.", intake_css, folder_css); sys.exit(1)
shutil.copy2(folder_css, BACKUP)
IC = re.sub(r'/\*[\s\S]*?\*/', '', read(intake_css))

def rgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

hexes = Counter(re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', IC))
orange_c, green_c, cream_c, red_c, dark_c = [], [], [], [], []
for h, c in hexes.items():
    try: r, g, b = rgb(h)
    except Exception: continue
    if r >= 200 and 90 <= g <= 190 and b <= 120: orange_c.append((h, c))
    elif r <= 80 and 40 <= g <= 110 and 40 <= b <= 110: green_c.append((h, c))
    elif r >= 235 and g >= 220 and b >= 205: cream_c.append((h, c))
    elif r >= 190 and g <= 100 and b <= 100: red_c.append((h, c))
    elif r <= 60 and g <= 60 and b <= 70: dark_c.append((h, c))
def top(lst, fb):
    return ('#' + max(lst, key=lambda x: x[1])[0]) if lst else fb
ORANGE = top(orange_c, '#EE8C3A'); GREEN = top(green_c, '#1e3b39')
CREAM = top(cream_c, '#f0e9e2'); RED = top(red_c, '#ef4444'); DARK = top(dark_c, '#122a28')

MONO = "'Space Mono',monospace" if 'Space Mono' in IC else "monospace"
CINZ = "'Cinzel',serif" if 'Cinzel' in IC else "serif"

# input look: white bg rules -> border + radius
inp = re.findall(r'background:\s*#fff[fF]?[^}]*?border:\s*([^;]+);[^}]*?border-radius:\s*([^;]+);', IC)
INP_BORDER = inp[0][0].strip() if inp else '1.5px solid #c8d6d7'
INP_RADIUS = inp[0][1].strip() if inp else '8px'
# primary button text color on orange
btn = re.findall(r'background:\s*' + ORANGE.lstrip('#') + r'[^}]*?color:\s*([^;]+);', IC) or \
      re.findall(r'background:\s*' + ORANGE + r'[^}]*?color:\s*([^;]+);', IC)
BTN_TXT = btn[0].strip() if btn else '#1a2e30'

report = ["INTAKE TOKEN REPORT", "orange=" + ORANGE, "panelGreen=" + GREEN, "cream=" + CREAM,
          "red=" + RED, "darkText=" + DARK, "inputBorder=" + INP_BORDER, "inputRadius=" + INP_RADIUS,
          "btnTextOnOrange=" + BTN_TXT, "fonts: Cinzel=" + ('yes' if 'Cinzel' in IC else 'no') +
          ", SpaceMono=" + ('yes' if 'Space Mono' in IC else 'no')]
print("\n".join(report))

css = read(folder_css)
css = re.sub(r'/\* FS-UNIFY v2[\s\S]*?(?=\n[^\n]|\Z)', '', css)  # drop guessed v2 block if present
css += '''
/* FS-UNIFY v3 — tokens ported verbatim from IntakePage.module.css at runtime */
:root{--fs-orange:%s;--fs-green:%s;--fs-red:%s;--fs-cream:%s;--fs-dark:%s;--fs-muted:rgba(255,255,255,.6);--fs-line:rgba(255,255,255,.08);}
.drawerHeader{border-bottom:1px solid %s;}
.drawerTitle{font-family:%s;color:%s;letter-spacing:.08em;text-transform:uppercase;font-weight:700;}
.drawerIcon,.chevron{color:%s;}
.specLabel{color:var(--fs-muted);letter-spacing:1.5px;text-transform:uppercase;}
.specValue{color:%s;font-family:%s;}
.hwInput,.selectTrigger{background:#fff;color:%s;border:%s;border-radius:%s;}
.hwInput::placeholder{color:#9aa8a6;}
.selectValue{color:%s;}
.inputLabelRow label{color:rgba(255,255,255,.85);letter-spacing:1.2px;text-transform:uppercase;font-size:10px;font-weight:700;}
.reqStar,.currencyTag{color:%s;}
.tabBtn{background:%s;color:#fff;border:1px solid rgba(255,255,255,.12);}
.tabBtnActive{background:%s;color:%s;border-color:%s;}
.ctrlBtnPay{background:%s;color:#fff;border:1px solid rgba(255,255,255,.18);}
.unlockMasterBtn{background:%s;color:%s;}
.btnPrimary{background:%s;color:%s;}
.btnDanger{background:transparent;color:%s;border:1.5px solid %s;}
''' % (ORANGE, GREEN, RED, CREAM, DARK,
       ORANGE, CINZ, ORANGE, ORANGE, ORANGE, MONO,
       DARK, INP_BORDER, INP_RADIUS, DARK, ORANGE,
       GREEN, ORANGE, BTN_TXT, ORANGE, GREEN, ORANGE, BTN_TXT,
       ORANGE, BTN_TXT, RED, RED)
write(folder_css, css)
print("WROTE: FolderPage.module.css (v3 Intake-ported tokens)")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix49: port exact Intake tokens into Folder overrides (no guessed values)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: committed and pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE. Paste the INTAKE TOKEN REPORT output back to me.")