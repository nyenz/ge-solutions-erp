import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def apply_patch(path, old, new, label):
    if not os.path.exists(path):
        print('MISSING (file not found): ' + label + ' -- ' + path)
        return
    content = read_file(path)
    if old in content:
        content = content.replace(old, new, 1)
        write_file(path, content)
        print('OK: ' + label)
    elif new in content:
        print('OK (already applied): ' + label)
    else:
        print('MISSING (patch target not found): ' + label + ' -- ' + path)

def write_full(path, content, label):
    write_file(path, content)
    print('OK (full rewrite): ' + label)


# =====================================================================
# PART 1 -- BACKEND: spentBy field (fixes "not everyone who enters the
# expense is who spent the money" logic gap)
# =====================================================================

EXPENSE_MODEL = 'erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/Expense.java'

apply_patch(
    EXPENSE_MODEL,
    '''    @Column(name = "recorded_by", length = 100)
    private String recordedBy;

    @Builder.Default''',
    '''    @Column(name = "recorded_by", length = 100)
    private String recordedBy;

    /**
     * Who the cash actually left the office with -- NOT necessarily the same
     * person as recordedBy. A secretary can log a fuel expense that was
     * actually spent by a field agent. Optional: if blank, the UI and every
     * analysis query fall back to recordedBy so old rows and same-person
     * entries behave exactly as before.
     */
    @Column(name = "spent_by", length = 100)
    private String spentBy;

    @Builder.Default''',
    'Expense.java -- add spentBy column'
)

EXPENSE_REPO = 'erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpenseRepository.java'

apply_patch(
    EXPENSE_REPO,
    '''    @Query("SELECT e FROM Expense e WHERE " +
           "(:from IS NULL OR e.createdAt >= :from) AND " +
           "(:to IS NULL OR e.createdAt <= :to) AND " +
           "(:category IS NULL OR e.category = :category) AND " +
           "(:recordedBy IS NULL OR LOWER(e.recordedBy) LIKE LOWER(CONCAT('%', :recordedBy, '%'))) AND " +
           "(:minAmount IS NULL OR e.amount >= :minAmount) AND " +
           "(:maxAmount IS NULL OR e.amount <= :maxAmount) " +
           "ORDER BY e.createdAt DESC")
    Page<Expense> search(
        @Param("from") LocalDateTime from,
        @Param("to") LocalDateTime to,
        @Param("category") String category,
        @Param("recordedBy") String recordedBy,
        @Param("minAmount") BigDecimal minAmount,
        @Param("maxAmount") BigDecimal maxAmount,
        Pageable pageable
    );''',
    '''    @Query("SELECT e FROM Expense e WHERE " +
           "(:from IS NULL OR e.createdAt >= :from) AND " +
           "(:to IS NULL OR e.createdAt <= :to) AND " +
           "(:category IS NULL OR e.category = :category) AND " +
           "(:recordedBy IS NULL OR LOWER(e.recordedBy) LIKE LOWER(CONCAT('%', :recordedBy, '%'))) AND " +
           "(:spentBy IS NULL OR LOWER(COALESCE(e.spentBy, e.recordedBy)) LIKE LOWER(CONCAT('%', :spentBy, '%'))) AND " +
           "(:minAmount IS NULL OR e.amount >= :minAmount) AND " +
           "(:maxAmount IS NULL OR e.amount <= :maxAmount) " +
           "ORDER BY e.createdAt DESC")
    Page<Expense> search(
        @Param("from") LocalDateTime from,
        @Param("to") LocalDateTime to,
        @Param("category") String category,
        @Param("recordedBy") String recordedBy,
        @Param("spentBy") String spentBy,
        @Param("minAmount") BigDecimal minAmount,
        @Param("maxAmount") BigDecimal maxAmount,
        Pageable pageable
    );''',
    'ExpenseRepository.java -- add spentBy to search query'
)

apply_patch(
    EXPENSE_REPO,
    '''    @Query("SELECT e.recordedBy, COALESCE(SUM(e.amount), 0) FROM Expense e " +
           "WHERE e.createdAt >= :from AND e.createdAt <= :to " +
           "GROUP BY e.recordedBy ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByStaffBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);''',
    '''    /**
     * Groups by who actually spent the cash (spentBy), falling back to
     * recordedBy when spentBy was never set -- this is what "BY STAFF"
     * on the Analysis panel is meant to answer, not "who typed this in".
     */
    @Query("SELECT COALESCE(e.spentBy, e.recordedBy), COALESCE(SUM(e.amount), 0) FROM Expense e " +
           "WHERE e.createdAt >= :from AND e.createdAt <= :to " +
           "GROUP BY COALESCE(e.spentBy, e.recordedBy) ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByStaffBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);''',
    'ExpenseRepository.java -- BY STAFF now groups by spentBy (falls back to recordedBy)'
)

EXPENSE_SERVICE = 'erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/ExpenseService.java'

