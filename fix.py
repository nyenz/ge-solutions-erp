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
# BACKEND: expose subCounty on both client endpoints (dossier + ledger list)
# so the frontend can show the real Sub-county instead of relabeling
# District as "County".
# ===========================================================================
BACKEND = 'erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryNoteController.java'

patch(
    BACKEND,
    'row.put("district", p.getDistrict());\n',
    'row.put("district", p.getDistrict());\nrow.put("subCounty", p.getSubCounty());\n',
    'backend: add subCounty to /clients/ledger rows',
)

patch(
    BACKEND,
    'pm.put("district", p.getDistrict());\n',
    'pm.put("district", p.getDistrict());\npm.put("subCounty", p.getSubCounty());\n',
    'backend: add subCounty to /clients/{id}/dossier plots',
)


# ===========================================================================
# FRONTEND: ClientLedgerPage.jsx
# ===========================================================================
LEDGER_JSX = 'erp-frontend/src/pages/Clients/ClientLedgerPage.jsx'

# 1) Search fields: drop plot number, search subCounty instead of district
#    (matches the renamed/re-sourced column below).
patch(
    LEDGER_JSX,
    """    const fields = [
        c.name, c.nin, c.phone, c.email,
        ...(c.plots || []).map(p => p.index),
        ...(c.plots || []).map(p => p.plot),
        ...(c.plots || []).map(p => p.district),
    ];""",
    """    const fields = [
        c.name, c.nin, c.phone, c.email,
        ...(c.plots || []).map(p => p.index),
        ...(c.plots || []).map(p => p.subCounty),
    ];""",
    'ledger: search by index/subCounty instead of plot/district',
)

# 2) Recency badge: 4-tier scheme matching the Dossier's Health column
#    exactly (same underlying "last payment" concept, so the same client
#    reads the same color on both pages) -- and no "payment" wording in
#    the labels shown next to the dot.
patch(
    LEDGER_JSX,
    """// -- PAYMENT HEALTH BADGE -- keyed off recency of the client's last
// payment across all their plots (not last contact): GREEN = paid
// within 14 days, YELLOW = paid 2-4 weeks ago, RED = over a month
// since the last payment, or never paid at all.
const getPaymentBadge = (c) => {
    if (!c.lastPaymentAt) return 'RED';
    const days = Math.floor((Date.now() - new Date(c.lastPaymentAt)) / 86400000);
    if (days <= 14) return 'GREEN';
    if (days <= 30) return 'YELLOW';
    return 'RED';
};
const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Recent payment', YELLOW: 'Paid 2-4 weeks ago', RED: 'No recent payment' };""",
    """// -- RECENCY BADGE -- keyed off how long since the client's last
// payment across all their plots (not last contact). Thresholds match
// the Client Dossier's Health column exactly so the same client shows
// the same color on both pages: GREEN = within this month, YELLOW =
// about 2 months back, ORANGE = further back than that, RED = nothing
// on record yet.
const getPaymentBadge = (c) => {
    if (!c.lastPaymentAt) return 'RED';
    const days = Math.floor((Date.now() - new Date(c.lastPaymentAt)) / 86400000);
    if (days <= 30) return 'GREEN';
    if (days <= 60) return 'YELLOW';
    return 'ORANGE';
};
const BADGE_COLORS = { GREEN: '#34d399', YELLOW: '#fbbf24', ORANGE: '#EE8C3A', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Paid this month', YELLOW: 'Paid about 2 months back', ORANGE: 'Over 2 months since paying', RED: 'Nothing on record' };""",
    'ledger: 4-tier recency badge (green/yellow/orange/red), no "payment" wording',
)

# 3) Legend group label -- drop the word "PAYMENT".
patch(
    LEDGER_JSX,
    '<span className={styles.legendGroupLabel}>PAYMENT</span>',
    '<span className={styles.legendGroupLabel}>RECENCY</span>',
    'ledger: legend label PAYMENT -> RECENCY',
)

