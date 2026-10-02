// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/ScenarioSeeder.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import com.gesolutions.erp.modules.land.model.DocumentCategory;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.LandTitle;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.repository.DocumentCategoryRepository;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.repository.ProjectDocumentRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import com.gesolutions.erp.modules.land.service.DocumentCategoryService;
import com.gesolutions.erp.modules.land.service.ProjectIndexService;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import javax.sql.DataSource;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.Statement;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * GOLDEN SEED -- SCENARIO SEEDER (dataset v4, fix167).
 *
 * Runs once (flag id = 4 in scenario_seed_flag). Step 1 removes every earlier
 * seed (v1, v2, v3, and v4 itself if the flag was cleared) -- and ONLY seed rows:
 * a client counts as seed when its NIN is CMS4/CMS3xxxxxxxxxx (v4/v3), CM9000000000xx
 * (v1) or one of the 24 exact v2 NINs. Real NINs never have a letter in the
 * third position and the v2 list is matched exactly, so real people are never
 * touched. Step 2 loads ScenarioData with every date back-dated so charts,
 * ageing, storage fees and recovery states behave as they would after a year
 * of real use.
 *
 * Demo staff are named demo.* and get a random password nobody knows, so no
 * one can sign in as them. Their names appear in audit lines, call notes,
 * payments and expenses so the Director's staff-activity view has real content.
 */
@Component
@RequiredArgsConstructor
public class ScenarioSeeder {

    public static final int VERSION = 5;   // fix180: project types, clients + owners, status lists per type, new title fields
    private static final int BELL_DAYS = 45;
    private static final String DEMO_LIKE = "demo.%";

    private final DataSource dataSource;
    private final PlatformTransactionManager txManager;
    private final PasswordEncoder passwordEncoder;
    private final UserRepository userRepository;
    private final ClientRepository clientRepository;
    private final RecoveryNoteRepository recoveryNoteRepository;
    private final LandProjectRepository projectRepository;
    private final ProjectStatusRepository statusRepository;
    private final PaymentRecordRepository paymentRepository;
    private final ProjectDocumentRepository documentRepository;
    private final FollowUpRepository followUpRepository;
    private final DocumentCategoryRepository categoryRepository;
    private final DocumentCategoryService categoryService;
    private final ProjectIndexService indexService;
    private final ExpenseRepository expenseRepository;
    private final ExpensePresetRepository presetRepository;
    private final NotificationRepository notificationRepository;
    private final NotificationReadRepository notificationReadRepository;
    private final AuditLogRepository auditRepository;

    // ---- per-run state
    private LocalDateTime now;
    private final List<AuditLog> audits = new ArrayList<>();
    private final List<Notification> bell = new ArrayList<>();
    private final Map<String, User> users = new LinkedHashMap<>();
    private final Map<String, Client> clients = new LinkedHashMap<>();
    private final Map<String, String> categoryLabels = new HashMap<>();