apply_patch(
    EXPENSE_SERVICE,
    '''    @Transactional
    public Expense createExpense(String category, BigDecimal amount, String note) {
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        Expense expense = Expense.builder()
                .category(category.trim())
                .amount(amount)
                .note(note)
                .recordedBy(getCurrentOperator())
                .build();

        Expense saved = expenseRepository.save(expense);

        auditService.logAction("EXPENSE_LOGGED",
            "Operator [" + getCurrentOperator() + "] logged expense: " + category
            + " -- UGX " + amount);

        return saved;
    }''',
    '''    @Transactional
    public Expense createExpense(String category, BigDecimal amount, String note, String spentBy) {
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        String cleanSpentBy = (spentBy != null && !spentBy.isBlank()) ? spentBy.trim() : null;

        Expense expense = Expense.builder()
                .category(category.trim())
                .amount(amount)
                .note(note)
                .recordedBy(getCurrentOperator())
                .spentBy(cleanSpentBy)
                .build();

        Expense saved = expenseRepository.save(expense);

        auditService.logAction("EXPENSE_LOGGED",
            "Operator [" + getCurrentOperator() + "] logged expense: " + category
            + " -- UGX " + amount
            + (cleanSpentBy != null ? " (spent by " + cleanSpentBy + ")" : ""));

        return saved;
    }''',
    'ExpenseService.java -- createExpense accepts spentBy'
)

apply_patch(
    EXPENSE_SERVICE,
    '''    @Transactional
    public Expense editExpense(UUID id, String category, BigDecimal amount, String note) {
        Expense expense = expenseRepository.findById(id)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));

        if (!expense.isEditable()) {
            throw new BusinessException("EDIT_WINDOW_CLOSED: This expense is more than "
                + EDIT_WINDOW_HOURS + " hours old and can no longer be edited. Ask a Director to delete it if it's wrong.");
        }
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        String oldCategory = expense.getCategory();
        BigDecimal oldAmount = expense.getAmount();

        expense.setCategory(category.trim());
        expense.setAmount(amount);
        expense.setNote(note);
        expense.setEditedAt(LocalDateTime.now());
        expense.setEditedBy(getCurrentOperator());''',
    '''    @Transactional
    public Expense editExpense(UUID id, String category, BigDecimal amount, String note, String spentBy) {
        Expense expense = expenseRepository.findById(id)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));

        if (!expense.isEditable()) {
            throw new BusinessException("EDIT_WINDOW_CLOSED: This expense is more than "
                + EDIT_WINDOW_HOURS + " hours old and can no longer be edited. Ask a Director to delete it if it's wrong.");
        }
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        String oldCategory = expense.getCategory();
        BigDecimal oldAmount = expense.getAmount();

        expense.setCategory(category.trim());
        expense.setAmount(amount);
        expense.setNote(note);
        expense.setSpentBy((spentBy != null && !spentBy.isBlank()) ? spentBy.trim() : null);
        expense.setEditedAt(LocalDateTime.now());
        expense.setEditedBy(getCurrentOperator());''',
    'ExpenseService.java -- editExpense accepts spentBy'
)

apply_patch(
    EXPENSE_SERVICE,
    '''    public Page<Expense> search(LocalDateTime from, LocalDateTime to, String category,
                                 String recordedBy, BigDecimal minAmount, BigDecimal maxAmount,
                                 Pageable pageable) {
        return expenseRepository.search(from, to, category, recordedBy, minAmount, maxAmount, pageable);
    }''',
    '''    public Page<Expense> search(LocalDateTime from, LocalDateTime to, String category,
                                 String recordedBy, String spentBy, BigDecimal minAmount, BigDecimal maxAmount,
                                 Pageable pageable) {
        return expenseRepository.search(from, to, category, recordedBy, spentBy, minAmount, maxAmount, pageable);
    }''',
    'ExpenseService.java -- search() passes spentBy through'
)

EXPENSE_CONTROLLER = 'erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/ExpenseController.java'

apply_patch(
    EXPENSE_CONTROLLER,
    '''    @PostMapping
    public ResponseEntity<Expense> createExpense(@RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        return ResponseEntity.ok(expenseService.createExpense(category, amount, note));
    }''',
    '''    @PostMapping
    public ResponseEntity<Expense> createExpense(@RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        String spentBy = (String) body.get("spentBy");
        return ResponseEntity.ok(expenseService.createExpense(category, amount, note, spentBy));
    }''',
    'ExpenseController.java -- createExpense reads spentBy'
)

apply_patch(
    EXPENSE_CONTROLLER,
    '''    @PutMapping("/{id}")
    public ResponseEntity<Expense> editExpense(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        return ResponseEntity.ok(expenseService.editExpense(id, category, amount, note));
    }''',
    '''    @PutMapping("/{id}")
    public ResponseEntity<Expense> editExpense(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        String spentBy = (String) body.get("spentBy");
        return ResponseEntity.ok(expenseService.editExpense(id, category, amount, note, spentBy));
    }''',
    'ExpenseController.java -- editExpense reads spentBy'
)