# 4) Header: COUNTY -> SUB-COUNTY (this column now reads the real
#    subCounty field from the backend, not District under a wrong name).
patch(
    LEDGER_JSX,
    '<th>COUNTY</th>',
    '<th>SUB-COUNTY</th>',
    'ledger: header COUNTY -> SUB-COUNTY',
)

# 5) That column's data source: subCounty, not district.
patch(
    LEDGER_JSX,
    "const countyList = [...new Set((c.plots || []).map(p => p.district).filter(Boolean))];",
    "const countyList = [...new Set((c.plots || []).map(p => p.subCounty).filter(Boolean))];",
    'ledger: county column reads subCounty',
)

# 6) "Plots" column -> "Index": show project index only, no plot-number
#    fallback (single-identity model -- index is the permanent handle).
patch(
    LEDGER_JSX,
    """                                <th onClick={() => handleSort('plotCount')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotCount' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiLayers aria-hidden="true" /> PLOTS {renderSortIcon('plotCount')}
                                </th>""",
    """                                <th onClick={() => handleSort('plotCount')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotCount' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiLayers aria-hidden="true" /> INDEX {renderSortIcon('plotCount')}
                                </th>""",
    'ledger: header PLOTS -> INDEX',
)

patch(
    LEDGER_JSX,
    "const plotNums = (c.plots || []).map(p => p.plot || p.index).filter(Boolean);",
    "const plotNums = (c.plots || []).map(p => p.index).filter(Boolean);",
    'ledger: row list shows index only, no plot-number fallback',
)

patch(
    LEDGER_JSX,
    "{ key: 'PAID', label: 'PAID UP' }, { key: 'NOPLOTS', label: 'NO PLOTS' },",
    "{ key: 'PAID', label: 'PAID UP' }, { key: 'NOPLOTS', label: 'NO PROJECTS' },",
    'ledger: filter label NO PLOTS -> NO PROJECTS',
)

patch(
    LEDGER_JSX,
    ': plotCount === 0 ? <span className={styles.tagIdle}>NO PLOTS</span>',
    ': plotCount === 0 ? <span className={styles.tagIdle}>NO PROJECTS</span>',
    'ledger: status tag NO PLOTS -> NO PROJECTS',
)

patch(
    LEDGER_JSX,
    'placeholder="Search name, NIN, phone, email or plot..."',
    'placeholder="Search name, NIN, phone, email or index..."',
    'ledger: search placeholder plot -> index',
)


# ===========================================================================
# FRONTEND: ClientLedgerPage.module.css
# ===========================================================================
LEDGER_CSS = 'erp-frontend/src/pages/Clients/ClientLedgerPage.module.css'

# Phone number is an important contact field -- make it read clearly
# bigger than the rest of the stacked sub-text next to it.
patch(
    LEDGER_CSS,
    '.ownerPhone{font-family:\'Space Mono\',monospace;font-size:11px;color:rgba(255,255,255,0.7);}',
    '.ownerPhone{font-family:\'Space Mono\',monospace;font-size:clamp(13px,1.3vw,15px);font-weight:700;color:rgba(255,255,255,0.92);}',
    'ledger CSS: bigger/bolder phone number',
)

# Light tone: a faint warm-cream wash (the app's own established cream
# glass token from Shell.module.css, at very low opacity) laid under the
# existing navy panel gradient so the panel reads less flat-dark, without
# introducing a new color into the palette.
patch(
    LEDGER_CSS,
    '.tablePanel{\n    position:relative;\n    background:linear-gradient(160deg,#1c3335 0%,#213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;\n}',
    '.tablePanel{\n    position:relative;\n    background:radial-gradient(120% 140% at 12% -10%, rgba(244,242,239,0.05), transparent 55%),linear-gradient(160deg,#1c3335 0%,#213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;\n}',
    'ledger CSS: subtle light-tone wash on table panel',
)


# ===========================================================================
# FRONTEND: ClientPortfolioPage.jsx
# ===========================================================================
DOSSIER_JSX = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx'

