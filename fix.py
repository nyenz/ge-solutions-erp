# fix.py -- fix111: plain glyph back-to-top with distance logic, joint count in label style, sidebar auto-collapse on Recovery
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

# 1. BackToTopButton: plain glyph styling (no bg/border), never blocks when hidden
write(FE / "components" / "common" / "BackToTopButton.module.css",
"""/* fix111: plain glyph back-to-top - no bg, no border, distance-based show, never blocks when hidden */
.backToTop {
  position: fixed;
  right: clamp(10px, 1.6vw, 20px);
  bottom: clamp(10px, 1.6vh, 20px);
  z-index: 400;
  width: clamp(30px, 3.4vw, 38px);
  height: clamp(30px, 3.4vw, 38px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  box-shadow: none;
  color: #EE8C3A;
  font-size: clamp(18px, 2.2vw, 24px);
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transform: translateY(8px);
  transition: opacity 0.25s ease, transform 0.25s ease, color 0.2s, text-shadow 0.2s;
  text-shadow: 0 0 8px rgba(238, 140, 58, 0.35);
}
.backToTop.show { opacity: 1; pointer-events: auto; transform: translateY(0); }
.backToTop:hover { color: #ffffff; text-shadow: 0 0 8px #EE8C3A, 0 0 15px #EE8C3A; }
.backToTop:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; border-radius: 6px; }
""")

# 2. Threshold: 300px from top (distance, not list bottom)
patch(FE / "components" / "common" / "BackToTopButton.jsx", "setShow(currentY() > 240)", "setShow(currentY() > 300)", "300px distance threshold")

# 3. RecoveryPortal: sidebar auto-collapse on mount (replaces click-to-collapse), joint count in label style
jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
patch(jsxp, """  const collapsedOnce = useRef(false);
  useEffect(() => {
    const handler = () => {
      if (collapsedOnce.current) return;
      collapsedOnce.current = true;
      const aside = document.querySelector('aside');
      const toggle = document.querySelector('[class*="sidebarToggle"]');
      if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
    };
    window.addEventListener('click', handler, { once: true });
    return () => window.removeEventListener('click', handler);
  }, []);""",
"""  useEffect(() => {
    const t = setTimeout(() => {
      const aside = document.querySelector('aside');
      const toggle = document.querySelector('[class*="sidebarToggle"]');
      if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
    }, 250);
    return () => clearTimeout(t);
  }, []);""", "sidebar auto-collapse on Recovery mount")
patch(jsxp, "{co.name} ({co.projects})", "{co.name} <span className={styles.coCount}>({co.projects})</span>", "joint count label style")

# 4. CSS: coCount style
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix111" not in s:
    s += """
/* fix111: joint-owner count matches the "Joint with:" label style */
.coCount {
  font-family: 'DM Sans', sans-serif;
  font-size: clamp(10px, 1.05vw, 12px);
  font-weight: 700;
  letter-spacing: 0.4px;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: none;
}
"""
    write(cssp, s)
    print("OK fix111 css")
else:
    print("SKIP fix111 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix111: plain glyph back-to-top with distance logic, joint count in label style, sidebar auto-collapse on Recovery"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")