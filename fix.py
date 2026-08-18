# PATH: fix.py
# DANGER ZONE: FULL SYSTEM DATA WIPE
# Run from project root: python fix.py   (or: py fix.py)
#
# WHAT THIS DOES:
# Adds a "Wipe All Data" feature, root-founder only:
#   1. New backend endpoint: POST /api/v1/admin/system/wipe-all-data
#      (erp-backend/.../modules/admin/controller/SystemAdminController.java)
#      - Root-only (same @PreAuthorize gate as StaffController).
#      - Requires ?confirm=WIPE-EVERYTHING or it does nothing.
#      - TRUNCATEs every business/user table (clients, land_projects,
#        land_titles, project_stages, payment_schedules, payment_records,
#        follow_up_logs, project_documents, company_expenses,
#        stage_templates, notifications, audit_logs, users).
#      - Immediately reseeds: the admin_root login (via the existing
#        DataInitializer.seedRootUser()), the project_index_counter
#        (back to 000/A), and the default stage template checklist.
#        Nobody gets permanently locked out.
#   2. New frontend Settings > DANGER ZONE panel (root only): type
#      WIPE-EVERYTHING to unlock a big red WIPE ALL DATA button, which
#      then asks for a final confirm popup before calling the endpoint.
#
# WHAT IT DOES NOT DO:
# Does NOT delete files already uploaded to Cloudinary -- those become
# orphaned and must be cleared separately in the Cloudinary dashboard
# if you want them gone too.
#
# AFTER RUNNING THIS + DEPLOY:
# 1. Log in as usual (Golden Seed / David).
# 2. Go to Settings, scroll to the DANGER ZONE panel at the bottom.
# 3. Type WIPE-EVERYTHING exactly into the box, click WIPE ALL DATA,
#    confirm the popup.
# 4. You get logged out. Log back in with your ADMIN_EMAIL /
#    ADMIN_DEFAULT_PASSWORD (the reseed uses those, not your last
#    custom password) and change the password again from Settings.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

