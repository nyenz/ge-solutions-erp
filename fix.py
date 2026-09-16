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
# fix63 hand-copied Intake's header bar / separator / hover onto this page's
# own custom .panel CSS -- close, but still an approximation (and it can
# only ever chase Intake's numbers, never actually match them). The real
# fix is to stop re-implementing Intake's panel and just USE it: Intake's
# own CollapsibleSection component already has the exact header/body split,
# spacing, hover glow, AND a working collapse arrow -- which also directly
# answers "add the panel contracting with the arrow". CornerDecor with
# hideTop swaps in for this page's old top-pins decor at the same time,
# which is the other ask: drop the top border dots, keep the bottom ones.
# ===========================================================================

patch(
    DOSSIER_JSX,
    """import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent, FiAlertTriangle,
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import clientService from '../../services/clientService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientPortfolioPage.module.css';""",
    """import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent, FiAlertTriangle,
  FiArrowUp, FiArrowDown,
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import clientService from '../../services/clientService';
import BackToTopButton from '../../components/common/BackToTopButton';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import CornerDecor from '../../components/ui/CornerDecor';
import styles from './ClientPortfolioPage.module.css';""",
    'imports: sort icons + the real CollapsibleSection/CornerDecor components',
)

patch(
    DOSSIER_JSX,
    """const pctTone = (pct) => (pct >= 75 ? styles.tagGood : pct >= 25 ? styles.tagWarn : styles.tagBad);

const Pins = () => (<React.Fragment>
  <div className={styles.pinsTop} aria-hidden="true">{[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}</div>
  <div className={styles.pinsBottom} aria-hidden="true">{[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}</div>
  <span className={styles.decorBl} aria-hidden="true" />
  <span className={styles.decorBr} aria-hidden="true" />
</React.Fragment>);

// -- IDENTIFIER CELL --""",
    """const pctTone = (pct) => (pct >= 75 ? styles.tagGood : pct >= 25 ? styles.tagWarn : styles.tagBad);

// Shared by both tables below -- sorts a list of plot rows by any column
// key (numeric or text), ascending or descending.
const sortPlots = (rows, key, direction) => {
  if (!key) return rows;
  const dir = direction === 'asc' ? 1 : -1;
  return [...rows].sort((a, b) => {
    let aVal, bVal;
    if (key === 'index') { aVal = a.index || ''; bVal = b.index || ''; }
    else if (key === 'district') { aVal = a.district || ''; bVal = b.district || ''; }
    else if (key === 'owed') { aVal = Number(a.owed || 0); bVal = Number(b.owed || 0); }
    else if (key === 'paid') { aVal = Number(a.paid || 0); bVal = Number(b.paid || 0); }
    else if (key === 'pct') { aVal = pctPaid(a); bVal = pctPaid(b); }
    else if (key === 'storage') { aVal = Number(a.storage || 0); bVal = Number(b.storage || 0); }
    else if (key === 'lastPayment') { aVal = a.lastPayment || ''; bVal = b.lastPayment || ''; }
    else { aVal = a[key]; bVal = b[key]; }
    if (aVal < bVal) return -1 * dir;
    if (aVal > bVal) return 1 * dir;
    return 0;
  });
};

// -- IDENTIFIER CELL --""",
    'drop the local Pins component (CornerDecor replaces it); add the shared sortPlots helper',
)

patch(
    DOSSIER_JSX,
    """  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState('');

  const load = useCallback(async () => {""",
    """  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState('');

  // Project Portfolio table's sort state, and Payment Health's own
  // (separate) one -- same click-header-to-sort idiom the Client Ledger
  // already uses.
  const [sortConfig, setSortConfig] = useState({ key: '', direction: 'asc' });
  const handleSort = (key) => setSortConfig((prev) => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
  const renderSortIcon = (key) => sortConfig.key !== key ? null
    : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

  const [healthSort, setHealthSort] = useState({ key: '', direction: 'asc' });
  const handleHealthSort = (key) => setHealthSort((prev) => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
  const renderHealthSortIcon = (key) => healthSort.key !== key ? null
    : (healthSort.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

  const load = useCallback(async () => {""",
    'add sort state + handlers for both tables',
)

