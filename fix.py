# PATH: fix.py
# EXPENSES ANALYTICS + AUTOCOMPLETE + AUDIT LABELS (PHASE)
# Run from project root: python fix.py   (or: py fix.py)
# Requires the "Rebuild Expenses page" fix.py (Expense/ExpensePreset flat
# model) to already be applied and deployed -- this phase builds on top
# of it, it does not replace it.
#
# WHY: the Expenses rebuild shipped the flat cash-out log, presets, the
# 24h edit window, and a Director-only category-breakdown summary -- but
# a few things that were designed for this page never actually got
# built:
#
#   1. A real spending-over-time graph. The ANALYSIS panel only ever
#      showed a single total for the selected period, never a trend.
#      This phase adds a DAY/WEEK/MONTH-bucketed bar chart.
#   2. A "by staff" breakdown, so a Director can see who is spending
#      the most without leaving the page.
#   3. Audit page label mapping. New expense action codes (EXPENSE_
#      LOGGED, EXPENSE_EDITED, EXPENSE_DELETED, EXPENSE_PRESET_CREATED)
#      were showing up as raw strings in the Audit Log instead of
#      readable text.
#   4. Category autocomplete. Typing a category in the "OTHER" log
#      flow, or editing a category on an existing entry, was a blank
#      text box with no memory of what has been typed before.
#
# NOTE ON THE 24-HOUR EDIT RULE: this was already correct. Any
# Manager+ user can already edit ANY entry (not just their own) within
# 24 hours of it being logged -- ExpenseService.editExpense() only
# checks Expense.isEditable() (a pure time check), it never checks who
# recorded it. Nothing to fix there; left untouched.
#
# BACKEND (patches):
#   - ExpenseRepository.java: adds findDistinctCategories(),
#     sumByStaffBetween(), findByCreatedAtBetweenOrderByCreatedAtAsc().
#   - ExpenseService.java: adds getCategorySuggestions(), getByStaff(),
#     getTimeSeries() (buckets by DAY/WEEK/MONTH in Java, same pattern
#     used elsewhere in this codebase for the old CompanyExpense
#     analytics).
#   - ExpenseController.java: adds GET /categories (Manager+), and
#     GET /analytics/by-staff + GET /analytics/timeseries (Director/
#     Admin only, same access level as the existing /summary and
#     /search endpoints).
#
# FRONTEND (patches):
#   - expenseService.js: adds getCategories(), getByStaff(),
#     getTimeSeries().
#   - ExpensesPage.jsx / .module.css: the ANALYSIS panel gains a BY
#     STAFF bar breakdown and a SPENDING OVER TIME chart with a DAY/
#     WEEK/MONTH toggle, both loaded alongside the existing summary
#     whenever a Director opens the panel. A shared <datalist> of
#     every category ever logged now backs the "OTHER" category field
#     and the edit-modal category field, so typing repeats what's
#     already been used instead of starting from nothing.
#   - AuditPage.jsx: adds friendly labels for the four expense action
#     codes.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone
# (most likely meaning this phase, or a later one, is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# (file, old, new) patches applied with str.replace, in order
PATCHES = [
    # ---------------------------------------------------------------
    # BACKEND: repository -- category list, by-staff totals, raw rows
    # for the time-series bucketer
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpenseRepository.java",
        '''    @Query("SELECT e.category, COALESCE(SUM(e.amount), 0) FROM Expense e GROUP BY e.category ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByCategoryAll();
}
''',
        '''    @Query("SELECT e.category, COALESCE(SUM(e.amount), 0) FROM Expense e GROUP BY e.category ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByCategoryAll();

    /** Powers the category autocomplete on the "OTHER" log field and the edit modal. */
    @Query("SELECT DISTINCT e.category FROM Expense e ORDER BY e.category ASC")
    List<String> findDistinctCategories();

    @Query("SELECT e.recordedBy, COALESCE(SUM(e.amount), 0) FROM Expense e " +
           "WHERE e.createdAt >= :from AND e.createdAt <= :to " +
           "GROUP BY e.recordedBy ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByStaffBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);

    /** Raw rows for the spending-over-time graph -- bucketed in Java, see ExpenseService.getTimeSeries(). */
    List<Expense> findByCreatedAtBetweenOrderByCreatedAtAsc(LocalDateTime from, LocalDateTime to);
}
''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: service -- category suggestions, by-staff, time series
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/ExpenseService.java",
        '''import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;''',
        '''import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.WeekFields;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/ExpenseService.java",
        '''        auditService.logAction("EXPENSE_PRESET_CREATED",
            "Operator [" + getCurrentOperator() + "] created expense preset: " + trimmed);

        return saved;
    }

    // -- LOGGING ------------------------------------------------------''',
        '''        auditService.logAction("EXPENSE_PRESET_CREATED",
            "Operator [" + getCurrentOperator() + "] created expense preset: " + trimmed);

        return saved;
    }

    /** Every distinct category ever logged -- feeds the "type it yourself" autocomplete. */
    @Transactional(readOnly = true)
    public List<String> getCategorySuggestions() {
        return expenseRepository.findDistinctCategories();
    }

    // -- LOGGING ------------------------------------------------------''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/ExpenseService.java",
        '''        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", total);
        result.put("byCategory", byCategory);
        return result;
    }

    // -- LIVE, NOT TIME-WINDOWED (used by the main Director Dashboard) -''',
        '''        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", total);
        result.put("byCategory", byCategory);
        return result;
    }

    // -- DIRECTOR ANALYSIS: BY STAFF -----------------------------------

    @Transactional(readOnly = true)
    public Map<String, BigDecimal> getByStaff(LocalDateTime from, LocalDateTime to) {
        Map<String, BigDecimal> byStaff = new LinkedHashMap<>();
        for (Object[] row : expenseRepository.sumByStaffBetween(from, to)) {
            String who = row[0] != null ? (String) row[0] : "UNKNOWN";
            byStaff.put(who, (BigDecimal) row[1]);
        }
        return byStaff;
    }

    // -- DIRECTOR ANALYSIS: SPENDING OVER TIME (DAY / WEEK / MONTH) ---

    /**
     * Buckets are computed in Java (not SQL) so the same logic works the
     * same way regardless of the underlying database -- same approach
     * used by the old CompanyExpense analytics before the Expenses
     * rebuild. Empty buckets are simply absent from the result; the
     * frontend only needs the points that exist.
     */
    @Transactional(readOnly = true)
    public List<Map<String, Object>> getTimeSeries(LocalDateTime from, LocalDateTime to, String bucket) {
        List<Expense> rows = expenseRepository.findByCreatedAtBetweenOrderByCreatedAtAsc(from, to);
        String normalizedBucket = (bucket == null || bucket.isBlank()) ? "DAY" : bucket.toUpperCase();

        Map<String, BigDecimal> totals = new TreeMap<>();
        DateTimeFormatter dayFmt = DateTimeFormatter.ISO_LOCAL_DATE;
        WeekFields wf = WeekFields.ISO;

        for (Expense e : rows) {
            if (e.getCreatedAt() == null) continue;
            var date = e.getCreatedAt().toLocalDate();
            String key;
            switch (normalizedBucket) {
                case "MONTH":
                    key = date.getYear() + "-" + String.format("%02d", date.getMonthValue());
                    break;
                case "WEEK":
                    int week = date.get(wf.weekOfWeekBasedYear());
                    key = date.getYear() + "-W" + String.format("%02d", week);
                    break;
                case "DAY":
                default:
                    key = date.format(dayFmt);
                    break;
            }
            totals.merge(key, e.getAmount(), BigDecimal::add);
        }

        List<Map<String, Object>> series = new ArrayList<>();
        for (Map.Entry<String, BigDecimal> entry : totals.entrySet()) {
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("bucket", entry.getKey());
            point.put("total", entry.getValue());
            series.add(point);
        }
        return series;
    }

    // -- LIVE, NOT TIME-WINDOWED (used by the main Director Dashboard) -''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: controller -- /categories (Manager+), /analytics/by-staff
    # and /analytics/timeseries (Director/Admin only, same as /summary)
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/ExpenseController.java",
        '''    @PostMapping("/presets")
    public ResponseEntity<ExpensePreset> createPreset(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("name");
        return ResponseEntity.ok(expenseService.createPreset(name));
    }

    // -- LOGGING (Manager+) -------------------------------------------''',
        '''    @PostMapping("/presets")
    public ResponseEntity<ExpensePreset> createPreset(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("name");
        return ResponseEntity.ok(expenseService.createPreset(name));
    }

    // -- CATEGORY AUTOCOMPLETE (Manager+) ------------------------------

    @GetMapping("/categories")
    public ResponseEntity<List<String>> getCategorySuggestions() {
        return ResponseEntity.ok(expenseService.getCategorySuggestions());
    }

    // -- LOGGING (Manager+) -------------------------------------------''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/ExpenseController.java",
        '''        return ResponseEntity.ok(expenseService.getSummary(fromDt, toDt));
    }
}
''',
        '''        return ResponseEntity.ok(expenseService.getSummary(fromDt, toDt));
    }

    // -- ANALYSIS: BY STAFF (DIRECTOR/ADMIN ONLY) -----------------------

    @GetMapping("/analytics/by-staff")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Map<String, BigDecimal>> byStaff(
            @RequestParam(defaultValue = "MONTH") String period,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to) {
        LocalDateTime[] range = resolveRange(period, from, to);
        return ResponseEntity.ok(expenseService.getByStaff(range[0], range[1]));
    }

    // -- ANALYSIS: SPENDING OVER TIME (DIRECTOR/ADMIN ONLY) -------------

    @GetMapping("/analytics/timeseries")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<List<Map<String, Object>>> timeseries(
            @RequestParam(defaultValue = "MONTH") String period,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(defaultValue = "DAY") String bucket) {
        LocalDateTime[] range = resolveRange(period, from, to);
        return ResponseEntity.ok(expenseService.getTimeSeries(range[0], range[1], bucket));
    }

    /** Same TODAY/WEEK/MONTH/YEAR/CUSTOM resolution already used by getSummary(), shared here. */
    private LocalDateTime[] resolveRange(String period, String from, String to) {
        LocalDateTime fromDt;
        LocalDateTime toDt = LocalDateTime.now();

        if ("CUSTOM".equalsIgnoreCase(period) && from != null && !from.isBlank()) {
            fromDt = LocalDate.parse(from).atStartOfDay();
            toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : toDt;
        } else {
            switch (period.toUpperCase()) {
                case "TODAY": fromDt = LocalDate.now().atStartOfDay(); break;
                case "WEEK":  fromDt = LocalDate.now().minusDays(7).atStartOfDay(); break;
                case "YEAR":  fromDt = LocalDate.now().minusYears(1).atStartOfDay(); break;
                case "MONTH":
                default:      fromDt = LocalDate.now().minusDays(30).atStartOfDay(); break;
            }
        }
        return new LocalDateTime[]{fromDt, toDt};
    }
}
''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: service -- categories, by-staff, timeseries calls
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/services/expenseService.js",
        '''    getSummary: async (period = 'MONTH', from, to) => {
        const response = await api.get('/finance/expenses/summary', {
            params: { period, from, to }
        });
        return response.data;
    },
};''',
        '''    getSummary: async (period = 'MONTH', from, to) => {
        const response = await api.get('/finance/expenses/summary', {
            params: { period, from, to }
        });
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get('/finance/expenses/categories');
        return response.data;
    },

    getByStaff: async (period = 'MONTH', from, to) => {
        const response = await api.get('/finance/expenses/analytics/by-staff', {
            params: { period, from, to }
        });
        return response.data;
    },

    getTimeSeries: async (period = 'MONTH', from, to, bucket = 'DAY') => {
        const response = await api.get('/finance/expenses/analytics/timeseries', {
            params: { period, from, to, bucket }
        });
        return response.data;
    },
};''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: ExpensesPage.jsx -- category state + fetch, By Staff
    # + Spending Over Time panels, shared category datalist
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''    const [presets, setPresets] = useState([]);
    const [recent, setRecent] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);''',
        '''    const [presets, setPresets] = useState([]);
    const [recent, setRecent] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [presetData, recentData] = await Promise.all([
                expenseService.getPresets(),
                expenseService.getRecent(EDIT_WINDOW_HOURS),
            ]);
            setPresets(presetData || []);
            setRecent(recentData || []);
        } catch {
            flash('Could not load expenses. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, []);''',
        '''    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [presetData, recentData, categoryData] = await Promise.all([
                expenseService.getPresets(),
                expenseService.getRecent(EDIT_WINDOW_HOURS),
                expenseService.getCategories(),
            ]);
            setPresets(presetData || []);
            setRecent(recentData || []);
            setCategories(categoryData || []);
        } catch {
            flash('Could not load expenses. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, []);''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''    // -- DIRECTOR ANALYSIS --------------------------------------------
    const [analysisOpen, setAnalysisOpen] = useState(false);
    const [period, setPeriod] = useState('MONTH');
    const [summary, setSummary] = useState({ total: 0, byCategory: {} });
    const [summaryLoading, setSummaryLoading] = useState(false);

    const [filters, setFilters] = useState({ from: '', to: '', category: '', recordedBy: '', minAmount: '', maxAmount: '' });
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    const loadSummary = useCallback(async (p) => {
        setSummaryLoading(true);
        try {
            const data = await expenseService.getSummary(p);
            setSummary(data || { total: 0, byCategory: {} });
        } catch {
            flash('Could not load the analysis summary.', 'error');
        } finally {
            setSummaryLoading(false);
        }
    }, []);

    useEffect(() => {
        if (isDirector && analysisOpen) loadSummary(period);
    }, [isDirector, analysisOpen, period, loadSummary]);''',
        '''    // -- DIRECTOR ANALYSIS --------------------------------------------
    const [analysisOpen, setAnalysisOpen] = useState(false);
    const [period, setPeriod] = useState('MONTH');
    const [summary, setSummary] = useState({ total: 0, byCategory: {} });
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [byStaff, setByStaff] = useState({});
    const [staffLoading, setStaffLoading] = useState(false);
    const [series, setSeries] = useState([]);
    const [bucket, setBucket] = useState('DAY');
    const [seriesLoading, setSeriesLoading] = useState(false);

    const [filters, setFilters] = useState({ from: '', to: '', category: '', recordedBy: '', minAmount: '', maxAmount: '' });
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    const loadSummary = useCallback(async (p) => {
        setSummaryLoading(true);
        try {
            const data = await expenseService.getSummary(p);
            setSummary(data || { total: 0, byCategory: {} });
        } catch {
            flash('Could not load the analysis summary.', 'error');
        } finally {
            setSummaryLoading(false);
        }
    }, []);

    const loadByStaff = useCallback(async (p) => {
        setStaffLoading(true);
        try {
            const data = await expenseService.getByStaff(p);
            setByStaff(data || {});
        } catch {
            flash('Could not load the staff breakdown.', 'error');
        } finally {
            setStaffLoading(false);
        }
    }, []);

    const loadSeries = useCallback(async (p, b) => {
        setSeriesLoading(true);
        try {
            const data = await expenseService.getTimeSeries(p, undefined, undefined, b);
            setSeries(data || []);
        } catch {
            flash('Could not load the spending trend.', 'error');
        } finally {
            setSeriesLoading(false);
        }
    }, []);

    useEffect(() => {
        if (isDirector && analysisOpen) {
            loadSummary(period);
            loadByStaff(period);
            loadSeries(period, bucket);
        }
    }, [isDirector, analysisOpen, period, bucket, loadSummary, loadByStaff, loadSeries]);''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''    const maxCategoryAmount = useMemo(() => {
        const vals = Object.values(summary.byCategory || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [summary]);''',
        '''    const maxCategoryAmount = useMemo(() => {
        const vals = Object.values(summary.byCategory || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [summary]);

    const maxStaffAmount = useMemo(() => {
        const vals = Object.values(byStaff || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [byStaff]);

    const maxSeriesAmount = useMemo(() => {
        return series.length ? Math.max(...series.map(pt => Number(pt.total))) : 0;
    }, [series]);''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''            {message && (
                <div className={`${styles.flashBanner} ${styles['flash_' + message.type]}`}>
                    {message.text}
                </div>
            )}

            {/* PRESET GRID -- ONE TAP LOGGING */}''',
        '''            {message && (
                <div className={`${styles.flashBanner} ${styles['flash_' + message.type]}`}>
                    {message.text}
                </div>
            )}

            {/* Shared autocomplete source for every "type it yourself" category field */}
            <datalist id="expense-categories">
                {categories.map(c => <option key={c} value={c} />)}
            </datalist>

            {/* PRESET GRID -- ONE TAP LOGGING */}''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''                        <div className={styles.searchDivider}>SEARCH ALL EXPENSES</div>''',
        '''                        <div className={styles.sectionLabel}>BY STAFF</div>
                        <div className={styles.categoryBars}>
                            {Object.entries(byStaff || {}).map(([who, amt]) => (
                                <div key={who} className={styles.barRow}>
                                    <span className={styles.barLabel}>{who}</span>
                                    <div className={styles.barTrack}>
                                        <div
                                            className={styles.barFill}
                                            style={{ width: maxStaffAmount ? `${(Number(amt) / maxStaffAmount) * 100}%` : '0%' }}
                                        />
                                    </div>
                                    <span className={styles.barValue}>UGX {fmt(amt)}</span>
                                </div>
                            ))}
                            {!staffLoading && Object.keys(byStaff || {}).length === 0 && (
                                <div className={styles.emptyCell}>NO EXPENSES IN THIS PERIOD</div>
                            )}
                        </div>

                        <div className={styles.sectionLabel}>SPENDING OVER TIME</div>
                        <div className={styles.bucketRow}>
                            {['DAY', 'WEEK', 'MONTH'].map(b => (
                                <button
                                    key={b}
                                    className={bucket === b ? styles.bucketBtnActive : styles.bucketBtn}
                                    onClick={() => setBucket(b)}
                                >
                                    {b}
                                </button>
                            ))}
                        </div>
                        {seriesLoading ? (
                            <div className={styles.emptyCell}>LOADING TREND...</div>
                        ) : series.length === 0 ? (
                            <div className={styles.emptyCell}>NO ACTIVITY IN THIS WINDOW</div>
                        ) : (
                            <div className={styles.tsChart}>
                                {series.map(point => (
                                    <div key={point.bucket} className={styles.tsBarWrap} title={`${point.bucket}: UGX ${fmt(point.total)}`}>
                                        <div className={styles.tsBarTrack}>
                                            <div
                                                className={styles.tsBarFill}
                                                style={{ height: maxSeriesAmount ? `${Math.max(2, (Number(point.total) / maxSeriesAmount) * 100)}%` : '2%' }}
                                            />
                                        </div>
                                        <span className={styles.tsBarLabel}>{point.bucket.slice(-5)}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.searchDivider}>SEARCH ALL EXPENSES</div>''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''                        <input
                            type="text"
                            className={modalStyles.modalInput}
                            placeholder="e.g. Courier fee"
                            value={logCategory}
                            onChange={e => setLogCategory(e.target.value)}
                        />''',
        '''                        <input
                            type="text"
                            list="expense-categories"
                            className={modalStyles.modalInput}
                            placeholder="e.g. Courier fee"
                            value={logCategory}
                            onChange={e => setLogCategory(e.target.value)}
                        />''',
    ),
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.jsx",
        '''                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        value={editCategory}
                        onChange={e => setEditCategory(e.target.value)}
                    />''',
        '''                    <input
                        type="text"
                        list="expense-categories"
                        className={modalStyles.modalInput}
                        value={editCategory}
                        onChange={e => setEditCategory(e.target.value)}
                    />''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: CSS -- section labels, bucket toggle, time-series bars
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/Financials/ExpensesPage.module.css",
        '''.barValue { font-size: 11px; font-weight: 800; text-align: right; color: rgba(255,255,255,0.7); }