NEW_CONTROLLER_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java"
NEW_CONTROLLER_CONTENT = '// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java\npackage com.gesolutions.erp.modules.admin.controller;\n\nimport com.gesolutions.erp.config.DataInitializer;\nimport com.gesolutions.erp.modules.land.service.StageTemplateService;\nimport lombok.RequiredArgsConstructor;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.security.access.prepost.PreAuthorize;\nimport org.springframework.web.bind.annotation.PostMapping;\nimport org.springframework.web.bind.annotation.RequestMapping;\nimport org.springframework.web.bind.annotation.RequestParam;\nimport org.springframework.web.bind.annotation.RestController;\n\nimport javax.sql.DataSource;\nimport java.sql.Connection;\nimport java.sql.Statement;\nimport java.util.LinkedHashMap;\nimport java.util.Map;\n\n/**\n * NYENZ ERP - SYSTEM RESET CONTROLLER\n *\n * Physically wipes every business record in the database and restores the\n * app to a fresh, empty state. SECURITY PROTOCOL: Root Founder only -- this\n * is the single most destructive endpoint in the system.\n *\n * After the wipe, the root admin account, the project index counter, and\n * the default stage-template checklist are automatically reseeded so the\n * app is immediately usable again (nobody gets permanently locked out).\n *\n * NOTE: This does NOT delete files already uploaded to Cloudinary. Any\n * documents attached to wiped projects become orphaned there -- clean those\n * up separately in the Cloudinary dashboard if needed.\n */\n@RestController\n@RequestMapping("/api/v1/admin/system")\n@RequiredArgsConstructor\n@PreAuthorize("hasRole(\'ROLE_ADMIN\') and authentication.principal.isRoot")\npublic class SystemAdminController {\n\n    private static final String CONFIRM_PHRASE = "WIPE-EVERYTHING";\n\n    // Every table that holds real business/user data. TRUNCATE ... CASCADE\n    // resolves foreign-key order automatically, so list order doesn\'t matter.\n    private static final String[] TABLES_TO_WIPE = {\n        "audit_logs",\n        "notifications",\n        "payment_records",\n        "payment_schedules",\n        "follow_up_logs",\n        "project_documents",\n        "project_stages",\n        "land_titles",\n        "land_projects",\n        "clients",\n        "company_expenses",\n        "stage_templates",\n        "users"\n    };\n\n    private final DataSource dataSource;\n    private final DataInitializer dataInitializer;\n    private final StageTemplateService stageTemplateService;\n\n    /**\n     * THE BIG RED BUTTON.\n     * Wipes every table above, then immediately reseeds the root admin\n     * account, the project index counter, and the default stage template\n     * so the system is left clean, working, and empty.\n     *\n     * Requires ?confirm=WIPE-EVERYTHING exactly, so this can never fire by\n     * accident (typo, stray request, browser prefetch, etc).\n     */\n    @PostMapping("/wipe-all-data")\n    public ResponseEntity<Map<String, Object>> wipeAllData(@RequestParam(required = false) String confirm) {\n        if (!CONFIRM_PHRASE.equals(confirm)) {\n            return ResponseEntity.badRequest().body(Map.of(\n                "wiped", false,\n                "message", "Confirmation phrase missing or incorrect. Send confirm=" + CONFIRM_PHRASE + " to proceed."\n            ));\n        }\n\n        System.out.println(">>> [WIPE] ================================================");\n        System.out.println(">>> [WIPE] FULL SYSTEM DATA WIPE TRIGGERED BY ROOT FOUNDER.");\n        System.out.println(">>> [WIPE] ================================================");\n\n        String tableList = String.join(", ", TABLES_TO_WIPE);\n        try (Connection conn = dataSource.getConnection();\n             Statement stmt = conn.createStatement()) {\n            stmt.execute("TRUNCATE TABLE " + tableList + " RESTART IDENTITY CASCADE");\n            System.out.println(">>> [WIPE] OK: All business tables truncated -- " + tableList);\n        } catch (Exception e) {\n            System.err.println(">>> [WIPE] FATAL: Truncate failed: " + e.getMessage());\n            return ResponseEntity.internalServerError().body(Map.of(\n                "wiped", false,\n                "message", "Wipe failed: " + e.getMessage()\n            ));\n        }\n\n        // Reset the project index counter back to 000/A\n        try (Connection conn = dataSource.getConnection();\n             Statement stmt = conn.createStatement()) {\n            stmt.execute("UPDATE project_index_counter SET current_number = 0, current_letter = \'A\' WHERE id = 1");\n            System.out.println(">>> [WIPE] OK: project_index_counter reset to 000/A");\n        } catch (Exception e) {\n            System.err.println(">>> [WIPE] WARNING: Could not reset project_index_counter: " + e.getMessage());\n        }\n\n        // Reseed the root admin account so nobody gets locked out\n        dataInitializer.seedRootUser();\n        System.out.println(">>> [WIPE] OK: admin_root reseeded");\n\n        // Reseed the default stage template checklist\n        stageTemplateService.seedDefaultStagesIfEmpty();\n        System.out.println(">>> [WIPE] OK: default stage template reseeded");\n\n        System.out.println(">>> [WIPE] SYSTEM RESET COMPLETE. Fresh start.");\n\n        Map<String, Object> response = new LinkedHashMap<>();\n        response.put("wiped", true);\n        response.put("tablesWiped", TABLES_TO_WIPE);\n        response.put("message", "All business data deleted. Root admin login, project index, and default stage template were reseeded to defaults. You will need to log in again with the ADMIN_EMAIL / ADMIN_DEFAULT_PASSWORD credentials. NOTE: files already on Cloudinary were NOT deleted.");\n        return ResponseEntity.ok(response);\n    }\n}\n'