apply_patch(
    EXPENSE_CONTROLLER,
    '''            @RequestParam(required = false) String category,
            @RequestParam(required = false) String recordedBy,
            @RequestParam(required = false) BigDecimal minAmount,
            @RequestParam(required = false) BigDecimal maxAmount,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {

        LocalDateTime fromDt = (from != null && !from.isBlank()) ? LocalDate.parse(from).atStartOfDay() : null;
        LocalDateTime toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : null;

        return ResponseEntity.ok(expenseService.search(
            fromDt, toDt, category, recordedBy, minAmount, maxAmount, PageRequest.of(page, size)
        ));''',
    '''            @RequestParam(required = false) String category,
            @RequestParam(required = false) String recordedBy,
            @RequestParam(required = false) String spentBy,
            @RequestParam(required = false) BigDecimal minAmount,
            @RequestParam(required = false) BigDecimal maxAmount,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {

        LocalDateTime fromDt = (from != null && !from.isBlank()) ? LocalDate.parse(from).atStartOfDay() : null;
        LocalDateTime toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : null;

        return ResponseEntity.ok(expenseService.search(
            fromDt, toDt, category, recordedBy, spentBy, minAmount, maxAmount, PageRequest.of(page, size)
        ));''',
    'ExpenseController.java -- search endpoint accepts spentBy'
)


# =====================================================================
# PART 2 -- FRONTEND SERVICE: pass spentBy through
# =====================================================================

EXPENSE_SVC_JS = 'erp-frontend/src/services/expenseService.js'

apply_patch(
    EXPENSE_SVC_JS,
    '''    create: async ({ category, amount, note }) => {
        const response = await api.post('/finance/expenses', { category, amount, note });
        return response.data;
    },''',
    '''    create: async ({ category, amount, note, spentBy }) => {
        const response = await api.post('/finance/expenses', { category, amount, note, spentBy });
        return response.data;
    },''',
    'expenseService.js -- create() sends spentBy'
)

apply_patch(
    EXPENSE_SVC_JS,
    '''    update: async (id, { category, amount, note }) => {
        const response = await api.put(`/finance/expenses/${id}`, { category, amount, note });
        return response.data;
    },''',
    '''    update: async (id, { category, amount, note, spentBy }) => {
        const response = await api.put(`/finance/expenses/${id}`, { category, amount, note, spentBy });
        return response.data;
    },''',
    'expenseService.js -- update() sends spentBy'
)


# =====================================================================
# PART 3 -- FRONTEND: ExpensesPage.jsx
# spentBy fields in Log/Edit modals, spentBy filter, themed category
# dropdown replacing the raw native <select>, spent-by tag in tables
# =====================================================================

EXPENSES_JSX = 'erp-frontend/src/pages/Financials/ExpensesPage.jsx'

apply_patch(
    EXPENSES_JSX,
    '''import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiBarChart2, FiX, FiSearch, FiClock
} from 'react-icons/fi';''',
    '''import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiBarChart2, FiX, FiSearch, FiClock, FiChevronDown
} from 'react-icons/fi';''',
    'ExpensesPage.jsx -- import useRef + FiChevronDown'
)

apply_patch(
    EXPENSES_JSX,
    '''    const [logCategory, setLogCategory] = useState('');
    const [logAmount, setLogAmount] = useState('');
    const [logNote, setLogNote] = useState('');
    const [logging, setLogging] = useState(false);

    const openLogModal = (presetName) => {
        setLogModal({ open: true, presetName, isOther: false });
        setLogCategory(presetName);
        setLogAmount('');
        setLogNote('');
    };
    const openOtherModal = () => {
        setLogModal({ open: true, presetName: '', isOther: true });
        setLogCategory('');
        setLogAmount('');
        setLogNote('');
    };
    const closeLogModal = () => setLogModal({ open: false, presetName: '', isOther: false });

    const submitLog = async () => {
        if (logModal.isOther && !logCategory.trim()) { flash('What is this expense for?', 'error'); return; }
        if (!logAmount || Number(logAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
        setLogging(true);
        try {
            await expenseService.create({
                category: (logModal.isOther ? logCategory : logModal.presetName).trim(),
                amount: Number(logAmount),
                note: logNote,
            });''',
    '''    const [logCategory, setLogCategory] = useState('');
    const [logAmount, setLogAmount] = useState('');
    const [logNote, setLogNote] = useState('');
    const [logSpentBy, setLogSpentBy] = useState('');
    const [logging, setLogging] = useState(false);

    const openLogModal = (presetName) => {
        setLogModal({ open: true, presetName, isOther: false });
        setLogCategory(presetName);
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const openOtherModal = () => {
        setLogModal({ open: true, presetName: '', isOther: true });
        setLogCategory('');
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const closeLogModal = () => setLogModal({ open: false, presetName: '', isOther: false });

    const submitLog = async () => {
        if (logModal.isOther && !logCategory.trim()) { flash('What is this expense for?', 'error'); return; }
        if (!logAmount || Number(logAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
        setLogging(true);
        try {
            await expenseService.create({
                category: (logModal.isOther ? logCategory : logModal.presetName).trim(),
                amount: Number(logAmount),
                note: logNote,
                spentBy: logSpentBy,
            });''',
    'ExpensesPage.jsx -- logSpentBy state + wiring'
)