    // =====================================================================
    // entry point
    // =====================================================================
    public void seedOnce() {
        JdbcTemplate jdbc = new JdbcTemplate(dataSource);
        try {
            jdbc.execute("CREATE TABLE IF NOT EXISTS scenario_seed_flag (id INTEGER PRIMARY KEY, seeded_at TIMESTAMP NOT NULL DEFAULT now())");
            Integer done = jdbc.queryForObject("SELECT COUNT(*) FROM scenario_seed_flag WHERE id = ?", Integer.class, VERSION);
            if (done != null && done > 0) {
                System.out.println(">>> [SCENARIO] Dataset v" + VERSION + " already seeded -- skipping.");
                return;
            }
            ScenarioData.selfCheck();
        } catch (Exception e) {
            System.err.println(">>> [SCENARIO] cannot start: " + e.getMessage());
            return;
        }

        // Transaction 1: remove old seed rows. Committed on its own so the index counter can be reset safely.
        try {
            new TransactionTemplate(txManager).executeWithoutResult(st -> purge(jdbc));
            resetIndexCounterIfEmpty(jdbc);
        } catch (Exception e) {
            System.err.println(">>> [SCENARIO] purge fault (nothing was changed): " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // Transaction 2: load the new dataset. All or nothing.
        try {
            new TransactionTemplate(txManager).executeWithoutResult(st -> {
                seed();
                new JdbcTemplate(dataSource).update("INSERT INTO scenario_seed_flag (id) VALUES (?) ON CONFLICT (id) DO NOTHING", VERSION);
            });
            System.out.println(">>> [SCENARIO] Dataset v" + VERSION + " seeded ("
                    + ScenarioData.projects().size() + " projects, "
                    + ScenarioData.people().size() + " people, "
                    + ScenarioData.expenses().size() + " expenses).");
        } catch (Exception e) {
            System.err.println(">>> [SCENARIO] seed fault (rolled back, will retry on next start): " + e.getMessage());
            e.printStackTrace();
        }
    }

    // =====================================================================
    // PURGE
    // =====================================================================
    private static String ids(List<String> l) {
        if (l.isEmpty()) return "NULL";
        StringBuilder sb = new StringBuilder();
        for (String s : l) {
            if (sb.length() > 0) sb.append(',');
            sb.append('\'').append(s).append('\'');
        }
        return sb.toString();
    }

    private static List<String> v2Nins() {
        String letters = "ABCDEFGHJKLMNPRSTUWXYZ";
        List<String> out = new ArrayList<>();
        for (int i = 1; i <= 24; i++) {
            out.add("CM99" + String.format("%06d", 120000 + (i * 3719) % 880000)
                    + letters.charAt(i % letters.length())
                    + letters.charAt((i * 5 + 3) % letters.length())
                    + letters.charAt((i * 7 + 1) % letters.length())
                    + letters.charAt((i * 11 + 2) % letters.length()));
        }
        return out;
    }

    private List<String> uuids(JdbcTemplate jdbc, String sql) {
        return jdbc.query(sql, (rs, i) -> String.valueOf(rs.getObject(1)));
    }

    private void purge(JdbcTemplate jdbc) {
        List<String> nins = new ArrayList<>();
        for (String n : v2Nins()) nins.add("'" + n + "'");
        List<String> clientIds = uuids(jdbc, "SELECT id FROM clients WHERE national_id LIKE 'CMS4%' OR national_id LIKE 'CMS3%' OR national_id LIKE 'CM9000000000%' OR national_id IN (" + String.join(",", nins) + ")");
        List<String> names = jdbc.query("SELECT full_name FROM clients WHERE id IN (" + ids(clientIds) + ")", (rs, i) -> rs.getString(1));
        List<String> projectIds = clientIds.isEmpty() ? new ArrayList<>() : uuids(jdbc,
                "SELECT project_id FROM project_proprietors GROUP BY project_id HAVING bool_and(client_id IN (" + ids(clientIds) + "))");
        List<String> titleIds = projectIds.isEmpty() ? new ArrayList<>() : uuids(jdbc,
                "SELECT title_id FROM land_projects WHERE title_id IS NOT NULL AND id IN (" + ids(projectIds) + ")");
        List<String> staffIds = uuids(jdbc, "SELECT id FROM users WHERE username LIKE '" + DEMO_LIKE + "'");
        List<String> expenseIds = uuids(jdbc, "SELECT id FROM expenses WHERE recorded_by LIKE '" + DEMO_LIKE + "'");

        List<String> entityIds = new ArrayList<>();
        entityIds.addAll(projectIds); entityIds.addAll(clientIds); entityIds.addAll(staffIds); entityIds.addAll(expenseIds);
        if (!entityIds.isEmpty()) {
            List<String> notifIds = uuids(jdbc, "SELECT id FROM notifications WHERE entity_id IN (" + ids(entityIds) + ")");
            if (!notifIds.isEmpty()) {
                jdbc.update("DELETE FROM notification_reads WHERE notification_id IN (" + ids(notifIds) + ")");
                jdbc.update("DELETE FROM notifications WHERE id IN (" + ids(notifIds) + ")");
            }
        }
        if (!staffIds.isEmpty()) jdbc.update("DELETE FROM notification_reads WHERE user_id IN (" + ids(staffIds) + ")");

        // audit lines written by demo staff, plus lines the old seeds wrote as SYSTEM
        jdbc.update("DELETE FROM audit_logs WHERE performed_by LIKE '" + DEMO_LIKE + "'");
        jdbc.update("DELETE FROM audit_logs WHERE performed_by = 'SYSTEM' AND action IN ('INTAKE','RECEIVABLE_TRIGGER','PROJECT_STAGES_ATTACHED','PROJECT_STATUSES_ATTACHED','CLIENT_ARCHIVE','DOCUMENT_UPLOADED','STORAGE_FEE_RESUMED')");
        for (String n : names) jdbc.update("DELETE FROM audit_logs WHERE performed_by = 'SYSTEM' AND details LIKE ?", "%" + n + "%");

        if (!projectIds.isEmpty()) {
            String p = ids(projectIds);
            for (String t : new String[] { "payment_records", "follow_up_logs", "project_documents", "project_statuses", "project_neighbors", "payment_schedules" }) {
                Boolean exists = jdbc.queryForObject("SELECT to_regclass('public." + t + "') IS NOT NULL", Boolean.class);
                if (Boolean.TRUE.equals(exists)) jdbc.update("DELETE FROM " + t + " WHERE project_id IN (" + p + ")");
            }
        }
        if (!clientIds.isEmpty()) jdbc.update("DELETE FROM recovery_notes WHERE client_id IN (" + ids(clientIds) + ")");
        if (!projectIds.isEmpty()) {
            jdbc.update("DELETE FROM project_proprietors WHERE project_id IN (" + ids(projectIds) + ")");
            Boolean pc = jdbc.queryForObject("SELECT to_regclass('public.project_clients') IS NOT NULL", Boolean.class);   // fix180
            if (Boolean.TRUE.equals(pc)) jdbc.update("DELETE FROM project_clients WHERE project_id IN (" + ids(projectIds) + ")");
            jdbc.update("DELETE FROM land_projects WHERE id IN (" + ids(projectIds) + ")");
        }
        if (!titleIds.isEmpty()) jdbc.update("DELETE FROM land_titles WHERE id IN (" + ids(titleIds) + ")");
        if (!clientIds.isEmpty()) jdbc.update("DELETE FROM clients WHERE id IN (" + ids(clientIds) + ") AND id NOT IN (SELECT client_id FROM project_proprietors)"
                + (Boolean.TRUE.equals(jdbc.queryForObject("SELECT to_regclass('public.project_clients') IS NOT NULL", Boolean.class)) ? " AND id NOT IN (SELECT client_id FROM project_clients)" : ""));

        jdbc.update("DELETE FROM expenses WHERE recorded_by LIKE '" + DEMO_LIKE + "'");
        jdbc.update("DELETE FROM expense_presets WHERE created_by LIKE '" + DEMO_LIKE + "'");
        jdbc.update("DELETE FROM document_categories WHERE built_in = false AND created_by LIKE '" + DEMO_LIKE + "'");
        jdbc.update("DELETE FROM recovery_notes WHERE author_id IN (SELECT id FROM users WHERE username LIKE '" + DEMO_LIKE + "')");
        jdbc.update("DELETE FROM users WHERE username LIKE '" + DEMO_LIKE + "'");
        System.out.println(">>> [SCENARIO] Old seed rows removed (" + clientIds.size() + " seed people, " + projectIds.size() + " seed projects).");
    }

    /** Uses its own connection so the reset is visible to ProjectIndexService immediately. */
    private void resetIndexCounterIfEmpty(JdbcTemplate jdbc) throws Exception {
        Integer left = jdbc.queryForObject("SELECT COUNT(*) FROM land_projects", Integer.class);
        if (left != null && left == 0) {
            try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
                st.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1");
            }
        }
    }

    // =====================================================================
    // SEED
    // =====================================================================
    private LocalDateTime at(int daysAgo, String salt) {
        int h = Math.abs((salt + daysAgo).hashCode());
        LocalDateTime t = now.toLocalDate().minusDays(Math.max(0, daysAgo)).atTime(8 + h % 9, (h / 7) % 60, (h / 11) % 60);
        if (t.isAfter(now.minusMinutes(3))) t = now.minusMinutes(3 + h % 40);
        return t;
    }

    private void audit(String action, String details, String by, LocalDateTime when) {
        audits.add(AuditLog.builder().action(action).details(details).performedBy(by).timestamp(when).build());
    }

    private void bell(String type, String severity, String message, String entityType, UUID entityId, String role, LocalDateTime when) {
        if (entityId == null || when.isBefore(now.minusDays(BELL_DAYS))) return;
        bell.add(Notification.builder().type(type).severity(severity).message(message)
                .entityType(entityType).entityId(entityId).targetRole(role).createdAt(when).build());
    }

    private void seed() {
        now = LocalDateTime.now();
        audits.clear();
        bell.clear();
        users.clear();
        clients.clear();

        seedCategories();
        seedStaff();
        seedPeople();
        for (ScenarioData.Spec s : ScenarioData.projects()) seedProject(s);
        seedCalls();
        seedExpenses();
        seedBellReads();

        auditRepository.saveAll(audits);
        notificationRepository.saveAll(bell);
    }

    // ---- categories ----------------------------------------------------
    private void seedCategories() {
        for (DocumentCategory c : categoryService.list()) categoryLabels.put(c.getCode(), c.getLabel());
        String[][] custom = { { ScenarioData.SP, "Site Photos" }, { ScenarioData.CL, "Council Letters" } };
        for (String[] c : custom) {
            if (categoryRepository.findByCode(c[0]).isEmpty()) {
                categoryRepository.save(DocumentCategory.builder().code(c[0]).label(c[1]).builtIn(false).sortOrder(100)
                        .createdBy(ScenarioData.MGR1).createdAt(at(200, c[0])).build());
            }
            categoryLabels.put(c[0], c[1]);
        }
    }

    // ---- staff ---------------------------------------------------------
    private void seedStaff() {
        for (ScenarioData.Staff s : ScenarioData.staff()) {
            User u = userRepository.save(User.builder()
                    .username(s.username)
                    .email(s.username + "@demo.gesolutions.local")
                    .password(passwordEncoder.encode(UUID.randomUUID() + "-" + UUID.randomUUID()))
                    .role(Role.valueOf(s.role))
                    .isRoot(false)
                    .isActive(s.active)
                    .mustChangePassword(s.mustChange)
                    .build());
            users.put(s.username, u);
            String creator = ScenarioData.ADMIN.equals(s.username) ? ScenarioData.DIRECTOR : ScenarioData.ADMIN;
            String roleName = s.role.replace("ROLE_", "");
            audit("OPERATOR_PROVISIONED", "New " + s.role + " account created: " + s.username, creator, at(s.createdAgo, s.username));
            bell("STAFF_PROVISIONED", "INFO", "Operator " + s.username + " provisioned as " + roleName + ".", "STAFF", u.getId(), "ROLE_DIRECTOR", at(s.createdAgo, s.username));
            if (s.promotedAgo > 0) {
                audit("RANK_ADJUSTMENT", "Operator " + s.username + " rank shifted to " + s.role, ScenarioData.ADMIN, at(s.promotedAgo, s.username));
                bell("STAFF_ROLE_CHANGED", "WARN", "Operator " + s.username + " is now " + roleName + ".", "STAFF", u.getId(), "ROLE_DIRECTOR", at(s.promotedAgo, s.username));
            }
            if (s.suspendedAgo > 0) {
                audit("OPERATOR_STATUS_CHANGE", "Account [" + s.username + "] moved to SUSPENDED", ScenarioData.ADMIN, at(s.suspendedAgo, s.username));
                bell("STAFF_SUSPENDED", "WARN", "Operator " + s.username + " suspended.", "STAFF", u.getId(), "ROLE_DIRECTOR", at(s.suspendedAgo, s.username));
            }
            if (s.keyResetAgo > 0) {
                audit("CREDENTIAL_RESET", "Temporary key generated for: " + s.username, ScenarioData.ADMIN, at(s.keyResetAgo, s.username));
                bell("KEY_RESET", "WARN", "Security key reset for " + s.username + ". They must change it at next sign in.", "STAFF", u.getId(), "ROLE_DIRECTOR", at(s.keyResetAgo, s.username));
            }
        }
    }

    // ---- people --------------------------------------------------------
    private void seedPeople() {
        List<ScenarioData.Person> people = ScenarioData.people();
        Map<String, Integer> position = new HashMap<>();
        for (int i = 0; i < people.size(); i++) position.put(people.get(i).key, i + 1);

        // recovery numbers come from the call list
        Map<String, LocalDateTime> last = new HashMap<>();
        Map<String, Integer> month = new HashMap<>();
        Map<String, Double> score = new HashMap<>();
        List<ScenarioData.Call> calls = new ArrayList<>(ScenarioData.calls());
        calls.sort((a, b) -> Integer.compare(b.ago, a.ago));
        for (ScenarioData.Call c : calls) {
            LocalDateTime t = at(c.ago, c.person + c.tag);
            if (last.get(c.person) == null || t.isAfter(last.get(c.person))) last.put(c.person, t);
            if (t.getMonth() == now.getMonth() && t.getYear() == now.getYear()) month.merge(c.person, 1, Integer::sum);
            double cur = score.getOrDefault(c.person, 100.0);
            cur += ScenarioData.ANS.equals(c.tag) ? 1.5 : -2.0;
            score.put(c.person, Math.max(0.0, Math.min(100.0, cur)));
        }
        score.putAll(ScenarioData.reliabilityOverrides());

        for (ScenarioData.Person p : people) {
            int i = position.get(p.key);
            int phoneIdx = (p.shareWith == null || p.shareWith.isEmpty()) ? i : position.get(p.shareWith);
            Client c = clientRepository.save(Client.builder()
                    .fullName(p.name)
                    .phoneNumber(ScenarioData.phoneFor(p.key, phoneIdx))
                    .nationalId(ScenarioData.nin(i))
                    .email(p.email == null || p.email.isEmpty() ? null : p.email)
                    .homeAddress(p.address)
                    .lastContactedAt(last.get(p.key))
                    .monthlyContactCount(month.getOrDefault(p.key, 0))
                    .reliabilityScore(score.getOrDefault(p.key, 100.0))
                    .build());
            clients.put(p.key, c);
        }
    }

    // ---- one project ---------------------------------------------------
    private String label(ScenarioData.Spec s, String index) {
        return s.plot != null && !s.pendingTitle ? s.plot : "project #" + index;
    }

    private String money(long v) { return String.valueOf(v); }

    private void seedProject(ScenarioData.Spec s) {
        String index = indexService.generateNextIndex();
        int entry = s.entry();
        LocalDateTime entryAt = at(entry, s.key);
        String staff = s.intakeBy;

        // --- title
        LandTitle title = null;
        if (s.hasTitle()) {
            int createdAgo = s.isFolder() ? s.issuedAgo : entry;
            title = LandTitle.builder()
                    .tenure(s.tenure)
                    .plotNumber(s.pendingTitle ? null : s.plot)
                    .block(s.pendingTitle ? null : s.block)
                    .areaHectares(s.pendingTitle ? null : hectares(s.area))      // fix180
                    .volume(s.pendingTitle ? null : volumeOf(s.volumeFolio))
                    .folio(s.pendingTitle ? null : folioOf(s.volumeFolio))
                    .projectStartDate(now.toLocalDate().minusDays(s.startAgo))
                    .titleIssueDate(s.pendingTitle ? null : now.toLocalDate().minusDays(s.issuedAgo))
                    .isReleased(s.releasedNow())
                    .releasedAt(s.releasedNow() ? at(s.releasedAgo, s.key + "X") : null)
                    .releasedBy(s.releasedNow() ? ScenarioData.DIRECTOR : null)
                    .releaseNote(s.releasedNow() ? releaseNote(s) : null)
                    .createdAt(at(createdAgo, s.key + "T"))
                    .build();
        }

        // --- money on the project row
        boolean recvNow = s.receivableNow();
        long totalCost = s.storedCost();
        long debt = s.origDebt >= 0 ? s.origDebt : Math.max(0, s.cost - s.paidBeforeReceivable());
        LocalDateTime lastPay = null;
        for (ScenarioData.Pay p : s.pays) {
            if (p.reversed()) continue;
            LocalDateTime t = at(s.payAgo(p), s.key + p.amount + p.ago);
            if (lastPay == null || t.isAfter(lastPay)) lastPay = t;
        }

        LandProject.LandProjectBuilder b = LandProject.builder()
                .landTitle(title)
                .projectIndex(index)
                .projectStartDate(now.toLocalDate().minusDays(s.startAgo))
                .entryDate(now.toLocalDate().minusDays(entry))
                .district(s.district).county(s.county).subCounty(s.subCounty).parish(s.parish).village(s.village).area(s.area)
                .totalCost(BigDecimal.valueOf(totalCost))
                .amountPaid(BigDecimal.valueOf(s.paid()))
                .isLegacy(s.legacy())
                .projectType(s.type().name())   // fix180
                .isReceivable(recvNow)
                .currentStatusIndex(s.statusIndex())
                .status(s.status())
                .lastPaymentDate(lastPay)
                .problem(s.problemNow())
                .problemBy(s.problemNow() ? ScenarioData.MGR1 : null)
                .problemAt(s.problemNow() ? at(s.problemAgo, s.key + "P") : null)
                .problemNote(s.problemNow() ? s.problemNote : null)
                .storagePaused(s.activePause())
                .storagePausedAt(s.activePause() ? at(s.pauseAgo, s.key + "Z") : null)
                .deleted(s.deletedAgo >= 0 && s.restoredAgo < 0)
                .deletedAt(s.deletedAgo >= 0 && s.restoredAgo < 0 ? at(s.deletedAgo, s.key + "D") : null);
        if (s.recvAgo >= 0) {
            b.originalDebt(BigDecimal.valueOf(debt))
             .storageFeesAccumulated(BigDecimal.valueOf(s.storedFees()))
             .storageFeesPaid(BigDecimal.valueOf(s.storedFeesPaid()))
             .receivableMonthsBilled(Math.max(0, s.billed));
            if (s.exit == null || !"PAID_OFF".equals(s.exit)) {
                // the folder screen never clears the start date when a plot leaves receivables.
                // fix167: a pause that already ended moved the billing clock forward by the paused days.
                b.receivableStartDate(at(s.clockAgo(), s.key + "R"));
            }
            if (recvNow && s.startOverride) b.receivableStartOverride(at(s.recvAgo, s.key + "R"));
        }
        if (s.customRate && recvNow) b.storageFeeOverride(BigDecimal.valueOf(s.rate));
        if (s.activePause() && s.deadlineIn != null) b.negotiationDeadline(now.toLocalDate().plusDays(s.deadlineIn).atTime(23, 59, 59));

        Set<Client> owners = new HashSet<>();
        StringBuilder ownerNames = new StringBuilder();
        for (String o : s.owners) {
            owners.add(clients.get(o));
            if (ownerNames.length() > 0) ownerNames.append(" & ");
            ownerNames.append(clients.get(o).getFullName());
        }
        b.proprietors(owners);
        b.clients(new HashSet<>(owners));   // fix180: in the demo data the clients are the owners
        LandProject saved = projectRepository.save(b.build());
        UUID pid = saved.getId();
        String lbl = label(s, index);
        String owner1 = clients.get(s.owners[0]).getFullName();

        // --- audit: identity + intake
        for (String o : s.owners) {
            Client c = clients.get(o);
            audit("CLIENT_ARCHIVE", "New identity registered via NIN: " + c.getFullName() + " (" + c.getNationalId() + ")", staff, entryAt.minusMinutes(2));
        }
        audit("INTAKE", "Operator [" + staff + "] ingested binder: " + (s.hasTitle() && !s.pendingTitle && !s.isFolder() ? s.plot : "project #" + index)
                + (s.recvAtIntake ? " [ENTERED AS RECEIVABLE]" : ""), staff, entryAt);
        bell("NEW_INTAKE", "INFO", "New project " + index + " registered by " + staff + ".", "PROJECT", pid, "ROLE_MANAGER", entryAt);
        if (s.recvAtIntake) {
            audit("RECEIVABLE_TRIGGER", "Operator [" + staff + "] flagged plot " + lbl + " as RECEIVABLE at intake. Debt: UGX " + money(debt), staff, entryAt.plusMinutes(1));
        }

        // --- statuses
        if (s.statusesAttached()) seedStatuses(s, pid, entryAt, staff);

        // --- payments (oldest first so the running balance is right)
        seedPayments(s, pid, index, lbl, owner1, staff);

        // --- receivable history
        seedReceivableHistory(s, pid, index, lbl, owner1, debt);

        // --- documents
        for (ScenarioData.Doc d : s.docs) {
            String by = d.by != null ? d.by : (d.ago > 60 ? staff : ScenarioData.SEC1);
            String cat = d.category;
            String ext = d.mime != null && d.mime.startsWith("image") ? "jpg" : "pdf";
            String fname = d.fileName != null ? d.fileName
                    : slug(categoryLabels.getOrDefault(cat, "document")) + "-" + slug(owner1) + "." + ext;
            addDocument(pid, index, cat, fname, d.mime != null ? d.mime : "application/pdf", by, at(Math.min(d.ago, entry), s.key + fname));
        }

        // --- notes
        for (ScenarioData.Note n : s.notes) {
            if (n.ago == -1) {
                followUpRepository.save(FollowUpLog.builder().projectId(pid).notes("INTAKE NOTE: " + n.text).recordedBy(staff).timestamp(entryAt.plusMinutes(1)).build());
                continue;
            }
            UUID ownerId = n.ownerKey == null ? null : clients.get(n.ownerKey).getId();
            LocalDateTime t = at(n.ago, s.key + n.text);
            followUpRepository.save(FollowUpLog.builder().projectId(pid).ownerId(ownerId).notes(n.text).recordedBy(n.by).timestamp(t).build());
            audit(ownerId == null ? "NOTE_ADDED" : "RECOVERY_SYNC",
                    ownerId == null ? "Operator [" + n.by + "] added note to plot: " + lbl
                                    : "Operator [" + n.by + "] logged call for plot: " + lbl + " (owner reached: " + ownerId + ")", n.by, t);
        }

        // --- problem flag (and fix167: flagged-then-cleared history)
        if (s.problemAgo >= 0) {
            String by = ScenarioData.MGR1;
            LocalDateTime t = at(s.problemAgo, s.key + "P");
            followUpRepository.save(FollowUpLog.builder().projectId(pid).notes("[PROBLEM] " + s.problemNote).recordedBy(by).timestamp(t).build());
            audit("PROBLEM_FLAG", "Operator [" + by + "] flagged PROBLEM on #" + index + ": " + s.problemNote + ".", by, t);
            bell("PROBLEM_FLAGGED", "CRITICAL", "Plot " + lbl + " flagged as a problem by " + by + ": " + s.problemNote, "PROJECT", pid, "ALL", t);
            if (s.problemClearedAgo >= 0) {
                String cb = ScenarioData.DIRECTOR;
                LocalDateTime c = at(s.problemClearedAgo, s.key + "PC");
                followUpRepository.save(FollowUpLog.builder().projectId(pid).notes("[PROBLEM CLEARED] " + s.clearNote).recordedBy(cb).timestamp(c).build());
                audit("PROBLEM_FLAG", "Operator [" + cb + "] cleared PROBLEM on #" + index + ": " + s.clearNote + ".", cb, c);
            }
        }

        // --- fix167: title taken off again
        if (s.revertAgo >= 0) {
            LocalDateTime t = at(s.revertAgo, s.key + "RV");
            audit("TITLE_REVERTED", "Operator [" + ScenarioData.DIRECTOR + "] took the saved title off project " + index
                    + ". Old title: plot " + s.revertedPlot + ", block KYADONDO BLOCK 0, area 0.4 ha, volume LRV 0000, folio 0, tenure FREEHOLD. Reason: Typed on the wrong project.", ScenarioData.DIRECTOR, t);
        }

        // --- title produced in bulk (details still to be typed in)
        if (s.pendingTitle) {
            audit("BULK_TITLE_PRODUCED", "Operator [" + ScenarioData.MGR1 + "] marked 1 projects as Titled.", ScenarioData.MGR1, at(s.issuedAgo, s.key + "B"));
        }

        // --- manual status override
        if (s.overrideTo > 0) {
            String by = ScenarioData.MGR2;
            LocalDateTime t = at(s.overrideAgo, s.key + "O");
            audit("STATUS_OVERRIDE", "Operator [" + by + "] shifted plot " + lbl + " from status 1 to status " + s.overrideTo, by, t);
            bell("STATUS_ADVANCED", "POSITIVE", lbl + " moved from status 1 to status " + s.overrideTo + " by " + by + ".", "PROJECT", pid, "ROLE_MANAGER", t);
        }

        // --- release (fix167: with a hand-over note, and the undo history)
        if (s.releasedAgo >= 0) {
            String by = ScenarioData.DIRECTOR;
            LocalDateTime t = at(s.releasedAgo, s.key + "X");
            followUpRepository.save(FollowUpLog.builder().projectId(pid).notes("[HANDED OVER] " + releaseNote(s)).recordedBy(by).timestamp(t).build());
            audit("TITLE_RELEASED", "Operator [" + by + "] authorized handover for Plot: " + s.plot + ". Note: " + releaseNote(s), by, t);
            bell("TITLE_COMPLETED", "POSITIVE", "Title for " + lbl + " released to the client.", "PROJECT", pid, "ROLE_DIRECTOR", t);
            if (s.undoReleaseAgo >= 0) {
                LocalDateTime u = at(s.undoReleaseAgo, s.key + "XU");
                String why = "Hand-over was recorded on the wrong plot.";
                followUpRepository.save(FollowUpLog.builder().projectId(pid).notes("[HAND-OVER UNDONE] " + why).recordedBy(by).timestamp(u).build());
                audit("TITLE_RELEASE_UNDONE", "Operator [" + by + "] undid the hand-over of " + lbl + ". Reason: " + why, by, u);
            }
        }

        // --- soft delete / restore
        if (s.deletedAgo >= 0) {
            LocalDateTime t = at(s.deletedAgo, s.key + "D");
            audit("RECORD_DELETED", "Root user [" + ScenarioData.ADMIN + "] deleted plot: " + lbl, ScenarioData.ADMIN, t);
            bell("PROJECT_DELETED", "CRITICAL", "Plot " + lbl + " deleted by " + ScenarioData.ADMIN + ". Restore it from Settings -> Archive.", "PROJECT", pid, "ROLE_DIRECTOR", t);
            if (s.restoredAgo >= 0) {
                LocalDateTime r = at(s.restoredAgo, s.key + "U");
                audit("RECORD_RESTORED", "Root user [" + ScenarioData.ADMIN + "] restored plot: " + lbl, ScenarioData.ADMIN, r);
                bell("PROJECT_RESTORED", "POSITIVE", "Plot " + lbl + " restored by " + ScenarioData.ADMIN + ".", "PROJECT", pid, "ROLE_DIRECTOR", r);
            }
        }
    }

    private String releaseNote(ScenarioData.Spec s) {
        return "Collected in person by " + clients.get(s.owners[0]).getFullName() + "; National ID checked against the card.";
    }

    private static String slug(String v) {
        return v.toLowerCase().replaceAll("[^a-z0-9]+", "-").replaceAll("^-|-$", "");
    }

    private ProjectDocument addDocument(UUID pid, String index, String cat, String fileName, String mime, String by, LocalDateTime when) {
        ProjectDocument doc = documentRepository.save(ProjectDocument.builder()
                .projectId(pid).fileName(fileName).fileType(mime).category(cat)
                .filePath("https://res.cloudinary.com/dfd115bnz/raw/upload/v1/ge_solutions/demo/" + index + "/" + fileName)
                .internalNotes(null).uploadedBy(by).uploadedAt(when).build());
        audit("DOCUMENT_UPLOADED", "Operator [" + by + "] uploaded 1 document(s) to plot: " + pid + " [" + (cat == null ? "UNCATEGORISED" : cat) + "]", by, when);
        bell("DOC_UPLOADED", "INFO", "1 document(s) attached to project #" + index + " by " + by + ".", "PROJECT", pid, "ROLE_MANAGER", when);
        return doc;
    }

    // fix180: "LRV 4001 FOLIO 2" -> volume "LRV 4001", folio "2"; "2 acres" -> 0.8094 hectares
    private static String volumeOf(String vf) {
        if (vf == null) return null;
        int i = vf.toUpperCase().indexOf(" FOLIO ");
        return i < 0 ? vf : vf.substring(0, i).trim();
    }

    private static String folioOf(String vf) {
        if (vf == null) return null;
        int i = vf.toUpperCase().indexOf(" FOLIO ");
        return i < 0 ? null : vf.substring(i + 7).trim();
    }

    private static BigDecimal hectares(String area) {
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("([0-9]+(?:[.][0-9]+)?)").matcher(area == null ? "" : area);
        double v = m.find() ? Double.parseDouble(m.group(1)) : 1.0;
        double ha = area != null && area.toLowerCase().contains("acre") ? v * 0.404686 : v;
        return BigDecimal.valueOf(Math.max(0.0001, ha)).setScale(4, java.math.RoundingMode.HALF_UP);
    }

    // ---- statuses ------------------------------------------------------
    // fix180: the project type's own list. A folder's 6 progress steps (Spec.done) are spread over that list; New Title
    // (Transfer of Title) projects have their first status done, Legacy Titles all of them.
    private void seedStatuses(ScenarioData.Spec s, UUID pid, LocalDateTime entryAt, String staff) {
        int span = Math.max(1, s.entry());
        int order = 0;
        List<String> names = s.type().getDefaultStatuses();
        int n = names.size();
        int doneN, atIntake;
        if (!s.isFolder()) {
            doneN = s.legacy() ? n : 1;
            atIntake = doneN;
        } else {
            doneN = s.done >= ScenarioData.STEPS ? n : Math.min(n - 1, Math.round(s.done * n / (float) ScenarioData.STEPS));
            atIntake = Math.min(doneN, s.ticksAtIntake() >= ScenarioData.STEPS ? n : Math.round(s.ticksAtIntake() * n / (float) ScenarioData.STEPS));
            if (s.done > 0 && doneN == 0) doneN = 1;
            if (s.ticksAtIntake() > 0 && atIntake == 0) atIntake = 1;
        }
        int attached = n + s.custom.size();
        audit("PROJECT_STATUSES_ATTACHED", "Operator [" + staff + "] attached " + attached + " status(es) to project: " + pid, staff, entryAt.plusMinutes(1));
        String[] crew = { ScenarioData.MGR1, ScenarioData.MGR2, ScenarioData.ADMIN };
        for (int k = 0; k < n; k++) {
            boolean done = k < doneN;
            LocalDateTime doneAt = null;
            String who = null;
            if (done && k < atIntake) {
                // fix167: ticked on the New Project page -> saved at intake, by the intake staff
                doneAt = entryAt;
                who = staff;
            } else if (done) {
                int ago;
                if (doneN >= n && s.issuedAgo >= 0) ago = span - (k + 1) * (span - s.issuedAgo) / doneN;
                else ago = span - (k + 1) * span / (doneN + 2);
                doneAt = at(Math.max(0, Math.min(span - 1, ago)), s.key + "S" + k);
                who = crew[k % 3];
                audit("PROJECT_STATUS_CHANGED", "Operator [" + who + "] marked status \"" + names.get(k) + "\" as COMPLETE on project: " + pid, who, doneAt);
            }
            statusRepository.save(ProjectStatus.builder().projectId(pid).statusName(names.get(k)).cost(BigDecimal.ZERO)
                    .isCustom(false).isCompleted(done).displayOrder(order++).completedAt(doneAt).completedBy(who).createdAt(entryAt).build());
        }
        int ci = 0;
        for (ScenarioData.Custom c : s.custom) {
            LocalDateTime addedAt = at(Math.max(0, span / 2), s.key + "C" + ci);
            LocalDateTime doneAt = c.done ? addedAt.plusDays(3).isAfter(now) ? now.minusMinutes(10) : addedAt.plusDays(3) : null;
            statusRepository.save(ProjectStatus.builder().projectId(pid).statusName(c.name).cost(BigDecimal.valueOf(c.cost))
                    .isCustom(true).isCompleted(c.done).displayOrder(order++).completedAt(doneAt).completedBy(c.done ? ScenarioData.MGR2 : null).createdAt(addedAt).build());
            audit("PROJECT_STATUSES_ATTACHED", "Operator [" + ScenarioData.MGR2 + "] attached 1 status(es) to project: " + pid, ScenarioData.MGR2, addedAt);
            if (c.done) audit("PROJECT_STATUS_CHANGED", "Operator [" + ScenarioData.MGR2 + "] marked status \"" + c.name + "\" as COMPLETE on project: " + pid, ScenarioData.MGR2, doneAt);
            ci++;
        }
    }

    // ---- payments ------------------------------------------------------
    // fix167: each payment says which owner paid and whether it was for the TITLE or STORAGE fees; reversed payments
    // get their negative REVERSAL line; the receipt document is linked to its payment.
    private void seedPayments(ScenarioData.Spec s, UUID pid, String index, String lbl, String owner1, String staff) {
        List<ScenarioData.Pay> ordered = new ArrayList<>(s.pays);
        ordered.sort((a, b) -> Integer.compare(s.payAgo(b), s.payAgo(a)));
        long running = 0;
        for (ScenarioData.Pay p : ordered) {
            int ago = s.payAgo(p);
            String by = p.by != null ? p.by : staff;
            String type = s.payType(p);
            running += p.amount;
            long costEff = s.cost + ("CAPITALIZE".equals(s.exit) && ago <= s.exitAgo ? s.feesNet() : 0);
            long fees = s.paidWhileReceivable(p) ? s.feesAt(ago) : 0;
            long after = Math.max(0, costEff + fees - running);
            LocalDateTime t = at(ago, s.key + p.amount + p.ago);
            String notes = p.note != null ? p.note : "Payment received";
            Client payer = clients.get(p.payer != null ? p.payer : s.owners[0]);
            String kind = p.storage ? "Storage Fee" : "Title Payment";
            ProjectDocument receipt = null;
            if (p.receipt || p.ago >= 0) {
                boolean photo = Math.abs((s.key + p.amount).hashCode()) % 3 == 0;
                String fname = "Receipt - " + kind + " - UGX " + p.amount + " - " + t.toLocalDate() + (photo ? ".jpg" : ".pdf");
                receipt = addDocument(pid, index, ScenarioData.PR, fname, photo ? "image/jpeg" : "application/pdf", by, t.plusMinutes(4));
            }
            PaymentRecord saved = paymentRepository.save(PaymentRecord.builder().projectId(pid).amountPaid(BigDecimal.valueOf(p.amount))
                    .paymentType(type).recordedBy(by).notes(notes).timestamp(t).balanceAfter(BigDecimal.valueOf(after))
                    .allocation(p.storage ? "STORAGE" : "TITLE").payerClientId(payer.getId()).payerName(payer.getFullName())
                    .receiptDocumentId(receipt != null ? receipt.getId() : null).build());
            if (p.ago >= 0) {
                audit("PAYMENT_RECORDED", "Operator [" + by + "] recorded UGX " + p.amount + " for plot: " + lbl + " | Type: " + type
                        + " | For: " + (p.storage ? "STORAGE" : "TITLE") + " | Paid by: " + payer.getFullName() + " | Amount owed after: UGX " + after, by, t);
                recoveryNoteRepository.save(RecoveryNote.builder().client(payer).author(null).tag("payment received").tone("INFO")
                        .countsAsAttempt(false).text("Paid UGX " + p.amount + " on " + t.toLocalDate() + (p.storage ? " (storage fees)" : "")).createdAt(t).build());
                if ("RECEIVABLE_PARTIAL".equals(type)) {
                    bell("PAYMENT_ON_RECEIVABLE", "POSITIVE", "Payment UGX " + p.amount + " received on " + lbl + ".", "PROJECT", pid, "ROLE_DIRECTOR", t);
                }
            }
            if (p.reversed()) {
                running -= p.amount;
                LocalDateTime rt = at(p.reversedAgo, s.key + "REV" + p.amount);
                paymentRepository.save(PaymentRecord.builder().projectId(pid).amountPaid(BigDecimal.valueOf(-p.amount))
                        .paymentType("REVERSAL").recordedBy(p.reverseBy).notes("[REVERSAL OF " + saved.getId() + "] " + p.reverseWhy)
                        .timestamp(rt).balanceAfter(BigDecimal.valueOf(after + p.amount))
                        .allocation(p.storage ? "STORAGE" : "TITLE").payerClientId(payer.getId()).payerName(payer.getFullName()).build());
                audit("PAYMENT_REVERSED", "Operator [" + p.reverseBy + "] reversed UGX " + p.amount + " on " + lbl + ". Reason: " + p.reverseWhy, p.reverseBy, rt);
            }
        }
    }

    // ---- receivable history -------------------------------------------
    private void seedReceivableHistory(ScenarioData.Spec s, UUID pid, String index, String lbl, String owner1, long debt) {
        if (s.recvAgo < 0) return;
        String admin = ScenarioData.DIRECTOR;
        LocalDateTime start = at(s.recvAgo, s.key + "R");

        if (s.auto365) {
            audit("AUTO_RECEIVABLE", "SYSTEM: Plot " + owner1 + " auto-flagged as RECEIVABLE after 365 days of no payment. Debt frozen at: UGX " + debt, "SYSTEM", start);
            bell("AUTO_RECEIVABLE_365", "WARN", owner1 + " auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", pid, "ROLE_DIRECTOR", start);
        } else if (!s.recvAtIntake) {
            audit("RECEIVABLE_TRIGGER", "Operator [" + admin + "] manually moved plot " + lbl + " to RECEIVABLE. Original debt frozen at: UGX " + debt, admin, start);
        }
        if (s.startOverride) {
            audit("RECEIVABLE_START_OVERRIDDEN", "Operator [" + ScenarioData.ADMIN + "] set receivable start date to " + start.toLocalDate() + " for plot: " + lbl, ScenarioData.ADMIN, at(s.entry(), s.key + "V"));
        }
        if (s.customRate) {
            audit("RECEIVABLE_SETTINGS", "Operator [" + admin + "] updated receivable settings on #" + index + " (monthly rate: default -> UGX " + s.rate
                    + "). Reason: Agreed with the client.", admin, start.plusDays(1).isAfter(now) ? start : start.plusDays(1));
        }
        if (s.activePause()) {
            LocalDateTime t = at(s.pauseAgo, s.key + "Z");
            String date = s.deadlineIn != null ? now.toLocalDate().plusDays(s.deadlineIn).toString() : "no end date";
            audit("RECEIVABLE_SETTINGS", "Operator [" + admin + "] updated receivable settings on #" + index + " (fees paused until: not paused -> " + date + "). Reason: Client is negotiating.", admin, t);
            if (s.deadlineIn != null && s.deadlineIn <= 4) {
                bell("NEGOTIATION_DEADLINE", "WARN", "Negotiation deadline for " + lbl + " is within 3 days.", "PROJECT", pid, "ROLE_MANAGER", at(1, s.key + "W"));
            }
        }
        if (s.pastPauseFrom >= 0) {
            audit("RECEIVABLE_SETTINGS", "Operator [" + admin + "] updated receivable settings on #" + index + " (fees paused until: not paused -> "
                    + now.toLocalDate().minusDays(s.pastPauseTo) + "). Reason: Client is negotiating.", admin, at(s.pastPauseFrom, s.key + "PP"));
            audit("STORAGE_FEE_RESUMED", "SYSTEM: Storage-fee pause ended on " + now.toLocalDate().minusDays(s.pastPauseTo) + " for " + owner1
                    + ". Billing restarts; the paused days are not charged.", "SYSTEM", at(s.pastPauseTo, s.key + "PE"));
        }
        for (ScenarioData.Reduce r : s.reductions) {
            LocalDateTime t = at(r.ago, s.key + "RD" + r.amount);
            audit("FEES_REDUCED", "Operator [" + admin + "] reduced storage fees on #" + index + " by UGX " + r.amount + ". Reason: " + r.why, admin, t);
        }

        // the nightly job's monthly bills (fix167: counted from the billing clock, which a finished pause moved forward)
        int endAgo = s.exit == null ? (s.activePause() ? s.pauseAgo : 0) : s.exitAgo;
        int clock = s.exit == null ? s.clockAgo() : s.recvAgo;
        long total = s.initFee;
        for (int m = 1; m <= Math.max(0, s.billed); m++) {
            int ago = clock - 30 * m;
            if (ago < endAgo) break;
            total += s.rate;
            LocalDateTime t = at(ago, s.key + "F" + m);
            audit("STORAGE_FEE_APPLIED", "SYSTEM: Added UGX " + s.rate + " monthly storage fee to receivable plot: " + owner1
                    + " (1 month(s) x UGX " + s.rate + ") | Total accumulated fees: UGX " + total, "SYSTEM", t);
            bell("STORAGE_FEE_APPLIED", "INFO", "Storage fee UGX " + s.rate + " added to " + owner1 + ".", "PROJECT", pid, "ROLE_DIRECTOR", t);
        }

        if (s.exit != null) {
            LocalDateTime t = at(s.exitAgo, s.key + "E");
            long fees = s.feesNet();
            switch (s.exit) {
                case "PAID_OFF":
                    audit("RECEIVABLE_EXIT", "Operator [" + ScenarioData.DIRECTOR + "] - Plot " + lbl + " EXITED RECEIVABLE after full payment clearance.", ScenarioData.DIRECTOR, t.plusMinutes(1));
                    break;
                case "WAIVE":
                    audit("FEES_WAIVED", "Operator [" + admin + "] waived UGX " + (fees - s.storagePaid()) + " of unpaid storage fees on #" + index + ". Reason: Settlement agreed with the client.", admin, t);
                    break;
                case "CAPITALIZE":
                    audit("FEES_CAPITALIZED", "Operator [" + admin + "] capitalized UGX " + fees + " of storage fees into total cost on #" + index + ". Reason: Client will pay the fees with the balance.", admin, t);
                    break;
                default:
                    audit("RECEIVABLE_SET_ASIDE", "Operator [" + admin + "] set aside #" + index + " (UGX " + s.storedFees() + " of unpaid fees kept, billing stopped). Reason: Court case pending.", admin, t);
            }
        }
    }

    // ---- recovery calls ------------------------------------------------
    private void seedCalls() {
        Map<String, List<ScenarioData.Call>> byPerson = new LinkedHashMap<>();
        for (ScenarioData.Call c : ScenarioData.calls()) byPerson.computeIfAbsent(c.person, k -> new ArrayList<>()).add(c);
        for (Map.Entry<String, List<ScenarioData.Call>> e : byPerson.entrySet()) {
            Client client = clients.get(e.getKey());
            List<ScenarioData.Call> list = e.getValue();
            list.sort((a, b) -> Integer.compare(b.ago, a.ago)); // oldest first
            List<Integer> goodAgo = new ArrayList<>();
            List<Integer> missAgo = new ArrayList<>();
            for (ScenarioData.Call c : list) {
                boolean positive = ScenarioData.ANS.equals(c.tag);
                LocalDateTime t = at(c.ago, c.person + c.tag);
                recoveryNoteRepository.save(RecoveryNote.builder().client(client).author(users.get(c.by)).tag(c.tag)
                        .tone(positive ? "POSITIVE" : "NEGATIVE").countsAsAttempt(true).text(c.text).createdAt(t).build());
                audit("RECOVERY_NOTE", "RECOVERY_NOTE: " + c.tag + " (NIN " + client.getNationalId() + ")", c.by, t);
                if (positive) goodAgo.add(c.ago); else missAgo.add(c.ago);
                // what the app would have seen on the day of this call (rolling 30 days)
                int good30 = 0, miss30 = 0;
                for (int g : goodAgo) if (g - c.ago >= 0 && g - c.ago <= 30) good30++;
                for (int m : missAgo) if (m - c.ago >= 0 && m - c.ago <= 30) miss30++;
                if (positive && good30 == 2) {
                    LocalDateTime unlock = t.plusDays(30);
                    bell("LOCKED", "INFO", client.getFullName() + " had 2 good calls. Rest until " + unlock.toLocalDate() + ".", "CLIENT", client.getId(),
                            users.get(c.by).getRole().name(), t);
                    if (unlock.isBefore(now)) {
                        bell("UNLOCK", "INFO", client.getFullName() + " is callable again.", "CLIENT", client.getId(), "ROLE_SECRETARY", unlock);
                        bell("UNLOCK_M", "INFO", client.getFullName() + " is callable again.", "CLIENT", client.getId(), "ROLE_MANAGER", unlock);
                    }
                }
                if (!positive && miss30 == 2 && good30 == 0) {
                    bell("SITE_VISIT_AUTO", "WARN", client.getFullName() + " missed twice with no answer in 30 days. Plan a site visit.", "CLIENT", client.getId(), "ROLE_MANAGER", t);
                }
            }
        }
    }

    // ---- expenses ------------------------------------------------------
    private void seedExpenses() {
        String[] presets = { "Fuel", "Rent", "Salaries", "Airtime & Data", "Vehicle Repairs" };
        for (String p : presets) {
            if (!presetRepository.existsByNameIgnoreCase(p)) {
                presetRepository.save(ExpensePreset.builder().name(p).createdBy(ScenarioData.DIRECTOR).createdAt(at(300, p)).build());
            }
        }
        for (ScenarioData.Exp x : ScenarioData.expenses()) {
            LocalDateTime t = now.minusMinutes(x.minutesAgo);
            Expense saved = expenseRepository.save(Expense.builder().category(x.category).amount(BigDecimal.valueOf(x.amount)).note(x.note)
                    .recordedBy(x.by).spentBy(x.spentBy).createdAt(t)
                    .editedAt(x.editedMinutesAgo > 0 ? now.minusMinutes(x.editedMinutesAgo) : null)
                    .editedBy(x.editedBy).build());
            audit("EXPENSE_LOGGED", "Operator [" + x.by + "] logged expense: " + x.category + " -- UGX " + x.amount
                    + (x.spentBy != null ? " (spent by " + x.spentBy + ")" : ""), x.by, t);
            bell("EXPENSE_LOGGED", "INFO", "Expense UGX " + x.amount + " on " + x.category + " logged by " + x.by + ".", "EXPENSE", saved.getId(), "ROLE_DIRECTOR", t);
            if (x.editedMinutesAgo > 0) {
                LocalDateTime et = now.minusMinutes(x.editedMinutesAgo);
                audit("EXPENSE_EDITED", "Operator [" + x.editedBy + "] edited expense (originally logged by " + x.by + "): " + x.category + " UGX 830000 -> " + x.category + " UGX " + x.amount, x.editedBy, et);
                bell("EXPENSE_EDITED", "WARN", "Expense corrected: " + x.category + " UGX 830000 changed to " + x.category + " UGX " + x.amount + " by " + x.editedBy + ".", "EXPENSE", saved.getId(), "ROLE_DIRECTOR", et);
            }
        }
    }

    // ---- bell read marks -------------------------------------------------
    /** The bell should not open with 300 unread rows: anything older than 3 days counts as read by the root account. */
    private void seedBellReads() {
        User root = userRepository.findByUsername(ScenarioData.ROOT).orElse(null);
        if (root == null) return;
        notificationRepository.saveAll(bell);
        List<NotificationRead> reads = new ArrayList<>();
        for (Notification n : bell) {
            if (n.getCreatedAt().isBefore(now.minusDays(3))) {
                reads.add(NotificationRead.builder().notificationId(n.getId()).userId(root.getId()).readAt(n.getCreatedAt().plusHours(2).isAfter(now) ? now : n.getCreatedAt().plusHours(2)).build());
            }
        }
        notificationReadRepository.saveAll(reads);
        bell.clear();
    }
}
