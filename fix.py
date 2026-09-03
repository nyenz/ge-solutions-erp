# fix.py — fix51: EXACT Intake port onto Folder page (CSS-only, values verbatim)
import os, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
css_path = None
for r, d, fs in os.walk(FE):
    if "FolderPage.module.css" in fs: css_path = os.path.join(r, "FolderPage.module.css"); break
if not css_path:
    print("ABORT: FolderPage.module.css not found."); sys.exit(1)
shutil.copy2(css_path, os.path.join(ROOT, ".fix_backup", "FolderPage.module.css.bak"))

css = open(css_path, "r", encoding="utf-8").read()
if "FS-UNIFY v4" in css:
    print("NOTE: v4 already present."); sys.exit(0)

css += '''
/* FS-UNIFY v4 — EXACT Intake port (values verbatim from IntakePage.module.css) */
.container{
  --orange:#EE8C3A; --orange-dim:rgba(238,140,58,0.18); --orange-border:rgba(238,140,58,0.28);
  --navy:#213E40; --navy-deep:#1a2e30; --red:#ef4444; --green:#10b981;
  --gap-xl:clamp(10px,1.6vw,18px); --gap-lg:clamp(7px,1.1vw,14px); --gap-md:clamp(5px,0.9vw,10px);
  --radius:10px; --radius-sm:6px;
  --fs-h1:clamp(18px,2.5vw,24px); --fs-sub:clamp(9px,0.9vw,11px); --fs-label:clamp(8px,0.85vw,10px);
  --fs-value:clamp(10px,1.05vw,12px); --fs-meta:clamp(8px,0.85vw,10px); --fs-btn:clamp(8px,0.85vw,10px);
  --input-height:clamp(34px,4.3vw,40px); --input-font:clamp(11px,1.05vw,13px);
  --input-px:clamp(9px,1.2vw,13px); --input-radius:6px;
  font-family:'Inter',sans-serif;
}
/* Panel shell: orange hairline border + bottom corner brackets + 4 dots (Intake decor) */
.hwPanel{
  border:1px solid var(--orange-border); border-radius:var(--radius); position:relative;
  background-image:
    radial-gradient(circle,var(--orange) 1.3px,transparent 1.8px),
    radial-gradient(circle,var(--orange) 1.3px,transparent 1.8px),
    radial-gradient(circle,var(--orange) 1.3px,transparent 1.8px),
    radial-gradient(circle,var(--orange) 1.3px,transparent 1.8px),
    linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  background-position:calc(50% - 15px) calc(100% - 8px),calc(50% - 5px) calc(100% - 8px),calc(50% + 5px) calc(100% - 8px),calc(50% + 15px) calc(100% - 8px),0 0;
  background-size:4px 4px,4px 4px,4px 4px,4px 4px,auto;
  background-repeat:no-repeat;
}
.hwPanel::before,.hwPanel::after{content:'';position:absolute;bottom:6px;width:14px;height:14px;border-bottom:2px solid var(--orange);pointer-events:none;}
.hwPanel::before{left:8px;border-left:2px solid var(--orange);}
.hwPanel::after{right:8px;border-right:2px solid var(--orange);}
.drawerHeader{background:rgba(0,0,0,0.22);border-bottom:1px solid var(--orange);border-radius:calc(var(--radius) - 1px) calc(var(--radius) - 1px) 0 0;padding:clamp(8px,1.2vw,14px) clamp(10px,1.6vw,18px);}
.drawerTitle{font-family:'Cinzel',serif;color:var(--orange);font-size:clamp(11px,1.3vw,14px);font-weight:700;letter-spacing:2px;text-transform:uppercase;}
.drawerIcon,.chevron{color:var(--orange);}
.panelInner{background:rgba(255,255,255,0.05);}
/* Labels = Intake .label */
.inputLabelRow label,.specLabel{font-family:'Inter',sans-serif;font-size:var(--fs-label);font-weight:900;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:2px;}
.reqStar{color:var(--red);}
.inputHint{font-size:var(--fs-meta);font-weight:700;color:rgba(255,255,255,0.35);letter-spacing:0.5px;}
/* Read-only values = Intake .indexDisplay */
.specValue{font-family:'Space Mono',monospace;font-weight:900;letter-spacing:1px;color:var(--orange);font-size:var(--input-font);}
.specItem{border-left:2px solid rgba(238,140,58,0.35);padding:3px 0 3px 8px;}
/* Editable inputs = Intake .input */
.hwInput,.selectTrigger,.dtInput{
  font-family:'Inter',sans-serif;font-weight:600;border:1.5px solid rgba(238,140,58,0.3);
  background:#ffffff;color:var(--navy);border-radius:var(--input-radius);
  height:var(--input-height);padding:0 var(--input-px);font-size:var(--input-font);
  transition:border-color .2s,box-shadow .2s;width:100%;box-sizing:border-box;
}
.hwInput:hover,.selectTrigger:hover,.dtInput:hover{border-color:var(--orange);}
.hwInput:focus,.selectTrigger:focus,.dtInput:focus{outline:none;border-color:var(--orange);box-shadow:0 0 0 2px rgba(238,140,58,0.15);}
.hwInput::placeholder{color:#9aa8a6;}
.selectValue{color:var(--navy);}
/* Secondary/toggle buttons = Intake .typeBtn / .addBtn */
.tabBtn,.payTypeBtn,.ghostBtn,.addNoteBtn,.addDocBtn{
  font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;text-transform:uppercase;
  background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);
  border-radius:6px;padding:clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px);
}
.tabBtn:hover,.payTypeBtn:hover,.ghostBtn:hover,.addNoteBtn:hover,.addDocBtn:hover{background:rgba(238,140,58,0.12);color:#EE8C3A;border-color:#EE8C3A;}
.tabBtnActive,.tabBtnActive:hover,.payTypeBtnActive,.payTypeBtnActive:hover{background:#EE8C3A;color:#1a2e30;border-color:#EE8C3A;box-shadow:0 0 14px rgba(238,140,58,0.4);}
.addStageBtn{font-family:'Inter',sans-serif;border:2px dashed rgba(238,140,58,0.4);color:var(--orange);background:rgba(238,140,58,0.06);}
/* Primary buttons = Intake .btn.primary (WHITE text on orange) */
.unlockMasterBtn,.btnPrimary{background:var(--orange);color:#fff;border-color:var(--orange);font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;}
.unlockMasterBtn:hover,.btnPrimary:hover{background:#d97a2b;border-color:#d97a2b;color:#fff;}
.btnDanger,.cancelLike{background:rgba(239,68,68,0.08);color:var(--red);border:1.5px solid rgba(239,68,68,0.45);font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;}
.btnDanger:hover{background:rgba(239,68,68,0.16);border-color:var(--red);color:var(--red);}
.dangerBtn{background:var(--red);color:#fff;border:none;font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;border-radius:6px;}
.btn,.ctrlBtnPay,.ctrlBtnReceivable,.purgeBtn,.printBtn{font-family:'Inter',sans-serif;}
/* Stage rows = Intake .stageItem */
.stageRow{background:rgba(0,0,0,0.15);border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius-sm);padding:clamp(6px,0.9vw,9px);}
.stageRowDone{background:rgba(238,140,58,0.07);border-color:var(--orange-border);}
.stageName{font-weight:700;color:#fff;font-size:var(--fs-value);letter-spacing:0.5px;text-transform:none;}
.stageCost{font-family:'Space Mono',monospace;font-size:var(--fs-meta);color:rgba(255,255,255,0.35);}
/* Money boxes = Intake .financialsSummary */
.statBox{background:rgba(0,0,0,0.15);border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius-sm);padding:var(--gap-lg);}
.statBox label{font-family:'Inter',sans-serif;font-size:var(--fs-label);font-weight:900;color:rgba(255,255,255,0.5);letter-spacing:2px;text-transform:uppercase;}
.statBox strong{font-family:'Space Mono',monospace;font-size:var(--input-font);color:var(--orange);letter-spacing:1px;}
/* Portfolio table + headings = Intake tones */
.sectionTitle{font-family:'Cinzel',serif;font-size:clamp(11px,1.3vw,13px);font-weight:700;color:var(--orange);letter-spacing:2px;text-transform:uppercase;}
.portfolioTable{font-family:'Space Mono',monospace;font-size:var(--fs-value);}
.portfolioTable th{font-family:'Inter',sans-serif;font-size:var(--fs-label);font-weight:900;color:rgba(255,255,255,0.5);letter-spacing:2px;border-bottom:1px solid rgba(255,255,255,0.06);}
.portfolioTable td{border-bottom:1px solid rgba(255,255,255,0.06);color:rgba(255,255,255,0.85);}
.textBadge{font-size:var(--fs-meta);font-weight:700;letter-spacing:1px;}
.emptyState span{font-family:'Inter',sans-serif;font-size:var(--fs-meta);font-weight:700;color:rgba(255,255,255,0.35);letter-spacing:0.5px;}
'''
open(css_path, "w", encoding="utf-8").write(css)
print("WROTE: FS-UNIFY v4 (exact Intake port)")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix51: exact Intake design port onto Folder (fonts/sizes/tones/decor verbatim)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: committed and pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")
