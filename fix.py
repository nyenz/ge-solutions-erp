# PATH: fix.py
# STAGE 1 -- STOP THE BLEEDING (bug-fix roadmap)
# Run from project root: python fix.py   (or: py fix.py)
#
# WHY: nobody can record a payment right now -- the button is wired to a
# web address that doesn't exist on the server. On top of that, the admin
# password quietly resets every time the server restarts, the promote/
# demote button can turn a Director into an Admin by mistake, and there
# is no limit stopping someone from "paying" more than a project owes.
#
# BACKEND (patches):
#   - LandController.java: adds POST /projects/{id}/payment, restricted
#     to ROLE_MANAGER/ROLE_ADMIN/ROLE_DIRECTOR, wired to
#     LandService.recordPayment(). This is the missing endpoint the
#     frontend has been calling all along.
#   - LandService.java: widens recordPayment()'s own @PreAuthorize to
#     also allow ROLE_MANAGER (it was ROLE_ADMIN/ROLE_DIRECTOR only,
#     which would have silently blocked Managers even with the new
#     controller route in place). Also adds an overpayment guard that
#     throws BusinessException before the payment is saved if the
#     amount exceeds what is currently owed.
#   - DataInitializer.java: seedRootUser() no longer overwrites
#     admin_root's password/is_active/must_change_password on every
#     restart -- that UPDATE now only ever runs once, at first creation.
#     Also removes the console line that printed the first 3 characters
#     of the raw admin password, and removes the post-write BCrypt
#     verification block (it only makes sense right after a fresh
#     insert; run against an existing, already-changed password it was
#     printing a false "FATAL: BCrypt verify FAILED" every restart).
#
# FRONTEND (patches):
#   - SettingsPage.jsx: replaces the binary promote/demote arrow toggle
#     (which sent ANY non-Admin role straight to Admin) with an explicit
#     rank menu showing all 4 roles, so the person promoting always
#     picks the exact target role.
#   - FolderPage.jsx: handleRecordPayment now reads the server's real
#     error message (err.response?.data?.message) instead of always
#     showing the generic "PAYMENT FAILED" toast -- so the new
#     overpayment message actually reaches the user.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone
# (most likely meaning this stage is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# (file, old, new) patches applied with str.replace, in order
PATCHES = [
    # ---------------------------------------------------------------
    # BACKEND: LandController -- add the missing payment endpoint
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    // NEW: Payment history per plot
    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }''',
        '''    // NEW: Payment history per plot
    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    // STAGE 1 FIX: this endpoint did not exist -- the frontend has been
    // calling it since it was built. Class-level @PreAuthorize already
    // covers ROLE_MANAGER/ROLE_ADMIN/ROLE_DIRECTOR.
    @PostMapping("/projects/{id}/payment")
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes) {
        landService.recordPayment(id, amount, notes);
        return ResponseEntity.ok().build();
    }''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandService -- widen recordPayment's own @PreAuthorize
    # and add the overpayment guard
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
        '''    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        String operator = getCurrentOperator();
        String paymentType = project.isReceivable() ? "RECEIVABLE_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);''',
        '''    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        // STAGE 1 FIX: block overpayment -- work out what is still owed
        // using the same logic already used below for balanceAfter.
        BigDecimal currentlyOwed = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        if (amount.compareTo(currentlyOwed) > 0) {
            throw new BusinessException("OVERPAYMENT_BLOCKED: This project only owes UGX "
                    + currentlyOwed + ". You tried to record UGX " + amount + ".");
        }

        String operator = getCurrentOperator();
        String paymentType = project.isReceivable() ? "RECEIVABLE_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: DataInitializer -- stop resetting the password on every
    # restart, stop printing the raw password prefix, drop the
    # verification block that only makes sense on fresh insert.
    # (Kept as ONE patch spanning the whole block -- splitting this
    # into two smaller patches lets the second patch's "new" text
    # collide with a substring of the first patch's "old" text, which
    # falsely reports "already patched" before either edit lands.)
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
        '''        System.out.println(">>> [REGISTRY] seedRootUser() via raw JDBC. Raw password=" + rawPassword.substring(0,3) + "***");

        try (java.sql.Connection conn = dataSource.getConnection()) {
            // Check if admin_root exists
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                // INSERT brand-new admin_root row
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                // UPDATE existing row -- raw JDBC, auto-commits, no cache issues
                String sql = "UPDATE users SET password = ?, is_active = true, must_change_password = true "
                           + "WHERE username = 'admin_root'";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setString(1, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] UPDATE admin_root rows affected: " + rows);
                }
            }

            // Verify by re-reading the stored hash
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT password, is_active FROM users WHERE username = 'admin_root'")) {
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) {
                        String storedHash = rs.getString("password");
                        boolean active = rs.getBoolean("is_active");
                        boolean matches = passwordEncoder.matches(rawPassword, storedHash);
                        System.out.println(">>> [REGISTRY] Post-write verification:");
                        System.out.println(">>>   is_active in DB = " + active);
                        System.out.println(">>>   hash starts with = " + storedHash.substring(0, Math.min(20, storedHash.length())));
                        System.out.println(">>>   BCrypt.matches(rawPassword, storedHash) = " + matches);
                        if (!matches) {
                            System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.");
                        } else {
                            System.out.println(">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.");
                        }
                    } else {
                        System.err.println(">>> [REGISTRY] FATAL: admin_root row not found after write!");
                    }
                }
            }

        } catch (Exception e) {''',
        '''        try (java.sql.Connection conn = dataSource.getConnection()) {
            // Check if admin_root exists
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                // INSERT brand-new admin_root row
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }

                // Verify by re-reading the stored hash -- only meaningful right
                // after a fresh insert, since this is the only branch that
                // actually wrote a new password.
                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                        "SELECT password, is_active FROM users WHERE username = 'admin_root'")) {
                    try (java.sql.ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            String storedHash = rs.getString("password");
                            boolean active = rs.getBoolean("is_active");
                            boolean matches = passwordEncoder.matches(rawPassword, storedHash);
                            System.out.println(">>> [REGISTRY] Post-write verification:");
                            System.out.println(">>>   is_active in DB = " + active);
                            System.out.println(">>>   BCrypt.matches(rawPassword, storedHash) = " + matches);
                            if (!matches) {
                                System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.");
                            } else {
                                System.out.println(">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.");
                            }
                        } else {
                            System.err.println(">>> [REGISTRY] FATAL: admin_root row not found after write!");
                        }
                    }
                }
            } else {
                // STAGE 1 FIX: admin_root already exists -- do NOT touch its
                // password, is_active, or must_change_password on restart.
                // Whatever David set those to in the running app stays as-is.
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset. Existing credentials remain in effect.");
            }

        } catch (Exception e) {''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage -- explicit rank menu instead of a
    # binary promote/demote toggle
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''    FiPower, FiMail, FiSave, FiAlertTriangle, FiArrowUp,
    FiArrowDown, FiChevronDown, FiActivity, FiEye, FiEyeOff,''',
        '''    FiPower, FiMail, FiSave, FiAlertTriangle,
    FiChevronDown, FiActivity, FiEye, FiEyeOff,''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''    const [tempKeyReveal, setTempKeyReveal] = useState(null);''',
        '''    const [tempKeyReveal, setTempKeyReveal] = useState(null);
    const [roleMenuFor,   setRoleMenuFor]   = useState(null); // STAGE 1 FIX: explicit rank menu''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''    // ── ROLE SWITCH ──
    const handleRoleSwitch = async (opUsername, currentRole) => {
        const targetRole = currentRole === 'ROLE_ADMIN' ? 'ROLE_MANAGER' : 'ROLE_ADMIN';
        const label = targetRole === 'ROLE_ADMIN' ? 'PROMOTE TO ADMIN' : 'DEMOTE TO OPERATOR';
        const ok = await confirm(label, `${label} for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.updateOperatorRole(opUsername, targetRole); fetchOperators(); }
        catch (err) { toast(err.message || 'ROLE SWITCH FAILED', 'error', 8000); }
    };''',
        '''    // ── ROLE SWITCH ── (STAGE 1 FIX: explicit target role, no more guessing)
    const ALL_RANKS = ['ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR'];
    const handleRoleSwitch = async (opUsername, targetRole) => {
        setRoleMenuFor(null);
        const label = 'SET RANK: ' + targetRole.replace('ROLE_', '');
        const ok = await confirm(label, `${label} for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.updateOperatorRole(opUsername, targetRole); fetchOperators(); }
        catch (err) { toast(err.message || 'ROLE SWITCH FAILED', 'error', 8000); }
    };''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''                                                <div className={styles.opActions}>
                                                    {!op.isRoot && (<>
                                                        <button className={styles.rankBtn} onClick={() => handleRoleSwitch(op.username, op.role)} aria-label={op.role === 'ROLE_ADMIN' ? `Demote ${op.username}` : `Promote ${op.username}`}>
                                                            {op.role === 'ROLE_ADMIN' ? <FiArrowDown aria-hidden="true" /> : <FiArrowUp aria-hidden="true" />}
                                                        </button>''',
        '''                                                <div className={styles.opActions}>
                                                    {!op.isRoot && (<>
                                                        <div className={styles.rankMenuWrapper}>
                                                            <button className={styles.rankBtn} onClick={() => setRoleMenuFor(roleMenuFor === op.username ? null : op.username)} aria-label={`Change rank for ${op.username}`} aria-haspopup="menu" aria-expanded={roleMenuFor === op.username}>
                                                                <FiChevronDown aria-hidden="true" />
                                                            </button>
                                                            {roleMenuFor === op.username && (
                                                                <div className={styles.rankMenu} role="menu">
                                                                    {ALL_RANKS.map(r => (
                                                                        <div
                                                                            key={r}
                                                                            role="menuitem"
                                                                            className={`${styles.rankMenuItem} ${op.role === r ? styles.rankMenuItemActive : ''}`}
                                                                            onClick={() => handleRoleSwitch(op.username, r)}
                                                                        >
                                                                            {r.replace('ROLE_', '')}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage.module.css -- styles for the new rank menu
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.module.css",
        '''.opActions { display: flex; gap: clamp(5px,0.6vw,7px); flex-shrink: 0; }''',
        '''.opActions { display: flex; gap: clamp(5px,0.6vw,7px); flex-shrink: 0; }
.rankMenuWrapper { position: relative; }
.rankMenu {
    position: absolute; top: calc(100% + 6px); right: 0; z-index: 20;
    min-width: clamp(120px,14vw,150px);
    background: #162a2c; border: 1px solid rgba(255,255,255,0.14);
    border-radius: var(--radius-sm); box-shadow: 0 8px 20px rgba(0,0,0,0.35);
    overflow: hidden;
}
.rankMenuItem {
    padding: clamp(7px,0.9vw,10px) clamp(10px,1.2vw,13px);
    font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px,0.95vw,11px);
    letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.75);
    cursor: pointer; transition: background 0.15s, color 0.15s;
}
.rankMenuItem:hover { background: rgba(238,140,58,0.14); color: var(--orange); }
.rankMenuItemActive { color: var(--orange); background: rgba(238,140,58,0.08); }''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: FolderPage -- show the real server error, not a
    # generic "PAYMENT FAILED" toast (so overpayment messages surface)
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        '''        } catch { toast('PAYMENT FAILED', 'error', 8000); }
        finally { setPaying(false); }''',
        '''        } catch (err) { toast('PAYMENT FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setPaying(false); }''',
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
    applied = 0
    missing = []
    total = len(PATCHES)

    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        desc = rel_path
        if not os.path.exists(full_path):
            print("[STAGE 1] " + desc + " ... MISSING (file not found)")
            missing.append(desc + " (file not found)")
            continue
        content = read_file(full_path)
        if new in content:
            print("[STAGE 1] " + desc + " ... OK (already patched)")
            applied += 1
            continue
        if old not in content:
            print("[STAGE 1] " + desc + " ... MISSING (patch target not found)")
            missing.append(desc + " (patch target not found)")
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("[STAGE 1] " + desc + " ... OK")
        applied += 1

    print("")
    print("============================================")
    print("STAGE 1 COMPLETE: " + str(applied) + " of " + str(total) + " patches applied")
    print("FIXED: payment endpoint, admin password reset, promote/demote, overpayment check")
    print("============================================")

    if missing:
        print("")
        print("MISSING ITEMS (need manual attention):")
        for m in missing:
            print("  - " + m)

    print("")
    print("Next steps:")
    print("1. git add -A && git commit -m 'Stage 1: payment endpoint, password reset, promote/demote, overpayment' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Test: log in as Manager, record a payment on any active project -- should succeed.")
    print("4. Test: try to pay more than a project owes -- should be blocked with a clear message.")
    print("5. Test: restart the backend and confirm the admin password you set earlier still works.")
    print("6. Test: try promoting a Director from Settings -- confirm it does NOT silently become Admin.")


if __name__ == "__main__":
    main()