# 1) Phone number: bigger font in both view mode and edit mode.
patch(
    DOSSIER_JSX,
    """          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiPhoneCall aria-hidden="true" /> PHONE</span>
            {isEditing
              ? (<input className={`${styles.editInput} ${fieldErrors.phone ? styles.inputError : ''}`} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />)
              : (<span className={styles.specMono}>{d.phone || '---'}</span>)}
          </div>""",
    """          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiPhoneCall aria-hidden="true" /> PHONE</span>
            {isEditing
              ? (<input className={`${styles.editInput} ${styles.editInputPhone} ${fieldErrors.phone ? styles.inputError : ''}`} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />)
              : (<span className={`${styles.specMono} ${styles.specPhone}`}>{d.phone || '---'}</span>)}
          </div>""",
    'dossier: bigger phone number (view + edit mode)',
)

# 2) Money strip stat cards become interconnected -- clicking one scrolls
#    to the panel that actually explains that number, instead of just
#    sitting there as a dead summary.
patch(
    DOSSIER_JSX,
    """      {isDirector && (
        <div className={styles.moneyStrip}>
          <div className={`${styles.statCard} ${styles.statRed}`}><label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong></div>
          <div className={`${styles.statCard} ${styles.statGreen}`}><label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong></div>
          <div className={`${styles.statCard} ${styles.statAmber}`}><label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong></div>
          <div className={styles.statCard}><label>PROJECTS</label><strong>{totals.count}</strong><span className={styles.statNote}>{totals.solo} SOLO / {totals.joint} JOINT</span></div>
        </div>
      )}""",
    """      {isDirector && (
        <div className={styles.moneyStrip}>
          <div className={`${styles.statCard} ${styles.statRed} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statGreen} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statAmber} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('health-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('health-panel'); } }}>
            <label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>PROJECTS</label><strong>{totals.count}</strong><span className={styles.statNote}>{totals.solo} SOLO / {totals.joint} JOINT</span>
          </div>
        </div>
      )}""",
    'dossier: money strip cards scroll to their matching panel',
)

# 3) The scroll helper + anchor ids it targets.
patch(
    DOSSIER_JSX,
    "  const backBtn = (<button type=\"button\" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden=\"true\" /> BACK TO CLIENT LEDGER</button>);",
    "  const scrollToSection = (elId) => { const el = document.getElementById(elId); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); };\n\n  const backBtn = (<button type=\"button\" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden=\"true\" /> BACK TO CLIENT LEDGER</button>);",
    'dossier: add scrollToSection helper',
)

patch(
    DOSSIER_JSX,
    '      <section className={styles.panel}>\n        <Pins />\n        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>',
    '      <section className={styles.panel} id="portfolio-panel">\n        <Pins />\n        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>',
    'dossier: anchor id on Project Portfolio panel',
)

patch(
    DOSSIER_JSX,
    '        <section className={styles.panel}>\n          <Pins />\n          <h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2>',
    '        <section className={styles.panel} id="health-panel">\n          <Pins />\n          <h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2>',
    'dossier: anchor id on Payment Health panel',
)

# 4) Health dot thresholds + wording: 4 tiers (green/yellow/orange/red),
#    no "payment" word in the description next to the dot.
patch(
    DOSSIER_JSX,
    "const health = dd == null ? { c: styles.dotGrey, t: 'No payment yet' } : dd <= 30 ? { c: styles.dotGreen, t: 'Paid within 30 days' } : dd <= 90 ? { c: styles.dotAmber, t: 'Paid 1-3 months ago' } : { c: styles.dotRed, t: 'No recent payment' };",
    "const health = dd == null ? { c: styles.dotRed, t: 'Nothing received yet' } : dd <= 30 ? { c: styles.dotGreen, t: 'Paid this month' } : dd <= 60 ? { c: styles.dotAmber, t: 'Paid about 2 months ago' } : { c: styles.dotOrange, t: 'Over 2 months since paying' };",
    'dossier: 4-tier health dot (green/yellow/orange/red), no "payment" wording',
)


