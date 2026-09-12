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


# ===========================================================================
# FRONTEND: ClientLedgerPage.jsx
# ===========================================================================
LEDGER_JSX = 'erp-frontend/src/pages/Clients/ClientLedgerPage.jsx'

# 1) Dot colors match the app's existing payment-dot precedent
#    (RecoveryPortal's payDotGreen/payDotYellow/payDotRed: #22c55e /
#    #f59e0b / #ef4444) instead of the emerald/amber tag colors fix61
#    borrowed -- ORANGE stays the brand orange for the 4th ("plus") tier.
patch(
    LEDGER_JSX,
    "const BADGE_COLORS = { GREEN: '#34d399', YELLOW: '#fbbf24', ORANGE: '#EE8C3A', RED: '#ef4444' };",
    "const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', ORANGE: '#EE8C3A', RED: '#ef4444' };",
    'ledger: dot colors match the app\'s existing payment-dot green/yellow/red',
)

# 2) Drop the "RECENCY" group label -- just the dots with their
#    definitions, no header word above them.
patch(
    LEDGER_JSX,
    """                <div className={styles.legendRow} aria-label="Legend">
                    <span className={styles.legendGroupLabel}>RECENCY</span>
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (""",
    """                <div className={styles.legendRow} aria-label="Legend">
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (""",
    'ledger: drop RECENCY legend label',
)


# ===========================================================================
# FRONTEND: ClientLedgerPage.module.css
# ===========================================================================
LEDGER_CSS = 'erp-frontend/src/pages/Clients/ClientLedgerPage.module.css'

# Replace the radial-gradient "light wash" hack from fix61 with the
# Intake page's actual lighter panel gradient (CollapsibleSection.module.css
# .section rule) so this reads like a real sibling of Intake, not an
# approximation.
patch(
    LEDGER_CSS,
    ".tablePanel{\n    position:relative;\n    background:radial-gradient(120% 140% at 12% -10%, rgba(244,242,239,0.05), transparent 55%),linear-gradient(160deg,#1c3335 0%,#213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;\n}",
    ".tablePanel{\n    position:relative;\n    background:linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;\n}",
    'ledger CSS: lighter panel background matching Intake exactly',
)


# ===========================================================================
# FRONTEND: ClientPortfolioPage.jsx
# ===========================================================================
DOSSIER_JSX = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx'

# 1) Split "number of projects" from "project type" (ownership breakdown):
#    PROJECTS card now shows only the count; OWNERSHIP is its own card.
patch(
    DOSSIER_JSX,
    """          <div className={`${styles.statCard} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>PROJECTS</label><strong>{totals.count}</strong><span className={styles.statNote}>{totals.solo} SOLO / {totals.joint} JOINT</span>
          </div>
        </div>
      )}""",
    """          <div className={`${styles.statCard} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>PROJECTS</label><strong>{totals.count}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>OWNERSHIP</label><strong className={styles.statTextValue}>{totals.solo} SOLO / {totals.joint} JOINT</strong>
          </div>
        </div>
      )}""",
    'dossier: PROJECTS count and OWNERSHIP breakdown are now separate cards',
)

# 2) The project count moves to a small badge in the Project Portfolio
#    panel's own corner, instead of living inside the money-strip card.
patch(
    DOSSIER_JSX,
    '      <section className={styles.panel} id="portfolio-panel">\n        <Pins />\n        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>',
    '      <section className={styles.panel} id="portfolio-panel">\n        <Pins />\n        <span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? \'PROJECT\' : \'PROJECTS\'}</span>\n        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>',
    'dossier: project count badge in the panel corner',
)


# ===========================================================================
# FRONTEND: ClientPortfolioPage.module.css
# ===========================================================================
DOSSIER_CSS = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.module.css'

