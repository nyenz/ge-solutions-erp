# fix.py -- fix107: cyan contact number, joint name in label format, matching phone icon, professional fixed back-to-top
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

# 1. Recovery colours: cyan phone, light phone icon, joint name in "Joint with:" label format
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix107" not in s:
    s += """
/* fix107: cyan contact number, phone icon matches other icons, joint name in label format */
.mono { color: #67e8f9; }
.monoRow svg { color: rgba(255, 255, 255, 0.8); }
.coChip {
  font-family: 'DM Sans', sans-serif;
  font-size: clamp(10px, 1.05vw, 12px);
  font-weight: 700;
  letter-spacing: 0.4px;
  color: #67e8f9;
}
"""
    write(cssp, s)
    print("OK fix107 css")
else:
    print("SKIP fix107 css already present")

# 2. Remove fix92 global back-to-top override so the new component styling wins
ix = FE / "index.css"
patch(ix, """/* fix92: back-to-top arrow is a plain glyph pinned bottom-right */
[class*="backToTop"], [class*="BackToTop"], [class*="toTop"] {
  position: fixed !important;
  right: clamp(12px, 2vw, 24px) !important;
  bottom: clamp(12px, 2vh, 24px) !important;
  left: auto !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}""", "/* fix92 back-to-top override removed in fix107 - component now self-positions */", "remove fix92 override")

# 3. Rewrite BackToTopButton: fixed bottom-right, appears after 320px of shell scroll
write(FE / "components" / "common" / "BackToTopButton.jsx",
"""import React, { useEffect, useState } from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

function findScroller() {
  const cands = [
    document.querySelector('[class*="scrollArea"]'),
    document.querySelector('[class*="mainContent"]'),
  ];
  for (const el of cands) if (el && el.scrollHeight > el.clientHeight + 40) return el;
  return document.scrollingElement || document.documentElement;
}

export default function BackToTopButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const scroller = findScroller();
    const onScroll = () => setShow((scroller.scrollTop || window.scrollY || 0) > 320);
    scroller.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
    return () => { scroller.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onScroll); };
  }, []);
  const toTop = () => { const s = findScroller(); s.scrollTo({ top: 0, behavior: 'smooth' }); };
  return (
    <button type="button" className={`${styles.backToTop} ${show ? styles.show : ''}`} onClick={toTop} aria-label="Back to top" tabIndex={show ? 0 : -1}>
      <FiArrowUp aria-hidden="true" />
    </button>
  );
}
""")

write(FE / "components" / "common" / "BackToTopButton.module.css",
"""/* fix107: professional back-to-top - fixed bottom-right, fades in after 320px of scroll */
.backToTop {
  position: fixed;
  right: clamp(14px, 2vw, 24px);
  bottom: clamp(14px, 2vh, 24px);
  z-index: 400;
  width: clamp(34px, 4vw, 42px);
  height: clamp(34px, 4vw, 42px);
  border-radius: 8px;
  border: 1.5px solid rgba(238, 140, 58, 0.4);
  background: rgba(26, 46, 48, 0.92);
  color: #EE8C3A;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transform: translateY(10px);
  transition: opacity 0.25s ease, transform 0.25s ease, background 0.2s, color 0.2s;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
}
.backToTop.show { opacity: 1; pointer-events: auto; transform: translateY(0); }
.backToTop:hover { background: #EE8C3A; color: #1a2e30; }
.backToTop:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }
""")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix107: cyan contact number, joint name in label format, matching phone icon, professional fixed back-to-top"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")