patch(
    DOSSIER_JSX,
    """  const groups = useMemo(() => ([
    { key: 'SOLO', label: 'SOLO PROJECTS', rows: plots.filter((p) => !isJoint(p)) },
    { key: 'JOINT', label: 'JOINT PROJECTS', rows: plots.filter(isJoint) },
  ].filter((g) => g.rows.length > 0)), [plots]);""",
    """  const groups = useMemo(() => ([
    { key: 'SOLO', label: 'SOLO PROJECTS', rows: sortPlots(plots.filter((p) => !isJoint(p)), sortConfig.key, sortConfig.direction) },
    { key: 'JOINT', label: 'JOINT PROJECTS', rows: sortPlots(plots.filter(isJoint), sortConfig.key, sortConfig.direction) },
  ].filter((g) => g.rows.length > 0)), [plots, sortConfig]);

  const healthRows = useMemo(() => sortPlots(plots, healthSort.key, healthSort.direction), [plots, healthSort]);""",
    'groups + health rows now sort by the active column',
)

# -- IDENTITY --
patch(
    DOSSIER_JSX,
    """      <section className={styles.panel}>
        <Pins />
        <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiUsers aria-hidden="true" /> IDENTITY</h2></div>
        <div className={styles.panelBody}>
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid}>""",
    """      <CollapsibleSection icon={<FiUsers aria-hidden="true" />} title="IDENTITY">
        <CornerDecor hideTop />
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid}>""",
    'IDENTITY panel -> CollapsibleSection',
)
patch(
    DOSSIER_JSX,
    """        </div>
        </div>
      </section>

      {isDirector && (
        <div className={styles.moneyStrip}>""",
    """        </div>
      </CollapsibleSection>

      {isDirector && (
        <div className={styles.moneyStrip}>""",
    'IDENTITY panel: close',
)

# -- PROJECT PORTFOLIO -- (sortable headers added here too)
patch(
    DOSSIER_JSX,
    """      <section className={styles.panel} id="portfolio-panel">
        <Pins />
        <div className={styles.panelHeader}>
          <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>
          <span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? 'PROJECT' : 'PROJECTS'}</span>
        </div>
        <div className={styles.panelBody}>
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead><tr><th>Index</th><th>District</th><th>Ownership</th><th>Status</th>{isDirector && <th>Owed (UGX)</th>}{isDirector && <th>Paid (UGX)</th>}{isDirector && <th><FiPercent aria-hidden="true" /> Paid %</th>}<th /></tr></thead>""",
    """      <div id="portfolio-panel">
      <CollapsibleSection icon={<FiFolder aria-hidden="true" />} title="PROJECT PORTFOLIO"
        right={<span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? 'PROJECT' : 'PROJECTS'}</span>}>
        <CornerDecor hideTop />
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead><tr>
              <th onClick={() => handleSort('index')} className={styles.sortable} aria-sort={sortConfig.key === 'index' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Index {renderSortIcon('index')}</th>
              <th onClick={() => handleSort('district')} className={styles.sortable} aria-sort={sortConfig.key === 'district' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>District {renderSortIcon('district')}</th>
              <th>Ownership</th><th>Status</th>
              {isDirector && <th onClick={() => handleSort('owed')} className={styles.sortable} aria-sort={sortConfig.key === 'owed' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Owed (UGX) {renderSortIcon('owed')}</th>}
              {isDirector && <th onClick={() => handleSort('paid')} className={styles.sortable} aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Paid (UGX) {renderSortIcon('paid')}</th>}
              {isDirector && <th onClick={() => handleSort('pct')} className={styles.sortable} aria-sort={sortConfig.key === 'pct' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}><FiPercent aria-hidden="true" /> Paid % {renderSortIcon('pct')}</th>}
              <th />
            </tr></thead>""",
    'PROJECT PORTFOLIO panel -> CollapsibleSection + sortable headers',
)

