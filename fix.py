import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING: {label or path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")

# =================================================================
# 1. HARDWARE MODAL - FIX NUMBER INPUT ARROWS (NO BACKGROUND)
# =================================================================
patch(
    "erp-frontend/src/components/common/HardwareModal.module.css",
    """/* Custom Spinners for Number Inputs */
.modalInput[type="number"] {
    color-scheme: dark;
}
.modalInput[type="number"]::-webkit-inner-spin-button,
.modalInput[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    background-color: #162a2c;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23EE8C3A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='7,11 12,6 17,11' /%3E%3Cpolyline points='7,13 12,18 17,13' /%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    border-left: 1px solid rgba(238, 140, 58, 0.3);
    cursor: pointer;
    opacity: 0.85;
    transition: opacity 0.2s, background-color 0.2s;
}
.modalInput[type="number"]::-webkit-inner-spin-button:hover,
.modalInput[type="number"]::-webkit-outer-spin-button:hover {
    opacity: 1;
    background-color: #213e40;
}""",
    """/* Custom Spinners for Number Inputs */
.modalInput[type="number"] {
    color-scheme: dark;
}
.modalInput[type="number"]::-webkit-inner-spin-button,
.modalInput[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    background-color: transparent;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23EE8C3A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='7,11 12,6 17,11' /%3E%3Cpolyline points='7,13 12,18 17,13' /%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    border-left: 1px solid rgba(238, 140, 58, 0.3);
    cursor: pointer;
    opacity: 0.85;
    transition: opacity 0.2s, background-color 0.2s;
}
.modalInput[type="number"]::-webkit-inner-spin-button:hover,
.modalInput[type="number"]::-webkit-outer-spin-button:hover {
    opacity: 1;
    background-color: rgba(238, 140, 58, 0.1);
}""",
    "HardwareModal.module.css - Transparent orange arrows"
)

# =================================================================
# 2. AUDIT PAGE - SEARCH BAR FOCUS & PADDING
# =================================================================
patch(
    "erp-frontend/src/pages/Audit/AuditPage.jsx",
    """    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '' });
    const [operators,  setOperators]  = useState([]);""",
    """    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '' });
    const [operators,  setOperators]  = useState([]);
    const [isSearchFocused, setIsSearchFocused] = useState(false);""",
    "AuditPage.jsx - Add search focus state"
)

patch(
    "erp-frontend/src/pages/Audit/AuditPage.jsx",
    """                    <input
                        type="search"
                        placeholder="Investigate specific Plot ID, Name, or Keyword..."
                        className={`${styles.searchInput} ${filters.search ? styles.searchInputActive : ''}`}
                        value={filters.search}
                        onChange={e => setFilters({...filters, search: e.target.value})}
                        aria-label="Search forensic logs"
                    />
                    {!filters.search && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    """                    <input
                        type="search"
                        placeholder="Investigate specific Plot ID, Name, or Keyword..."
                        className={`${styles.searchInput} ${(filters.search || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={filters.search}
                        onChange={e => setFilters({...filters, search: e.target.value})}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)}
                        aria-label="Search forensic logs"
                    />
                    {!(filters.search || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    "AuditPage.jsx - Hide icon on focus"
)

patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    """.searchInput { width: 100%; border: none; outline: none; background: transparent; padding: 0 clamp(34px,4.5vw,42px); font-family: 'DM Sans', sans-serif; font-weight: 800; font-size: var(--fs-input); color: var(--navy); -webkit-appearance: none; appearance: none; transition: padding 0.2s ease; }
.searchInputActive { padding-left: clamp(12px,1.5vw,16px); }""",
    """.searchInput { width: 100%; border: none; outline: none; background: transparent; padding: 0 clamp(34px,4.5vw,42px) 0 clamp(42px,5vw,50px); font-family: 'DM Sans', sans-serif; font-weight: 800; font-size: var(--fs-input); color: var(--navy); -webkit-appearance: none; appearance: none; transition: padding 0.2s ease; }
.searchInputActive { padding-left: clamp(14px,1.5vw,18px) !important; }""",
    "AuditPage.module.css - Increase search left padding"
)

# =================================================================
# 3. LEDGER PAGE - SEARCH BAR FOCUS & PADDING
# =================================================================
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """    const [page,         setPage]         = useState(0);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');""",
    """    const [page,         setPage]         = useState(0);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [activeFilter, setActiveFilter] = useState('ALL');""",
    "LedgerPage.jsx - Add search focus state"
)

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                        <input
                            type="search" id="ledger-search"
                            placeholder="Plot ID, box, owner, phone, NIN, email, district, county, tenure..."
                            className={`${styles.searchInput} ${searchTerm ? styles.searchInputActive : ''}`}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            aria-label="Search ledger records"
                            autoComplete="off"
                        />
                        {!searchTerm && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    """                        <input
                            type="search" id="ledger-search"
                            placeholder="Plot ID, box, owner, phone, NIN, email, district, county, tenure..."
                            className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            onFocus={() => setIsSearchFocused(true)}
                            onBlur={() => setIsSearchFocused(false)}
                            aria-label="Search ledger records"
                            autoComplete="off"
                        />
                        {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    "LedgerPage.jsx - Hide icon on focus"
)

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """.searchInput {
    width: 100%;
    height: clamp(36px, 4.5vw, 44px);
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(32px, 4vw, 40px) 0 clamp(36px, 4.5vw, 46px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 800;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s, padding 0.2s ease;
    box-sizing: border-box;
    -webkit-appearance: none;
    appearance: none;
    line-height: clamp(36px, 4.5vw, 44px);
}
.searchInputActive {
    padding-left: clamp(12px, 1.5vw, 16px);
}""",
    """.searchInput {
    width: 100%;
    height: clamp(36px, 4.5vw, 44px);
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(32px, 4vw, 40px) 0 clamp(42px, 5vw, 50px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 800;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s, padding 0.2s ease;
    box-sizing: border-box;
    -webkit-appearance: none;
    appearance: none;
    line-height: clamp(36px, 4.5vw, 44px);
}
.searchInputActive {
    padding-left: clamp(14px, 1.5vw, 18px) !important;
}""",
    "LedgerPage.module.css - Increase search left padding"
)

# =================================================================
# 4. PAYMENTS PAGE - SEARCH BAR FOCUS & PADDING
# =================================================================
patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.jsx",
    """    const [loading,    setLoading]    = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [typeFilter, setTypeFilter] = useState('ALL');""",
    """    const [loading,    setLoading]    = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [typeFilter, setTypeFilter] = useState('ALL');""",
    "PaymentsPage.jsx - Add search focus state"
)

patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.jsx",
    """                <div className={styles.searchWrap}>
                    {!searchTerm && <FiSearch className={styles.searchIcon} />}
                    <input type="search" 
                        className={`${styles.searchInput} ${searchTerm ? styles.searchInputActive : ''}`}
                        placeholder="Search plot ID, owner name, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                    {searchTerm && (""",
    """                <div className={styles.searchWrap}>
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} />}
                    <input type="search" 
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                        placeholder="Search plot ID, owner name, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
                    {searchTerm && (""",
    "PaymentsPage.jsx - Hide icon on focus"
)

patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    """.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 36px 0 38px;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
    height: 100%;
    transition: padding 0.2s ease;
}
.searchInputActive {
    padding-left: 12px;
}""",
    """.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 36px 0 42px;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
    height: 100%;
    transition: padding 0.2s ease;
}
.searchInputActive {
    padding-left: 14px !important;
}""",
    "PaymentsPage.module.css - Increase search left padding"
)

# =================================================================
# 5. RECOVERY PAGE - SEARCH BAR FOCUS & PADDING
# =================================================================
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    """    const [expandedPhone, setExpandedPhone] = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });""",
    """    const [expandedPhone, setExpandedPhone] = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });""",
    "RecoveryPortal.jsx - Add search focus state"
)

patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    """            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search owner, phone, or plot ID..."
                        className={`${styles.searchInput} ${searchTerm ? styles.searchInputActive : ''}`} value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)} />
                    {!searchTerm && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    """            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search owner, phone, or plot ID..."
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`} value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}""",
    "RecoveryPortal.jsx - Hide icon on focus"
)

patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    """.searchInput { width:100%; border:none; outline:none; background:transparent; color:var(--navy); padding:0 34px 0 38px; font-family:'DM Sans',sans-serif; font-weight:800; font-size:clamp(11px,1.1vw,13px); transition: padding 0.2s ease; }
.searchInputActive { padding-left: 12px; }""",
    """.searchInput { width:100%; border:none; outline:none; background:transparent; color:var(--navy); padding:0 34px 0 42px; font-family:'DM Sans',sans-serif; font-weight:800; font-size:clamp(11px,1.1vw,13px); transition: padding 0.2s ease; }
.searchInputActive { padding-left: 14px !important; }""",
    "RecoveryPortal.module.css - Increase search left padding"
)

print("\n=== PRIORITY 1 POLISH: ARROWS AND SEARCH INPUTS FIXED ===")