apply_patch(
    EXPENSES_JSX,
    '''    const [editCategory, setEditCategory] = useState('');
    const [editAmount, setEditAmount] = useState('');
    const [editNote, setEditNote] = useState('');
    const [saving, setSaving] = useState(false);

    const openEdit = (expense) => {
        setEditModal({ open: true, expense });
        setEditCategory(expense.category);
        setEditAmount(String(expense.amount));
        setEditNote(expense.note || '');
    };

    const submitEdit = async () => {
        if (!editAmount || Number(editAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
        setSaving(true);
        try {
            await expenseService.update(editModal.expense.id, {
                category: editCategory.trim(),
                amount: Number(editAmount),
                note: editNote,
            });''',
    '''    const [editCategory, setEditCategory] = useState('');
    const [editAmount, setEditAmount] = useState('');
    const [editNote, setEditNote] = useState('');
    const [editSpentBy, setEditSpentBy] = useState('');
    const [saving, setSaving] = useState(false);

    const openEdit = (expense) => {
        setEditModal({ open: true, expense });
        setEditCategory(expense.category);
        setEditAmount(String(expense.amount));
        setEditNote(expense.note || '');
        setEditSpentBy(expense.spentBy || '');
    };

    const submitEdit = async () => {
        if (!editAmount || Number(editAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
        setSaving(true);
        try {
            await expenseService.update(editModal.expense.id, {
                category: editCategory.trim(),
                amount: Number(editAmount),
                note: editNote,
                spentBy: editSpentBy,
            });''',
    'ExpensesPage.jsx -- editSpentBy state + wiring'
)

apply_patch(
    EXPENSES_JSX,
    '''    const [filters, setFilters] = useState({ from: '', to: '', category: '', recordedBy: '', minAmount: '', maxAmount: '' });''',
    '''    const [filters, setFilters] = useState({ from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' });''',
    'ExpensesPage.jsx -- filters state gets spentBy'
)

apply_patch(
    EXPENSES_JSX,
    '''    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);''',
    '''    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    const [categoryDropdownOpen, setCategoryDropdownOpen] = useState(false);
    const categoryDropdownRef = useRef(null);
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (categoryDropdownRef.current && !categoryDropdownRef.current.contains(e.target)) {
                setCategoryDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);''',
    'ExpensesPage.jsx -- category dropdown state + outside-click handler'
)

apply_patch(
    EXPENSES_JSX,
    '''        setFilters({ from: '', to: '', category: '', recordedBy: '', minAmount: '', maxAmount: '' });
        setSearchResults(null);''',
    '''        setFilters({ from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' });
        setSearchResults(null);''',
    'ExpensesPage.jsx -- clearSearch resets spentBy'
)

apply_patch(
    EXPENSES_JSX,
    '''                        <div className={styles.sectionLabel}>BY STAFF</div>''',
    '''                        <div className={styles.sectionLabel}>BY STAFF (WHO SPENT IT)</div>''',
    'ExpensesPage.jsx -- relabel BY STAFF section'
)

apply_patch(
    EXPENSES_JSX,
    '''                                            <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                            <td className={styles.metaCell}>{e.recordedBy}</td>
                                            <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            <td>
                                                <div className={styles.rowActions}>
                                                    {editable ? (''',
    '''                                            <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                            <td className={styles.metaCell}>
                                                {e.recordedBy}
                                                {e.spentBy && e.spentBy !== e.recordedBy && (
                                                    <span className={styles.spentByTag}>SPENT: {e.spentBy}</span>
                                                )}
                                            </td>
                                            <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            <td>
                                                <div className={styles.rowActions}>
                                                    {editable ? (''',
    'ExpensesPage.jsx -- show SPENT BY tag in recent-entries table'
)