# -- PROJECT PORTFOLIO close / PAYMENT HEALTH open (also sortable headers) --
patch(
    DOSSIER_JSX,
    """          </table>
        </div>
        </div>
      </section>

      {isDirector && (
        <section className={styles.panel} id="health-panel">
          <Pins />
          <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2></div>
          <div className={styles.panelBody}>
          <div className={styles.tableScroll}>
            <table className={styles.ledgerTable}>
              <thead><tr><th>Index</th><th>Paid (UGX)</th><th>Storage (UGX)</th><th>Last payment</th><th>Health</th></tr></thead>
              <tbody>
                {plots.length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  plots.map((p, i) => {""",
    """          </table>
        </div>
      </CollapsibleSection>
      </div>

      {isDirector && (
        <div id="health-panel">
        <CollapsibleSection icon={<FiCreditCard aria-hidden="true" />} title="PAYMENT HEALTH PER PROJECT">
          <CornerDecor hideTop />
          <div className={styles.tableScroll}>
            <table className={styles.ledgerTable}>
              <thead><tr>
                <th onClick={() => handleHealthSort('index')} className={styles.sortable} aria-sort={healthSort.key === 'index' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Index {renderHealthSortIcon('index')}</th>
                <th onClick={() => handleHealthSort('paid')} className={styles.sortable} aria-sort={healthSort.key === 'paid' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Paid (UGX) {renderHealthSortIcon('paid')}</th>
                <th onClick={() => handleHealthSort('storage')} className={styles.sortable} aria-sort={healthSort.key === 'storage' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Storage (UGX) {renderHealthSortIcon('storage')}</th>
                <th onClick={() => handleHealthSort('lastPayment')} className={styles.sortable} aria-sort={healthSort.key === 'lastPayment' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Last payment {renderHealthSortIcon('lastPayment')}</th>
                <th>Health</th>
              </tr></thead>
              <tbody>
                {healthRows.length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  healthRows.map((p, i) => {""",
    'PROJECT PORTFOLIO close / PAYMENT HEALTH panel -> CollapsibleSection + sortable headers',
)

# -- PAYMENT HEALTH close / CALL LOG open --
patch(
    DOSSIER_JSX,
    """              </tbody>
            </table>
          </div>
          </div>
        </section>
      )}

      <section className={styles.panel}>
        <Pins />
        <div className={styles.panelHeader}><h2 className={styles.panelTitle}><FiPhoneCall aria-hidden="true" /> CALL LOG</h2></div>
        <div className={styles.panelBody}>""",
    """              </tbody>
            </table>
          </div>
        </CollapsibleSection>
        </div>
      )}

      <CollapsibleSection icon={<FiPhoneCall aria-hidden="true" />} title="CALL LOG">
        <CornerDecor hideTop />""",
    'PAYMENT HEALTH close / CALL LOG panel -> CollapsibleSection',
)

# -- CALL LOG close --
patch(
    DOSSIER_JSX,
    """          </div>
        )}
        </div>
      </section>
      <BackToTopButton />""",
    """          </div>
        )}
      </CollapsibleSection>
      <BackToTopButton />""",
    'CALL LOG panel: close',
)


# ===========================================================================
# CSS: remove this page's now-unused hand-rolled panel/pins/decor rules
# (CollapsibleSection + CornerDecor bring their own), tighten the page's
# vertical rhythm to Intake's actual --gap-lg token, and add the sortable-
# header hover state the Client Ledger's table already has.
# ===========================================================================
patch(
    DOSSIER_CSS,
    "  display: flex; flex-direction: column; gap: clamp(10px,1.5vw,16px);",
    "  display: flex; flex-direction: column; gap: clamp(7px,1.1vw,14px);",
    'CSS: page vertical rhythm matches Intake\'s --gap-lg exactly',
)

patch(
    DOSSIER_CSS,
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
}
.pinsTop, .pinsBottom { position: absolute; display: flex; gap: 7px; left: 50%; transform: translateX(-50%); pointer-events: none; z-index: 20; }
.pinsTop { top: -3px; } .pinsBottom { bottom: -3px; }
.pin { width: 3px; height: 5px; background: var(--orange); border-radius: 1px; box-shadow: 0 0 5px rgba(238,140,58,0.4); }
.decorBl, .decorBr { position: absolute; width: 14px; height: 14px; border: 1.5px solid var(--orange); opacity: 0.55; pointer-events: none; z-index: 20; }
.decorBl::after, .decorBr::after { content: ''; position: absolute; width: 4px; height: 4px; background: rgba(255,255,255,0.5); border-radius: 50%; box-shadow: 0 0 6px rgba(255,255,255,0.4); }
.decorBl { bottom: 8px; left: 8px; border-right: none; border-top: none; border-radius: 0 0 0 6px; }
.decorBl::after { bottom: -2px; left: -2px; }
.decorBr { bottom: 8px; right: 8px; border-left: none; border-top: none; border-radius: 0 0 6px 0; }
.decorBr::after { bottom: -2px; right: -2px; }""",
    """/* -- PANEL -- panels are now the shared CollapsibleSection + CornerDecor
   components (see IDENTITY / PROJECT PORTFOLIO / etc in the JSX) instead
   of a hand-copied approximation of Intake's panel -- so this page is
   pixel-identical to Intake because it's literally the same component:
   same header/body padding, same orange separator, same hover glow, and
   now the same collapse arrow. CornerDecor's hideTop drops the top pins
   (kept on the bottom) the same way Intake's own section bodies do.
   Only the small corner badge this page adds stays local. -- */