# 1) Same Intake-matching lighter gradient on the main panels...
patch(
    DOSSIER_CSS,
    """.panel {
  position: relative; isolation: isolate;
  background: radial-gradient(120% 140% at 12% -10%, rgba(244,242,239,0.05), transparent 55%), linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px);
}""",
    """.panel {
  position: relative; isolation: isolate;
  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px);
}""",
    'dossier CSS: lighter panel background matching Intake exactly',
)

# 2) ...and on the money-strip stat cards, for the same reason.
patch(
    DOSSIER_CSS,
    """.statCard {
  background: radial-gradient(130% 160% at 20% -20%, rgba(244,242,239,0.06), transparent 60%), linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid rgba(255,255,255,0.1);
  border-radius: var(--radius); padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 4px;
}""",
    """.statCard {
  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
  border: 1.5px solid rgba(255,255,255,0.1);
  border-radius: var(--radius); padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 4px;
}""",
    'dossier CSS: lighter stat-card background matching Intake exactly',
)

# 3) Text-value modifier for the new OWNERSHIP card (its value is a
#    short phrase, not a number, so it needs a smaller size than the
#    other cards' big figures).
patch(
    DOSSIER_CSS,
    '.statCard strong { font-family: \'Space Mono\', monospace; font-size: clamp(14px,1.8vw,20px); font-weight: 800; color: #fff; }',
    '.statCard strong { font-family: \'Space Mono\', monospace; font-size: clamp(14px,1.8vw,20px); font-weight: 800; color: #fff; }\n.statTextValue { font-size: clamp(11px,1.3vw,15px); }',
    'dossier CSS: smaller text-value style for the OWNERSHIP card',
)

# 4) Corner badge style for the Project Portfolio panel's project count.
patch(
    DOSSIER_CSS,
    '.panelTitle {\n  font-family: \'Cinzel\', serif; color: var(--orange); font-size: clamp(12px,1.4vw,15px); font-weight: 700;\n  letter-spacing: 2px; text-transform: uppercase; margin: 0 0 clamp(10px,1.4vw,16px);\n  display: flex; align-items: center; gap: 8px;\n}',
    '.panelTitle {\n  font-family: \'Cinzel\', serif; color: var(--orange); font-size: clamp(12px,1.4vw,15px); font-weight: 700;\n  letter-spacing: 2px; text-transform: uppercase; margin: 0 0 clamp(10px,1.4vw,16px);\n  display: flex; align-items: center; gap: 8px;\n}\n.panelCornerBadge {\n  position: absolute; top: clamp(10px,1.4vw,16px); right: clamp(14px,1.8vw,20px);\n  font-family: \'Inter\', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px;\n  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);\n  border-radius: 20px; padding: 4px 12px; text-transform: uppercase; z-index: 5;\n}',
    'dossier CSS: panel corner badge style',
)

# 5) Dot colors match the app's existing payment-dot precedent (see
#    the Ledger patch above) instead of the tag-green/amber this page
#    was using.
patch(
    DOSSIER_CSS,
    """.dotGreen { background: #34d399; box-shadow: 0 0 4px #34d399; }
.dotAmber { background: #fbbf24; box-shadow: 0 0 4px #fbbf24; }
.dotOrange { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.dotRed { background: #ef4444; box-shadow: 0 0 4px #ef4444; }""",
    """.dotGreen { background: #22c55e; box-shadow: 0 0 4px #22c55e; }
.dotAmber { background: #f59e0b; box-shadow: 0 0 4px #f59e0b; }
.dotOrange { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.dotRed { background: #ef4444; box-shadow: 0 0 4px #ef4444; }""",
    'dossier CSS: dot colors match the app\'s existing payment-dot green/yellow/red',
)