apply_patch(
    EXPENSES_JSX,
    '''                                        <tr>
                                            <th>DATE</th>
                                            <th>CATEGORY</th>
                                            <th>AMOUNT</th>
                                            <th>LOGGED BY</th>
                                            <th>NOTE</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {searchResults.length === 0 ? (
                                            <tr><td colSpan="5" className={styles.emptyCell}>NO RESULTS</td></tr>
                                        ) : searchResults.map(e => (
                                            <tr key={e.id}>
                                                <td className={styles.dateCell}>{new Date(e.createdAt).toLocaleDateString()}</td>
                                                <td><span className={styles.categoryTag}>{e.category}</span></td>
                                                <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                                <td className={styles.metaCell}>{e.recordedBy}</td>
                                                <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            </tr>
                                        ))}''',
    '''                                        <tr>
                                            <th>DATE</th>
                                            <th>CATEGORY</th>
                                            <th>AMOUNT</th>
                                            <th>LOGGED BY</th>
                                            <th>SPENT BY</th>
                                            <th>NOTE</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {searchResults.length === 0 ? (
                                            <tr><td colSpan="6" className={styles.emptyCell}>NO RESULTS</td></tr>
                                        ) : searchResults.map(e => (
                                            <tr key={e.id}>
                                                <td className={styles.dateCell}>{new Date(e.createdAt).toLocaleDateString()}</td>
                                                <td><span className={styles.categoryTag}>{e.category}</span></td>
                                                <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                                <td className={styles.metaCell}>{e.recordedBy}</td>
                                                <td className={styles.metaCell}>{e.spentBy || e.recordedBy}</td>
                                                <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            </tr>
                                        ))}''',
    'ExpensesPage.jsx -- SPENT BY column in search results'
)

apply_patch(
    EXPENSES_JSX,
    '''                            <select className={styles.filterInput} value={filters.category}
                                onChange={e => setFilters({ ...filters, category: e.target.value })}>
                                <option value="">ALL CATEGORIES</option>
                                {presets.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
                            </select>
                            <input type="text" className={styles.filterInput} placeholder="Logged by..."
                                value={filters.recordedBy} onChange={e => setFilters({ ...filters, recordedBy: e.target.value })} />
                            <input type="number" className={styles.filterInput} placeholder="Min UGX"''',
    '''                            <div className={styles.categoryDropdown} ref={categoryDropdownRef}>
                                <button
                                    type="button"
                                    className={styles.categoryDropdownBtn}
                                    onClick={() => setCategoryDropdownOpen(o => !o)}
                                >
                                    <span>{filters.category || 'ALL CATEGORIES'}</span>
                                    <FiChevronDown className={categoryDropdownOpen ? styles.categoryDropdownIconOpen : ''} />
                                </button>
                                {categoryDropdownOpen && (
                                    <div className={styles.categoryDropdownList}>
                                        <div
                                            className={`${styles.categoryDropdownOption} ${!filters.category ? styles.categoryDropdownOptionActive : ''}`}
                                            onClick={() => { setFilters({ ...filters, category: '' }); setCategoryDropdownOpen(false); }}
                                        >
                                            ALL CATEGORIES
                                        </div>
                                        {presets.map(p => (
                                            <div
                                                key={p.id}
                                                className={`${styles.categoryDropdownOption} ${filters.category === p.name ? styles.categoryDropdownOptionActive : ''}`}
                                                onClick={() => { setFilters({ ...filters, category: p.name }); setCategoryDropdownOpen(false); }}
                                            >
                                                {p.name}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <input type="text" className={styles.filterInput} placeholder="Logged by..."
                                value={filters.recordedBy} onChange={e => setFilters({ ...filters, recordedBy: e.target.value })} />
                            <input type="text" className={styles.filterInput} placeholder="Spent by..."
                                value={filters.spentBy} onChange={e => setFilters({ ...filters, spentBy: e.target.value })} />
                            <input type="number" className={styles.filterInput} placeholder="Min UGX"''',
    'ExpensesPage.jsx -- themed category dropdown replaces native select + spentBy filter'
)

apply_patch(
    EXPENSES_JSX,
    '''                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Any extra detail..."
                        value={logNote}
                        onChange={e => setLogNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeLogModal}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitLog} loading={logging} icon={FiPlus}>
                        SAVE EXPENSE
                    </HardwareButton>
                </div>
            </HardwareModal>''',
    '''                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Any extra detail..."
                        value={logNote}
                        onChange={e => setLogNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT YOU)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to you"
                        value={logSpentBy}
                        onChange={e => setLogSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeLogModal}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitLog} loading={logging} icon={FiPlus}>
                        SAVE EXPENSE
                    </HardwareButton>
                </div>
            </HardwareModal>''',
    'ExpensesPage.jsx -- WHO ACTUALLY SPENT THIS field in Log modal'
)

apply_patch(
    EXPENSES_JSX,
    '''                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        value={editNote}
                        onChange={e => setEditNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setEditModal({ open: false, expense: null })}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitEdit} loading={saving} icon={FiEdit2}>
                        SAVE CHANGES
                    </HardwareButton>
                </div>
            </HardwareModal>''',
    '''                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        value={editNote}
                        onChange={e => setEditNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT THE LOGGER)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to whoever logged it"
                        value={editSpentBy}
                        onChange={e => setEditSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setEditModal({ open: false, expense: null })}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitEdit} loading={saving} icon={FiEdit2}>
                        SAVE CHANGES
                    </HardwareButton>
                </div>
            </HardwareModal>''',
    'ExpensesPage.jsx -- WHO ACTUALLY SPENT THIS field in Edit modal'
)