# (file, old, new) patches applied with str.replace, in order
PATCHES = [
    (
        "erp-frontend/src/services/settingsService.js",
        '    /**\n     * GOVERNANCE: EMERGENCY KEY RESET\n     */\n    resetOperatorKey: async (username) => {\n        try {\n            const response = await api.post(\'/staff/reset-password\', { username });\n            return response.data.temporaryPassword;\n        } catch (error) {\n            const serverMsg = error.response?.data?.message || "RESET_FAILED";\n            throw new Error(serverMsg.toUpperCase());\n        }\n    }\n};',
        '    /**\n     * GOVERNANCE: EMERGENCY KEY RESET\n     */\n    resetOperatorKey: async (username) => {\n        try {\n            const response = await api.post(\'/staff/reset-password\', { username });\n            return response.data.temporaryPassword;\n        } catch (error) {\n            const serverMsg = error.response?.data?.message || "RESET_FAILED";\n            throw new Error(serverMsg.toUpperCase());\n        }\n    },\n\n    /**\n     * DANGER ZONE: FULL SYSTEM WIPE (ROOT ONLY)\n     * Permanently deletes every client, project, payment, and log, then\n     * reseeds a clean root login, project index counter, and default\n     * stage template. Cannot be undone.\n     */\n    wipeAllData: async () => {\n        try {\n            const response = await api.post(\'/admin/system/wipe-all-data\', null, {\n                params: { confirm: \'WIPE-EVERYTHING\' }\n            });\n            return response.data;\n        } catch (error) {\n            const serverMsg = error.response?.data?.message || "WIPE_FAILED";\n            throw new Error(serverMsg.toUpperCase());\n        }\n    }\n};',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "    const [drawers,       setDrawers]       = useState({ security: true, governance: true });\n    const [pwdState,      setPwdState]      = useState({ old: '', new: '', confirm: '' });\n    const [pwdLoading,    setPwdLoading]    = useState(false);\n    const [showOld,       setShowOld]       = useState(false);\n    const [showNew,       setShowNew]       = useState(false);\n    const [showConfirm,   setShowConfirm]   = useState(false);\n    const [operators,     setOperators]     = useState([]);\n    const [opLoading,     setOpLoading]     = useState(false);\n    const [newOpModal,    setNewOpModal]    = useState(false);\n    const [newOpData,     setNewOpData]     = useState({ username: '', email: '', role: 'ROLE_MANAGER' });\n    const [tempKeyReveal, setTempKeyReveal] = useState(null);",
        "    const [drawers,       setDrawers]       = useState({ security: true, governance: true, danger: false });\n    const [pwdState,      setPwdState]      = useState({ old: '', new: '', confirm: '' });\n    const [pwdLoading,    setPwdLoading]    = useState(false);\n    const [showOld,       setShowOld]       = useState(false);\n    const [showNew,       setShowNew]       = useState(false);\n    const [showConfirm,   setShowConfirm]   = useState(false);\n    const [operators,     setOperators]     = useState([]);\n    const [opLoading,     setOpLoading]     = useState(false);\n    const [newOpModal,    setNewOpModal]    = useState(false);\n    const [newOpData,     setNewOpData]     = useState({ username: '', email: '', role: 'ROLE_MANAGER' });\n    const [tempKeyReveal, setTempKeyReveal] = useState(null);\n    const [wipeConfirmText, setWipeConfirmText] = useState('');\n    const [wiping,          setWiping]          = useState(false);",
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "    // ── STATUS TOGGLE ──\n    const handleStatusToggle = async (opUsername, currentlyActive) => {\n        const action = currentlyActive ? 'SUSPEND' : 'RESTORE';\n        const ok = await confirm(`${action} OPERATOR`, `Physically ${action.toLowerCase()} access for ${opUsername}?`, 'warn');\n        if (!ok) return;\n        try { await settingsService.toggleOperator(opUsername, !currentlyActive); fetchOperators(); }\n        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }\n    };",
        "    // ── STATUS TOGGLE ──\n    const handleStatusToggle = async (opUsername, currentlyActive) => {\n        const action = currentlyActive ? 'SUSPEND' : 'RESTORE';\n        const ok = await confirm(`${action} OPERATOR`, `Physically ${action.toLowerCase()} access for ${opUsername}?`, 'warn');\n        if (!ok) return;\n        try { await settingsService.toggleOperator(opUsername, !currentlyActive); fetchOperators(); }\n        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }\n    };\n\n    // -- FULL SYSTEM WIPE (DANGER ZONE) --\n    const handleWipeAllData = async () => {\n        if (wipeConfirmText !== 'WIPE-EVERYTHING') return;\n        const ok = await confirm(\n            'FULL SYSTEM WIPE',\n            'This permanently deletes every client, project, payment, and log in the system. This CANNOT be undone. Continue?',\n            'danger'\n        );\n        if (!ok) return;\n        setWiping(true);\n        try {\n            await settingsService.wipeAllData();\n            toast('SYSTEM WIPED. LOGGING OUT...', 'success', 6000);\n            setWipeConfirmText('');\n            setTimeout(logout, 2500);\n        } catch (err) {\n            toast(err.message || 'WIPE FAILED', 'error', 8000);\n        } finally {\n            setWiping(false);\n        }\n    };",
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '                    </div>\n                )}\n            </div>\n\n            {/* PROVISION MODAL */}',
        '                    </div>\n                )}\n\n                {/* PANEL: DANGER ZONE (ROOT ONLY) */}\n                {isRoot && (\n                    <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>\n                        <DrawerHeader label="DANGER ZONE" isOpen={drawers.danger} onClick={() => toggleDrawer(\'danger\')} icon={FiAlertTriangle} />\n                        <div className={`${styles.panelBody} ${drawers.danger ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.danger}>\n                            <div className={styles.panelInner}>\n                                <div className={styles.securityAlert} style={{ borderColor: \'var(--red)\' }}>\n                                    <FiAlertTriangle aria-hidden="true" style={{ color: \'var(--red)\' }} />\n                                    <span>\n                                        Permanently deletes every client, project, payment, and log in the system.\n                                        Cannot be undone. Root login, project index, and default stage template\n                                        are automatically restored to defaults right after.\n                                    </span>\n                                </div>\n                                <div className={styles.wipeField}>\n                                    <HardwareInput\n                                        label=\'TYPE "WIPE-EVERYTHING" TO UNLOCK\'\n                                        value={wipeConfirmText}\n                                        onChange={e => setWipeConfirmText(e.target.value)}\n                                    />\n                                </div>\n                                <button\n                                    className={styles.wipeBtn}\n                                    disabled={wipeConfirmText !== \'WIPE-EVERYTHING\' || wiping}\n                                    onClick={handleWipeAllData}\n                                >\n                                    {wiping ? \'WIPING...\' : <><FiAlertTriangle aria-hidden="true" /> WIPE ALL DATA</>}\n                                </button>\n                            </div>\n                        </div>\n                    </div>\n                )}\n            </div>\n\n            {/* PROVISION MODAL */}',
    ),
]

