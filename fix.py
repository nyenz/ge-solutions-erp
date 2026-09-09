# fix.py -- fix108: back-to-top capture-scroll fix, remove all underlines on Recovery, legend family/weight = Ledger Inter 700
import subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)

# 1. BackToTopButton: capture-phase scroll listener works on ANY scroller
write(FE / "components" / "common" / "BackToTopButton.jsx",
"""import React, { useEffect, useState } from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

function scrollers() {
  const list = [];
  const a = document.querySelector('[class*="scrollArea"]');
  const b = document.querySelector('[class*="mainContent"]');
  if (a) list.push(a);
  if (b && b !== a) list.push(b);
  return list;
}
function currentY() {
  let y = window.scrollY || 0;
  for (const el of scrollers()) y = Math.max(y, el.scrollTop || 0);
  return y;
}

export default function BackToTopButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(currentY() > 240);
    document.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', onScroll);
    onScroll();
    return () => {
      document.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onScroll);
    };
  }, []);
  const toTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    for (const el of scrollers()) el.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return (
    <button type="button" className={`${styles.backToTop} ${show ? styles.show : ''}`} onClick={toTop} aria-label="Back to top" tabIndex={show ? 0 : -1}>
      <FiArrowUp aria-hidden="true" />
    </button>
  );
}
""")

# 2. index.css: strip any leftover global backToTop override blocks
ix = FE / "index.css"
s = read(ix)
s2 = re.sub(r'/\*[^*]*back-to-top[^*]*\*/\s*', '', s, flags=re.I)
s2 = re.sub(r'\[class\*="backToTop"\][^}]*\}', '', s2)
s2 = re.sub(r'\[class\*="BackToTop"\][^}]*\}', '', s2)
s2 = re.sub(r'\[class\*="toTop"\][^}]*\}', '', s2)
if s2 != s:
    write(ix, s2)
    print("OK index.css cleaned")
else:
    print("SKIP index.css already clean")

# 3. Recovery css: no underlines anywhere + legend = Ledger Inter 700
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix108" not in s:
    s += """
/* fix108: no underlines anywhere on Recovery + legend matches Ledger Inter 700 exactly */
.projLink, .cardBtnLink, .chipPos, .chipNeg, .chipNone, .coChip, .mono, .nin, .loc, .coLine, .attemptLine, .reason, .dayChip {
  text-decoration: none !important;
  border-bottom: none !important;
}
.dotLegend span {
  font-family: 'Inter', sans-serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: normal;
  text-transform: none;
  color: rgba(26, 46, 48, 0.6);
}
"""
    write(cssp, s)
    print("OK fix108 css")
else:
    print("SKIP fix108 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix108: back-to-top capture-scroll fix, remove all underlines on Recovery, legend family/weight = Ledger Inter 700"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")