# =====================================================================
# PART 4 -- FRONTEND: ExpensesPage.module.css FULL REWRITE
# Table/header now match LedgerPage exactly (dark header bar, orange
# uppercase labels, 3px orange bottom border, orange left-border on row
# hover). Period/bucket buttons now use the app's CONFIRMED STANDARD
# filter-button spec instead of the old ad-hoc orange pill. New themed
# category dropdown (Intake-style look, compact filter-row sizing).
# spentByTag class added. Duplicate select.filterInput blocks removed
# since the native select is gone.
# =====================================================================

EXPENSES_CSS_PATH = 'erp-frontend/src/pages/Financials/ExpensesPage.module.css'

EXPENSES_CSS_CONTENT = """/* PATH: erp-frontend/src/pages/Financials/ExpensesPage.module.css */
/* Table/header/filter-button styling intentionally mirrors LedgerPage.module.css
   (the confirmed master reference) -- same tokens, same table treatment, same
   filter-button spec. Spacing here stays compact for this page's denser layout;
   only the visual language (colors, weights, borders, radii) is copied. */

.container {
    --orange:        #EE8C3A;
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --red:           #ef4444;
    --green:         #10b981;
    --amber:         #f59e0b;

    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:  clamp(18px, 2.5vw, 24px);
    --fs-sub: clamp(8px,  0.85vw, 10px);
    --fs-th:  clamp(8px,  0.85vw, 10px);
    --fs-td:  clamp(10px, 1.05vw, 12px);
    --fs-tag: clamp(7px,  0.75vw, 9px);

    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(24px, 3vw, 36px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 24px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; margin: 0; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1; }
.subtitle { color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

.headerActions { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }
.refreshBtn, .analysisBtn, .analysisBtnActive {
    display: flex; align-items: center; gap: 6px;
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(12px, 1.5vw, 16px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.2s;
}
.refreshBtn { background: rgba(26,46,48,0.08); border: 1.5px solid rgba(26,46,48,0.2); color: #1a2e30; }
.refreshBtn:hover { background: var(--orange); color: #fff; border-color: var(--orange); }
.analysisBtn { background: rgba(26,46,48,0.08); border: 1.5px solid rgba(26,46,48,0.2); color: #1a2e30; }
.analysisBtn:hover { background: rgba(26,46,48,0.16); }
.analysisBtnActive { background: var(--navy); border: 1.5px solid var(--navy); color: #fff; box-shadow: 0 3px 10px rgba(26,46,48,0.3); }

.flashBanner {
    padding: 10px 16px;
    border-radius: var(--radius-sm);
    font-weight: 800;
    font-size: 12px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.flash_success { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.flash_error   { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.flash_warn    { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.flash_info    { background: rgba(255,255,255,0.1); color: #fff;    border: 1px solid rgba(255,255,255,0.2); }

.panelSpacer { margin-top: clamp(14px, 2vw, 20px); }

/* -- PRESET GRID --------------------------------------------------- */
.presetGrid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: clamp(10px, 1.4vw, 14px);
}
.presetTile, .presetTileOther, .presetTileNew {
    height: clamp(64px, 8vw, 84px);
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(11px, 1.1vw, 13px);
    letter-spacing: 0.5px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    text-align: center;
    padding: 8px;
    transition: transform 0.15s, box-shadow 0.15s;
}
.presetTile {
    background: linear-gradient(160deg, var(--orange) 0%, #d97a28 100%);
    color: #fff;
    border: none;
    box-shadow: 0 4px 12px rgba(238,140,58,0.35);
}
.presetTile:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(238,140,58,0.5); }
.presetTileOther {
    background: rgba(26,46,48,0.85);
    color: #fff;
    border: 1.5px dashed rgba(255,255,255,0.3);
}
.presetTileOther:hover { background: rgba(26,46,48,1); }
.presetTileNew {
    background: transparent;
    color: var(--orange);
    border: 1.5px dashed var(--orange-border);
}
.presetTileNew:hover { background: rgba(238,140,58,0.08); border-color: var(--orange); }

/* -- AMOUNT INPUT (triggers native numeric keypad on mobile) ------ */
.amountInput {
    width: 100%;
    height: 56px;
    font-size: 28px;
    font-weight: 900;
    text-align: center;
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.25);
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    box-sizing: border-box;
}
.amountInput:focus { outline: none; border-color: var(--orange); }

/* -- TABLE (recent entries + search results) -----------------------
   Matches LedgerPage's table exactly: dark header bar, orange uppercase
   labels, 3px orange bottom border, orange left-border on row hover. --- */
.tableWrap { overflow-x: auto; margin-top: 10px; border-radius: var(--radius-sm); background: rgba(0,0,0,0.15); }
.table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: var(--fs-td); min-width: 640px; }
.table thead th {
    background: #162a2c;
    text-align: left;
    padding: clamp(9px, 1.2vw, 13px) clamp(10px, 1.5vw, 16px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    letter-spacing: 2px;
    color: var(--orange);
    text-transform: uppercase;
    border-bottom: 3px solid var(--orange);
    white-space: nowrap;
}
.table tbody tr {
    border-left: 3px solid transparent;
    transition: background 0.18s, border-left-color 0.18s;
}
.table tbody tr:hover {
    background: rgba(255, 255, 255, 0.04);
    border-left-color: var(--orange);
}
.table tbody td {
    padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.5vw, 16px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    vertical-align: middle;
}
.dateCell { white-space: nowrap; color: rgba(255,255,255,0.6); font-size: 11px; }
.moneyCell { font-weight: 900; white-space: nowrap; }
.metaCell { color: rgba(255,255,255,0.7); white-space: nowrap; }
.notesCell { color: rgba(255,255,255,0.55); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.emptyCell {
    text-align: center;
    padding: clamp(20px, 4vw, 40px) 16px;
    font-family: 'Space Mono', monospace;
    color: rgba(255,255,255,0.3);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.categoryTag {
    display: inline-block;
    background: rgba(238,140,58,0.15);
    color: var(--orange);
    border: 1px solid rgba(238,140,58,0.3);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}
.editedBadge {
    display: inline-block;
    margin-left: 6px;
    background: rgba(245,158,11,0.15);
    color: var(--amber);
    border: 1px solid rgba(245,158,11,0.3);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 0.4px;
}
/* Shown next to LOGGED BY when spentBy differs from recordedBy --
   this is the "who actually spent the cash" fix. */
.spentByTag {
    display: block;
    margin-top: 3px;
    color: rgba(255,255,255,0.4);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    white-space: normal;
}
.lockedTag {
    color: rgba(255,255,255,0.35);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.rowActions { display: flex; align-items: center; gap: 6px; }
.editIconBtn, .deleteIconBtn {
    width: 26px; height: 26px;
    border-radius: 5px;
    border: none;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    transition: background 0.15s;
}
.editIconBtn { background: rgba(59,130,246,0.15); color: #3b82f6; }
.editIconBtn:hover { background: rgba(59,130,246,0.3); }
.deleteIconBtn { background: rgba(239,68,68,0.15); color: var(--red); }
.deleteIconBtn:hover { background: rgba(239,68,68,0.3); }

/* -- DIRECTOR ANALYSIS ----------------------------------------------
   Period / bucket toggles now use the app's CONFIRMED STANDARD filter-
   button spec (rectangular, radius-sm, exact dark/hover/active colors)
   instead of the old ad-hoc orange pill. ---------------------------- */
.periodRow { display: flex; gap: clamp(6px, 1vw, 10px); flex-wrap: wrap; margin-bottom: 14px; }
.periodBtn, .periodBtnActive,
.bucketBtn, .bucketBtnActive {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
}
.periodBtn:hover, .bucketBtn:hover {
    background: rgba(238, 140, 58, 0.12);
    color: #EE8C3A;
    border-color: #EE8C3A;
}
.periodBtnActive, .bucketBtnActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.4);
}

.totalBox {
    background: rgba(0,0,0,0.2);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.totalBox label { font-size: 10px; font-weight: 800; letter-spacing: 0.8px; color: rgba(255,255,255,0.5); text-transform: uppercase; }
.totalBox strong { font-size: 24px; font-weight: 900; color: #fff; }

.categoryBars { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.barRow { display: grid; grid-template-columns: 110px 1fr 110px; align-items: center; gap: 10px; }
.barLabel { font-size: 11px; font-weight: 800; color: rgba(255,255,255,0.8); text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.barTrack { height: 14px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; }
.barFill { height: 100%; background: linear-gradient(90deg, var(--orange) 0%, #d97a28 100%); border-radius: 999px; transition: width 0.4s ease; }
.barValue { font-size: 11px; font-weight: 800; text-align: right; color: rgba(255,255,255,0.7); }

.sectionLabel {
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--orange);
    text-transform: uppercase;
    margin: 18px 0 10px;
}

.bucketRow { display: flex; gap: clamp(6px, 1vw, 10px); flex-wrap: wrap; margin-bottom: 12px; }

.tsChart { display: flex; gap: 6px; overflow-x: auto; padding: 4px 4px 0; align-items: flex-end; min-height: 140px; }
.tsBarWrap { display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; width: 32px; }
.tsBarTrack { height: 110px; width: 100%; display: flex; align-items: flex-end; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.tsBarFill { width: 100%; background: linear-gradient(180deg, var(--orange) 0%, #d97a28 100%); border-radius: 3px 3px 0 0; min-height: 2px; }
.tsBarLabel { font-size: 8px; color: rgba(255,255,255,0.45); white-space: nowrap; }

.searchDivider {
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--orange);
    text-transform: uppercase;
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 14px;
    margin-bottom: 10px;
}
.filterRow { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filterInput {
    height: 36px;
    padding: 0 10px;
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.2);
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    min-width: 120px;
}
.filterInput:focus { outline: none; border-color: var(--orange); }

/* -- CATEGORY DROPDOWN (filter row) ----------------------------------
   Same visual language as the Intake page's themed dropdown (white
   panel, orange border/accents, orange-filled hover, left-border-marked
   selected row) but sized to sit flush in this compact filter row --
   height/font intentionally match .filterInput, not Intake's spacing. */
.categoryDropdown {
    position: relative;
    flex: 1 1 160px;
    min-width: 120px;
}
.categoryDropdownBtn {
    width: 100%;
    height: 36px;
    padding: 0 10px;
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.2);
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    text-align: left;
    text-transform: uppercase;
    transition: border-color 0.2s;
}
.categoryDropdownBtn span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.categoryDropdownBtn:hover { border-color: var(--orange); }
.categoryDropdownBtn svg { color: var(--orange); flex-shrink: 0; transition: transform 0.2s; }
.categoryDropdownIconOpen { transform: rotate(180deg); }

.categoryDropdownList {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: var(--radius-sm);
    box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 8px 20px rgba(0,0,0,0.25);
    overflow: hidden;
    max-height: 220px;
    overflow-y: auto;
    z-index: 300;
    scrollbar-width: none;
}
.categoryDropdownList::-webkit-scrollbar { display: none; }
.categoryDropdownOption {
    padding: 9px 12px;
    color: var(--navy);
    font-size: 12px;
    font-weight: 700;
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.15s, color 0.15s;
}
.categoryDropdownOption:last-child { border-bottom: none; }
.categoryDropdownOption:hover { background: var(--orange); color: #fff; }
.categoryDropdownOptionActive { background: #f1f5f9; border-left: 4px solid var(--orange); }

.searchBtn, .clearBtn {
    display: flex; align-items: center; gap: 6px;
    height: 36px;
    padding: 0 14px;
    border-radius: var(--radius-sm);
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 0.6px;
    cursor: pointer;
    border: none;
}
.searchBtn { background: var(--orange); color: #fff; }
.searchBtn:hover { background: #d97a28; }
.searchBtn:disabled { opacity: 0.5; cursor: not-allowed; }
.clearBtn { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.8); }
.clearBtn:hover { background: rgba(255,255,255,0.18); }

/* -- RESPONSIVE ------------------------------------------------------ */
@media (max-width: 768px) {
    .table { min-width: 560px; }
    .barRow { grid-template-columns: 80px 1fr 80px; }
}
@media (max-width: 480px) {
    .presetGrid { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); }
    .table thead th { padding: 8px; font-size: 8px; }
    .table tbody td { padding: 7px 8px; }
    .categoryDropdown { flex: 1 1 100%; }
}
"""