.searchDivider {''',
        '''.barValue { font-size: 11px; font-weight: 800; text-align: right; color: rgba(255,255,255,0.7); }

.sectionLabel {
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--orange);
    text-transform: uppercase;
    margin: 18px 0 10px;
}

.bucketRow { display: flex; gap: 6px; margin-bottom: 12px; }
.bucketBtn, .bucketBtnActive {
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 0.6px;
    cursor: pointer;
}
.bucketBtn { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: rgba(255,255,255,0.7); }
.bucketBtn:hover { background: rgba(255,255,255,0.12); }
.bucketBtnActive { background: var(--orange); border: 1px solid var(--orange); color: #fff; }

.tsChart { display: flex; gap: 6px; overflow-x: auto; padding: 4px 4px 0; align-items: flex-end; min-height: 140px; }
.tsBarWrap { display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; width: 32px; }
.tsBarTrack { height: 110px; width: 100%; display: flex; align-items: flex-end; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.tsBarFill { width: 100%; background: linear-gradient(180deg, var(--orange) 0%, #d97a28 100%); border-radius: 3px 3px 0 0; min-height: 2px; }
.tsBarLabel { font-size: 8px; color: rgba(255,255,255,0.45); white-space: nowrap; }

.searchDivider {''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: Audit page -- friendly labels for the Expenses actions
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/Audit/AuditPage.jsx",
        '''        if (action === 'NUCLEAR_PURGE')             return 'DELETE RECORD';
        return action;
    };''',
        '''        if (action === 'NUCLEAR_PURGE')             return 'DELETE RECORD';
        if (action === 'EXPENSE_LOGGED')            return 'EXPENSE LOGGED';
        if (action === 'EXPENSE_EDITED')            return 'EXPENSE CORRECTED';
        if (action === 'EXPENSE_DELETED')           return 'EXPENSE DELETED';
        if (action === 'EXPENSE_PRESET_CREATED')    return 'PRESET ADDED';
        return action;
    };''',
    ),
]


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            print("MISSING (file not found): " + rel_path)
            continue
        content = read_file(full_path)
        if new in content:
            print("SKIP (already patched): " + rel_path)
            continue
        if old not in content:
            print("MISSING (patch target not found -- is the Expenses rebuild fix.py applied?): " + rel_path)
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("OK: patched " + rel_path)

    print("")
    print("Done. Next steps:")
    print("1. git add -A && git commit -m 'Expenses analytics + autocomplete + audit labels' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Open Expenses as Director/Admin, tap ANALYSIS -- you should now see")
    print("   BY STAFF and SPENDING OVER TIME (with a DAY/WEEK/MONTH toggle) below")
    print("   the existing category breakdown.")
    print("4. Tap OTHER on the log form, or edit an existing entry, and start typing")
    print("   a category you've used before -- it should now autocomplete.")
    print("5. Check the Audit Log after logging/editing/deleting an expense or")
    print("   creating a preset -- the action should show a readable label, not")
    print("   a raw code like EXPENSE_LOGGED.")


if __name__ == "__main__":
    main()