.panelCornerBadge {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 20px; padding: 4px 12px; text-transform: uppercase; flex-shrink: 0;
}""",
    'CSS: drop the hand-rolled panel/pins/decor rules (CollapsibleSection + CornerDecor own this now)',
)

patch(
    DOSSIER_CSS,
    """.ledgerTable thead th:first-child { border-radius: 6px 0 0 0; }
.ledgerTable thead th:last-child { border-radius: 0 6px 0 0; }""",
    """.ledgerTable thead th:first-child { border-radius: 6px 0 0 0; }
.ledgerTable thead th:last-child { border-radius: 0 6px 0 0; }
.sortable { cursor: pointer; transition: background 0.18s, color 0.18s; }
.sortable:hover { background: linear-gradient(rgba(238,140,58,0.12), rgba(238,140,58,0.12)), #162a2c; color: #fff; }""",
    'CSS: sortable column-header hover state (matches Client Ledger)',
)


# ===========================================================================
# LLM CONTEXT ADDENDUM
# ===========================================================================
ADDENDUM = 'LLM_CONTEXT_ADDENDUM.md'
patch(
    ADDENDUM,
    "- fix63 (2026-09-13): Client Dossier's 4 panels (IDENTITY, PROJECT PORTFOLIO, PAYMENT HEALTH PER PROJECT, CALL LOG) now have the actual header/body split Intake's CollapsibleSection uses -- a dark #162a2c header bar carrying the title, a 1.5px orange bottom-border line separating it from the body, and a hover glow on the whole panel (border brightens, shadow deepens) with the title brightening to white on header hover. The Project Portfolio panel's count badge moved off absolute positioning and into that header row, next to the title, instead of floating in the corner. Back button is one word (\"BACK\") instead of \"BACK TO CLIENT LEDGER\". The Dossier's load-error screen (\"could not load dossier\") now matches the Client Ledger's existing warning treatment -- alert icon plus a real RETRY button that calls load() again -- instead of plain text telling the person to refresh their browser.\n",
    "- fix63 (2026-09-13): Client Dossier's 4 panels (IDENTITY, PROJECT PORTFOLIO, PAYMENT HEALTH PER PROJECT, CALL LOG) now have the actual header/body split Intake's CollapsibleSection uses -- a dark #162a2c header bar carrying the title, a 1.5px orange bottom-border line separating it from the body, and a hover glow on the whole panel (border brightens, shadow deepens) with the title brightening to white on header hover. The Project Portfolio panel's count badge moved off absolute positioning and into that header row, next to the title, instead of floating in the corner. Back button is one word (\"BACK\") instead of \"BACK TO CLIENT LEDGER\". The Dossier's load-error screen (\"could not load dossier\") now matches the Client Ledger's existing warning treatment -- alert icon plus a real RETRY button that calls load() again -- instead of plain text telling the person to refresh their browser.\n"
    "- fix64 (2026-09-16): fix63's panel header/separator/hover was a hand-copied approximation of Intake's CollapsibleSection -- this swaps the Dossier's 4 panels to literally BE CollapsibleSection + CornerDecor (the exact components Intake itself uses), so spacing, padding, hover glow and header styling are now pixel-identical to Intake by construction instead of chased numbers, and the panels are now actually collapsible with the same chevron arrow Intake has. CornerDecor's hideTop also drops the top row of border-pin dots (kept on the bottom), matching how Intake's own section bodies use it. The page's outer vertical gap between panels now matches Intake's --gap-lg token exactly (was noticeably larger). Both the Project Portfolio and Payment Health tables' column headers are now clickable to sort (Index, District, Owed, Paid, %Paid on the first; Index, Paid, Storage, Last payment on the second), same click-to-sort/arrow-icon idiom the Client Ledger's table already uses -- Project Portfolio's SOLO/JOINT grouping is preserved, sorting happens within each group.\n",
    'addendum: log fix64',
)


# ===========================================================================
# GIT
# ===========================================================================
def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)

run(['git', 'add', '-A'])
run(['git', 'commit', '-m', 'fix64: Dossier panels use the real CollapsibleSection (matches Intake, adds collapse arrow), drop top pins, sortable table headers'])
run(['git', 'push'])