CSS_PATH = "erp-frontend/src/pages/settings/SettingsPage.module.css"
CSS_MARKER = 'DANGER ZONE'
CSS_APPEND = "\n\n/* -- DANGER ZONE -------------------------------------------------- */\n.dangerPanel { border-color: rgba(239,68,68,0.35); }\n.dangerPanel:hover { border-color: rgba(239,68,68,0.55); }\n.dangerPanel .drawerTitle, .dangerPanel .chevron { color: var(--red); }\n.dangerPanel .drawerHeader { border-bottom-color: rgba(239,68,68,0.18); }\n.dangerPanel .drawerHeader:hover { background: rgba(239,68,68,0.05); }\n\n.wipeField { margin: var(--gap-md) 0; }\n\n.wipeBtn {\n    background: var(--red); color: #fff; border: none;\n    padding: 0 var(--btn-px, clamp(16px,2vw,24px));\n    height: var(--btn-height, clamp(38px, 5vw, 44px));\n    border-radius: var(--input-radius, var(--radius-sm));\n    font-family: 'DM Sans', sans-serif; font-weight: 900;\n    font-size: var(--fs-btn); text-transform: uppercase; letter-spacing: 1px;\n    cursor: pointer; display: inline-flex; align-items: center;\n    gap: clamp(5px,0.7vw,8px); transition: background 0.2s, transform 0.2s, box-shadow 0.2s;\n    box-shadow: 0 3px 10px rgba(0,0,0,0.2);\n    white-space: nowrap; width: 100%; justify-content: center;\n}\n.wipeBtn:hover:not(:disabled) { background: #dc2626; transform: translateY(-2px); box-shadow: 0 6px 18px rgba(239,68,68,0.35); }\n.wipeBtn:disabled { opacity: 0.4; cursor: not-allowed; }\n.wipeBtn:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }\n"


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
    # 1) New backend controller file
    full_new_path = os.path.join(ROOT, NEW_CONTROLLER_PATH)
    if os.path.exists(full_new_path):
        print("SKIP (already exists): " + NEW_CONTROLLER_PATH)
    else:
        write_file(full_new_path, NEW_CONTROLLER_CONTENT)
        print("OK: created " + NEW_CONTROLLER_PATH)

    # 2) str.replace patches
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
            print("MISSING (patch target not found): " + rel_path)
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("OK: patched " + rel_path)

    # 3) CSS append (idempotent via marker check)
    full_css_path = os.path.join(ROOT, CSS_PATH)
    if not os.path.exists(full_css_path):
        print("MISSING (file not found): " + CSS_PATH)
    else:
        css_content = read_file(full_css_path)
        if CSS_MARKER in css_content:
            print("SKIP (already patched): " + CSS_PATH)
        else:
            write_file(full_css_path, css_content + CSS_APPEND)
            print("OK: appended danger-zone styles to " + CSS_PATH)

    print("")
    print("Done. Next steps:")
    print("1. git add -A && git commit -m \'Add root-only full system data wipe\' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Log in, go to Settings, scroll to DANGER ZONE, type WIPE-EVERYTHING,")
    print("   click WIPE ALL DATA, confirm the popup.")
    print("4. Log back in with ADMIN_EMAIL / ADMIN_DEFAULT_PASSWORD and set a new")
    print("   password from Settings.")


if __name__ == "__main__":
    main()