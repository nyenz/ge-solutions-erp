import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def path(rel):
    return os.path.join(ROOT, rel)

def read(rel):
    with open(path(rel), 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(rel, content):
    os.makedirs(os.path.dirname(path(rel)) or '.', exist_ok=True)
    with open(path(rel), 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(rel, old, new, label):
    content = read(rel)
    count = content.count(old)
    if count == 1:
        content = content.replace(old, new)
        write(rel, content)
        print('OK   - ' + label)
    elif count == 0:
        print('MISSING - ' + label + ' (target not found in ' + rel + ')')
    else:
        print('MISSING - ' + label + ' (target found ' + str(count) + ' times, expected 1, in ' + rel + ')')


DOSSIER_JSX = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx'
DOSSIER_CSS = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.module.css'

# ===========================================================================
# 1) Panel header/body split -- this is the actual structural piece Intake's
#    CollapsibleSection has that the Dossier's plain <h2> panels didn't: a
#    separate dark header bar, an orange bottom-border line separating it
#    from the body, and a hover glow. Restructuring the CSS first, then the
#    4 panels' JSX.
# ===========================================================================
patch(
    DOSSIER_CSS,
    """/* -- PANEL -- the pins + corner-decor card every reference page uses -- */
.panel {
  position: relative; isolation: isolate;
  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px);
}
.panelTitle {
  font-family: 'Cinzel', serif; color: var(--orange); font-size: clamp(12px,1.4vw,15px); font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; margin: 0 0 clamp(10px,1.4vw,16px);
  display: flex; align-items: center; gap: 8px;
}
.panelCornerBadge {
  position: absolute; top: clamp(10px,1.4vw,16px); right: clamp(14px,1.8vw,20px);
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 20px; padding: 4px 12px; text-transform: uppercase; z-index: 5;
}""",
    """/* -- PANEL -- the pins + corner-decor card every reference page uses.
   Header/body split, orange separator line and hover glow now match
   Intake's CollapsibleSection exactly (dark #162a2c header bar, 1.5px
   orange bottom border, whole-panel hover glow, title brightens on
   header hover). -- */
.panel {
  position: relative; isolation: isolate;
  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: 0; transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.panel:hover { border-color: var(--orange); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
.panelHeader {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: clamp(10px,1.4vw,14px) clamp(14px,1.8vw,20px);
  background: #162a2c; border-bottom: 1.5px solid var(--orange);
  border-radius: var(--radius) var(--radius) 0 0;
}
.panelBody { padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px); }
.panelTitle {
  font-family: 'Cinzel', serif; color: var(--orange); font-size: clamp(12px,1.4vw,15px); font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; margin: 0;
  display: flex; align-items: center; gap: 8px; transition: color 0.18s ease;
}
.panelHeader:hover .panelTitle { color: #fff; }
.panelCornerBadge {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 20px; padding: 4px 12px; text-transform: uppercase; flex-shrink: 0;
}""",
    'CSS: panel header/body split + orange separator + hover glow (matches Intake)',
)

# IDENTITY panel
patch(
    DOSSIER_JSX,
    """      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiUsers aria-hidden="true" /> IDENTITY</h2>
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid}>""",
    """      <section className={styles.panel}>
        <Pins />
        <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiUsers aria-hidden="true" /> IDENTITY</h2></div>
        <div className={styles.panelBody}>
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid}>""",
    'IDENTITY panel: header bar',
)
patch(
    DOSSIER_JSX,
    """        </div>
      </section>

      {isDirector && (
        <div className={styles.moneyStrip}>""",
    """        </div>
        </div>
      </section>

      {isDirector && (
        <div className={styles.moneyStrip}>""",
    'IDENTITY panel: close body wrapper',
)

# PROJECT PORTFOLIO panel
patch(
    DOSSIER_JSX,
    """      <section className={styles.panel} id="portfolio-panel">
        <Pins />
        <span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? 'PROJECT' : 'PROJECTS'}</span>
        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>
        <div className={styles.tableScroll}>""",
    """      <section className={styles.panel} id="portfolio-panel">
        <Pins />
        <div className={styles.panelHeader}>
          <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>
          <span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? 'PROJECT' : 'PROJECTS'}</span>
        </div>
        <div className={styles.panelBody}>
        <div className={styles.tableScroll}>""",
    'PROJECT PORTFOLIO panel: header bar (badge moves into the header row)',
)
patch(
    DOSSIER_JSX,
    """          </table>
        </div>
      </section>

      {isDirector && (
        <section className={styles.panel} id="health-panel">
          <Pins />
          <h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2>
          <div className={styles.tableScroll}>""",
    """          </table>
        </div>
        </div>
      </section>

      {isDirector && (
        <section className={styles.panel} id="health-panel">
          <Pins />
          <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2></div>
          <div className={styles.panelBody}>
          <div className={styles.tableScroll}>""",
    'PROJECT PORTFOLIO panel: close body wrapper / PAYMENT HEALTH panel: header bar',
)
patch(
    DOSSIER_JSX,
    """            </table>
          </div>
        </section>
      )}

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiPhoneCall aria-hidden="true" /> CALL LOG</h2>""",
    """            </table>
          </div>
          </div>
        </section>
      )}

      <section className={styles.panel}>
        <Pins />
        <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiPhoneCall aria-hidden="true" /> CALL LOG</h2></div>
        <div className={styles.panelBody}>""",
    'PAYMENT HEALTH panel: close body wrapper / CALL LOG panel: header bar',
)
patch(
    DOSSIER_JSX,
    """          </div>
        )}
      </section>
      <BackToTopButton />""",
    """          </div>
        )}
        </div>
      </section>
      <BackToTopButton />""",
    'CALL LOG panel: close body wrapper',
)

# ===========================================================================
# 2) Back button: one word, not four.
# ===========================================================================
patch(
    DOSSIER_JSX,
    '<FiArrowLeft aria-hidden="true" /> BACK TO CLIENT LEDGER',
    '<FiArrowLeft aria-hidden="true" /> BACK',
    'back button is one word',
)

# ===========================================================================
# 3) Load-error state gets the same warning treatment (icon + a real RETRY
#    button that calls load() again) the Client Ledger already uses --
#    instead of plain unstyled "REFRESH TO RETRY" text that just tells the
#    person to hit their browser's refresh button.
# ===========================================================================
patch(
    DOSSIER_JSX,
    """import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent,
} from 'react-icons/fi';""",
    """import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent, FiAlertTriangle,
} from 'react-icons/fi';""",
    'import FiAlertTriangle',
)
patch(
    DOSSIER_JSX,
    "    <div className={styles.noRecordsBig}>COULD NOT LOAD DOSSIER {loadCode ? '(' + loadCode + ') ' : ''}- REFRESH TO RETRY</div>",
    """    <div className={styles.errorState}>
      <FiAlertTriangle aria-hidden="true" /> COULD NOT LOAD DOSSIER{loadCode ? ' (' + loadCode + ')' : ''} --{' '}
      <button type="button" className={styles.retryBtn} onClick={() => load()}>RETRY</button>
    </div>""",
    'load-error state gets an icon + working RETRY button',
)
patch(
    DOSSIER_CSS,
    """/* -- EMPTY / LOADING -- */
.noRecordsBig { padding: 60px 20px; text-align: center; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }
.noRecords { text-align: center; padding: 24px !important; color: rgba(255,255,255,0.4); font-weight: 700; letter-spacing: 0.5px; }""",
    """/* -- EMPTY / LOADING -- */
.noRecordsBig { padding: 60px 20px; text-align: center; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }
.noRecords { text-align: center; padding: 24px !important; color: rgba(255,255,255,0.4); font-weight: 700; letter-spacing: 0.5px; }
.errorState { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; padding: 60px 20px; text-align: center; color: #fca5a5; font-weight: 800; letter-spacing: 1px; }
.retryBtn { background: none; border: 1px solid var(--red); color: var(--red); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-weight: 800; font-size: inherit; transition: background 0.15s ease; }
.retryBtn:hover { background: rgba(239,68,68,0.12); }""",
    'CSS: errorState + retryBtn (matches Ledger\'s warning treatment)',
)


# ===========================================================================
# LLM CONTEXT ADDENDUM
# ===========================================================================
ADDENDUM = 'LLM_CONTEXT_ADDENDUM.md'
patch(
    ADDENDUM,
    "- fix62 (2026-09-11): follow-up on fix61 per David's review. Dropped the standalone \"RECENCY\" legend label on the Client Ledger -- just the dots with their definitions now. Swapped both pages' recency/health dot colors to match the app's actual existing payment-dot precedent (RecoveryPortal's payDotGreen/Yellow/Red: #22c55e / #f59e0b / #ef4444) instead of fix61's tag-green/amber, which read wrong next to the rest of the app. Replaced fix61's radial-gradient \"light wash\" approximation on both pages' panels and the Dossier's stat cards with the Intake page's REAL lighter gradient (CollapsibleSection.module.css's linear-gradient(135deg,#3a5a5c,#2a4a4c,#213E40)) so they're now pixel-matched to Intake, not just a guess at \"lighter\". Dossier's PROJECTS money-strip card no longer mixes the raw count with the SOLO/JOINT breakdown -- count stays in PROJECTS, breakdown moved to its own new OWNERSHIP card; the project count also now shows as a small corner badge on the Project Portfolio panel itself.\n",
    "- fix62 (2026-09-11): follow-up on fix61 per David's review. Dropped the standalone \"RECENCY\" legend label on the Client Ledger -- just the dots with their definitions now. Swapped both pages' recency/health dot colors to match the app's actual existing payment-dot precedent (RecoveryPortal's payDotGreen/Yellow/Red: #22c55e / #f59e0b / #ef4444) instead of fix61's tag-green/amber, which read wrong next to the rest of the app. Replaced fix61's radial-gradient \"light wash\" approximation on both pages' panels and the Dossier's stat cards with the Intake page's REAL lighter gradient (CollapsibleSection.module.css's linear-gradient(135deg,#3a5a5c,#2a4a4c,#213E40)) so they're now pixel-matched to Intake, not just a guess at \"lighter\". Dossier's PROJECTS money-strip card no longer mixes the raw count with the SOLO/JOINT breakdown -- count stays in PROJECTS, breakdown moved to its own new OWNERSHIP card; the project count also now shows as a small corner badge on the Project Portfolio panel itself.\n"
    "- fix63 (2026-09-13): Client Dossier's 4 panels (IDENTITY, PROJECT PORTFOLIO, PAYMENT HEALTH PER PROJECT, CALL LOG) now have the actual header/body split Intake's CollapsibleSection uses -- a dark #162a2c header bar carrying the title, a 1.5px orange bottom-border line separating it from the body, and a hover glow on the whole panel (border brightens, shadow deepens) with the title brightening to white on header hover. The Project Portfolio panel's count badge moved off absolute positioning and into that header row, next to the title, instead of floating in the corner. Back button is one word (\"BACK\") instead of \"BACK TO CLIENT LEDGER\". The Dossier's load-error screen (\"could not load dossier\") now matches the Client Ledger's existing warning treatment -- alert icon plus a real RETRY button that calls load() again -- instead of plain text telling the person to refresh their browser.\n",
    'addendum: log fix63',
)


# ===========================================================================
# GIT
# ===========================================================================
def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)

run(['git', 'add', '-A'])
run(['git', 'commit', '-m', 'fix63: intake-style panel headers/separator/hover on Dossier, styled load-error, one-word back button'])
run(['git', 'push'])