# ===========================================================================
# FRONTEND: ClientPortfolioPage.module.css
# ===========================================================================
DOSSIER_CSS = 'erp-frontend/src/pages/Clients/ClientPortfolioPage.module.css'

# 1) Uniform input sizing -- match the app-wide modalInput padding token
#    instead of this page's own one-off smaller padding.
patch(
    DOSSIER_CSS,
    """.editInput {
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: clamp(11px,1.05vw,13px);
  border: 1.5px solid rgba(238,140,58,0.3); border-radius: 6px; background: #ffffff; color: var(--navy);
  padding: clamp(6px,0.8vw,9px) clamp(8px,1vw,11px); width: 100%; box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}""",
    """.editInput {
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: clamp(11px,1.05vw,13px);
  border: 1.5px solid rgba(238,140,58,0.3); border-radius: 6px; background: #ffffff; color: var(--navy);
  padding: clamp(9px,1.2vw,13px); width: 100%; box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.editInputPhone { font-size: clamp(14px,1.5vw,17px); font-weight: 700; }""",
    'dossier CSS: uniform input padding (matches modalInput) + bigger phone edit input',
)

# 2) Bigger phone number in view mode.
patch(
    DOSSIER_CSS,
    '.specMono { font-family: \'Space Mono\', monospace; font-size: clamp(11px,1.1vw,13px); font-weight: 700; color: var(--orange); }',
    '.specMono { font-family: \'Space Mono\', monospace; font-size: clamp(11px,1.1vw,13px); font-weight: 700; color: var(--orange); }\n.specPhone { font-size: clamp(14px,1.6vw,18px); font-weight: 800; letter-spacing: 0.5px; }',
    'dossier CSS: bigger phone number in view mode',
)

# 3) Bottom corner decor -- bring the small glow-dot detail over from the
#    Client Ledger's (== Project Ledger's) decorBl/decorBr so both pages
#    use the identical corner decoration, not two slightly different ones.
patch(
    DOSSIER_CSS,
    '.decorBl, .decorBr { position: absolute; width: 14px; height: 14px; border: 1.5px solid var(--orange); opacity: 0.55; pointer-events: none; z-index: 20; }\n.decorBl { bottom: 8px; left: 8px; border-right: none; border-top: none; border-radius: 0 0 0 6px; }\n.decorBr { bottom: 8px; right: 8px; border-left: none; border-top: none; border-radius: 0 0 6px 0; }',
    '.decorBl, .decorBr { position: absolute; width: 14px; height: 14px; border: 1.5px solid var(--orange); opacity: 0.55; pointer-events: none; z-index: 20; }\n.decorBl::after, .decorBr::after { content: \'\'; position: absolute; width: 4px; height: 4px; background: rgba(255,255,255,0.5); border-radius: 50%; box-shadow: 0 0 6px rgba(255,255,255,0.4); }\n.decorBl { bottom: 8px; left: 8px; border-right: none; border-top: none; border-radius: 0 0 0 6px; }\n.decorBl::after { bottom: -2px; left: -2px; }\n.decorBr { bottom: 8px; right: 8px; border-left: none; border-top: none; border-radius: 0 0 6px 0; }\n.decorBr::after { bottom: -2px; right: -2px; }',
    'dossier CSS: match Ledger\'s corner-decor glow dot exactly',
)

# 4) Light tone wash on the main dark panels -- same low-opacity cream
#    token as the Ledger page, so the two match and the page reads less
#    flat-dark overall.
patch(
    DOSSIER_CSS,
    """.panel {
  position: relative; isolation: isolate;
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px);
}""",
    """.panel {
  position: relative; isolation: isolate;
  background: radial-gradient(120% 140% at 12% -10%, rgba(244,242,239,0.05), transparent 55%), linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(14px,2vw,22px) clamp(14px,1.8vw,20px);
}""",
    'dossier CSS: subtle light-tone wash on main panels',
)