write_full(EXPENSES_CSS_PATH, EXPENSES_CSS_CONTENT, 'ExpensesPage.module.css -- full rewrite (Ledger-matched table + dropdown + filter buttons)')


# =====================================================================
# PART 5 -- GLOBAL: themed number-input spinners app-wide
# Fixes the unstyled browser-default up/down arrows everywhere in the
# app (Expenses amount/min/max fields, FolderPage cost fields, Intake
# cost fields, etc.) in one place instead of patching every page.
# =====================================================================

INDEX_CSS = 'erp-frontend/src/index.css'

apply_patch(
    INDEX_CSS,
    '''/* --- THE HARDWARE SCROLLBAR (Rule 2) --- */''',
    '''/* ===== GLOBAL NUMBER INPUT SPINNER THEME =====
   "NO BROWSER DEFAULT STYLING" rule: every type="number" input in the app
   gets these themed up/down arrows by default, so nobody has to remember
   to add this per-page. Anything more specifically styled (e.g. the
   .modalInput rules in HardwareModal.module.css) simply wins on
   specificity and overrides this, so this is safe to apply everywhere.
   ============================================================= */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    appearance: none;
    width: 22px;
    margin: 0;
    background-color: transparent;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23EE8C3A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='7,11 12,6 17,11' /%3E%3Cpolyline points='7,13 12,18 17,13' /%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    background-size: 16px;
    border-left: 1px solid rgba(238, 140, 58, 0.3);
    cursor: pointer;
    opacity: 0.85;
    transition: opacity 0.2s, background-color 0.2s;
}
input[type="number"]::-webkit-inner-spin-button:hover,
input[type="number"]::-webkit-outer-spin-button:hover {
    opacity: 1;
    background-color: rgba(238, 140, 58, 0.1);
}
input[type="number"] {
    -moz-appearance: textfield;
}

/* --- THE HARDWARE SCROLLBAR (Rule 2) --- */''',
    'index.css -- global themed number-input spinner arrows'
)

print('')
print('DONE. Check every line above for MISSING before committing.')