# ===========================================================================
# LLM CONTEXT ADDENDUM
# ===========================================================================
ADDENDUM = 'LLM_CONTEXT_ADDENDUM.md'
patch(
    ADDENDUM,
    "- fix61 (2026-09-11): Client Dossier + Client Ledger redesign batch. Backend now exposes real subCounty on both /clients/ledger and /clients/{id}/dossier (was showing District mislabeled as County) -- Ledger's column renamed COUNTY -> SUB-COUNTY and reads it. Both pages' payment-recency dot is now one shared 4-tier scheme: green = paid this month, amber/yellow = ~2 months back, orange = further back (\"plus\"), red = nothing on record yet -- matches the app's existing green/amber/orange/red attention-color rule; no dot description anywhere says the word \"payment\" anymore. Ledger's PLOTS column (and its NO PLOTS tag/filter label) renamed to INDEX / NO PROJECTS, and its row list + search now use project index only, no plot-number fallback. Phone number is bigger on both pages (view mode and the Dossier's edit input). Dossier's editInput padding now matches the app-wide modalInput token. Dossier's panel corner-decor now matches Ledger's exactly (added the missing ::after glow dot). Both pages' dark panels (and the Dossier's stat cards) got a very faint cream-tint radial wash layered under the existing navy gradient -- same low-opacity cream token Shell.module.css already uses, so it's a lighter read without a new color entering the palette. Dossier's money-strip stat cards are now clickable and smooth-scroll to the panel that explains that number (owed/paid/projects -> Project Portfolio, storage -> Payment Health).\n",
    "- fix61 (2026-09-11): Client Dossier + Client Ledger redesign batch. Backend now exposes real subCounty on both /clients/ledger and /clients/{id}/dossier (was showing District mislabeled as County) -- Ledger's column renamed COUNTY -> SUB-COUNTY and reads it. Both pages' payment-recency dot is now one shared 4-tier scheme: green = paid this month, amber/yellow = ~2 months back, orange = further back (\"plus\"), red = nothing on record yet -- matches the app's existing green/amber/orange/red attention-color rule; no dot description anywhere says the word \"payment\" anymore. Ledger's PLOTS column (and its NO PLOTS tag/filter label) renamed to INDEX / NO PROJECTS, and its row list + search now use project index only, no plot-number fallback. Phone number is bigger on both pages (view mode and the Dossier's edit input). Dossier's editInput padding now matches the app-wide modalInput token. Dossier's panel corner-decor now matches Ledger's exactly (added the missing ::after glow dot). Both pages' dark panels (and the Dossier's stat cards) got a very faint cream-tint radial wash layered under the existing navy gradient -- same low-opacity cream token Shell.module.css already uses, so it's a lighter read without a new color entering the palette. Dossier's money-strip stat cards are now clickable and smooth-scroll to the panel that explains that number (owed/paid/projects -> Project Portfolio, storage -> Payment Health).\n"
    "- fix62 (2026-09-11): follow-up on fix61 per David's review. Dropped the standalone \"RECENCY\" legend label on the Client Ledger -- just the dots with their definitions now. Swapped both pages' recency/health dot colors to match the app's actual existing payment-dot precedent (RecoveryPortal's payDotGreen/Yellow/Red: #22c55e / #f59e0b / #ef4444) instead of fix61's tag-green/amber, which read wrong next to the rest of the app. Replaced fix61's radial-gradient \"light wash\" approximation on both pages' panels and the Dossier's stat cards with the Intake page's REAL lighter gradient (CollapsibleSection.module.css's linear-gradient(135deg,#3a5a5c,#2a4a4c,#213E40)) so they're now pixel-matched to Intake, not just a guess at \"lighter\". Dossier's PROJECTS money-strip card no longer mixes the raw count with the SOLO/JOINT breakdown -- count stays in PROJECTS, breakdown moved to its own new OWNERSHIP card; the project count also now shows as a small corner badge on the Project Portfolio panel itself.\n",
    'addendum: log fix62',
)


# ===========================================================================
# GIT
# ===========================================================================
def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)

run(['git', 'add', '-A'])
run(['git', 'commit', '-m', 'fix62: dot colors, drop RECENCY label, split projects/ownership, intake-style lighter panels'])
run(['git', 'push'])