# 5) Same light-tone treatment on the money-strip stat cards, plus a
#    clickable affordance for the new interconnected stat cards.
patch(
    DOSSIER_CSS,
    """.statCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%); border: 1.5px solid rgba(255,255,255,0.1);
  border-radius: var(--radius); padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 4px;
}""",
    """.statCard {
  background: radial-gradient(130% 160% at 20% -20%, rgba(244,242,239,0.06), transparent 60%), linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid rgba(255,255,255,0.1);
  border-radius: var(--radius); padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 4px;
}
.statClickable { cursor: pointer; transition: transform 0.2s ease, border-color 0.2s ease; }
.statClickable:hover { border-color: var(--orange); transform: translateY(-2px); }
.statClickable:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }""",
    'dossier CSS: light-tone stat cards + clickable affordance',
)

# 6) 4-tier health dots -- yellow (2 months) is now its own amber tone,
#    separate from orange ("plus"/further back); grey ("never") is gone
#    since "never" is now red, matching the rest of the app's color rule
#    (red = debt/danger, the worst state).
patch(
    DOSSIER_CSS,
    """.dotGreen { background: #34d399; box-shadow: 0 0 4px #34d399; }
.dotAmber { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.dotRed { background: #ef4444; box-shadow: 0 0 4px #ef4444; }
.dotGrey { background: rgba(255,255,255,0.25); }""",
    """.dotGreen { background: #34d399; box-shadow: 0 0 4px #34d399; }
.dotAmber { background: #fbbf24; box-shadow: 0 0 4px #fbbf24; }
.dotOrange { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.dotRed { background: #ef4444; box-shadow: 0 0 4px #ef4444; }""",
    'dossier CSS: 4-tier dot colors (green/amber/orange/red)',
)


# ===========================================================================
# LLM CONTEXT ADDENDUM
# ===========================================================================
ADDENDUM = 'LLM_CONTEXT_ADDENDUM.md'
patch(
    ADDENDUM,
    "\n- fix60 (2026-09-03): dedupe FolderPortalController problem put; app-wide removal of CANCEL buttons that sit beside the animated X (design rule: X is the closer); verified one-word badges + RELATED PROJECTS on Folder page.\n",
    "\n- fix60 (2026-09-03): dedupe FolderPortalController problem put; app-wide removal of CANCEL buttons that sit beside the animated X (design rule: X is the closer); verified one-word badges + RELATED PROJECTS on Folder page.\n"
    "- fix61 (2026-09-11): Client Dossier + Client Ledger redesign batch. Backend now exposes real subCounty on both /clients/ledger and /clients/{id}/dossier (was showing District mislabeled as County) -- Ledger's column renamed COUNTY -> SUB-COUNTY and reads it. Both pages' payment-recency dot is now one shared 4-tier scheme: green = paid this month, amber/yellow = ~2 months back, orange = further back (\"plus\"), red = nothing on record yet -- matches the app's existing green/amber/orange/red attention-color rule; no dot description anywhere says the word \"payment\" anymore. Ledger's PLOTS column (and its NO PLOTS tag/filter label) renamed to INDEX / NO PROJECTS, and its row list + search now use project index only, no plot-number fallback. Phone number is bigger on both pages (view mode and the Dossier's edit input). Dossier's editInput padding now matches the app-wide modalInput token. Dossier's panel corner-decor now matches Ledger's exactly (added the missing ::after glow dot). Both pages' dark panels (and the Dossier's stat cards) got a very faint cream-tint radial wash layered under the existing navy gradient -- same low-opacity cream token Shell.module.css already uses, so it's a lighter read without a new color entering the palette. Dossier's money-strip stat cards are now clickable and smooth-scroll to the panel that explains that number (owed/paid/projects -> Project Portfolio, storage -> Payment Health).\n",
    'addendum: log fix61',
)


# ===========================================================================
# GIT
# ===========================================================================
def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)

run(['git', 'add', '-A'])
run(['git', 'commit', '-m', 'fix61: client dossier + client ledger redesign batch'])
run(['git', 'push'])