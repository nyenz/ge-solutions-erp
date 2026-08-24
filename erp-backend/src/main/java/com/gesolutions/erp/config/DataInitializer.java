// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");

        // Run schema migrations via raw JDBC -- never touches JPA/Hibernate session
        runSchemaMigrations();

        // Seed root user if missing
        seedRootUser();

        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        // EXPENSES REBUILD: Seed the default expense presets if empty
        seedDefaultExpensePresets();

        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    // NOTE: Deliberately NOT @Transactional -- same raw-JDBC-safety reasoning
    // as seedRootUser() below. Only seeds if the table is completely empty,
    // so it never overwrites presets a Manager has already created.
    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) {
            System.out.println(">>> [EXPENSES] Presets already exist, skipping default seed.");
            return;
        }
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) {
            expensePresetRepository.save(ExpensePreset.builder()
                    .name(name)
                    .createdBy("SYSTEM")
                    .build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",

            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",

            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            // PHASE 2 - NIN-BASED IDENTITY
            // Phone numbers are no longer required to be unique -- joint owners or
            // family members can share one phone. NIN is now the real identity check.
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",

            // PHASE C - FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.4)
            // national_id becomes a TRUE mandatory, unique column. The old
            // "ADD CONSTRAINT UNIQUE" line above this comment (removed) had been
            // silently failing on every boot since Phase 2 -- the blanket
            // try/catch below logs any failure as "already exists" whether that
            // was true or not, and there was nothing upstream cleaning duplicate
            // or blank values first. These four steps run in order, each one
            // guarded so it is a no-op once already applied -- same repeatable,
            // safe-on-every-boot pattern as the district/county and projectIndex
            // backfills above.
            //
            // Step 1: blank-string NINs are not the same as a real NULL -- fold
            // them in first so step 3 catches them too.
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            //
            // Step 2: disambiguate any rows that already share a duplicate NIN
            // (possible from before this was ever enforced) -- keep the oldest
            // row's value untouched, suffix every later duplicate with its own
            // id so the unique constraint below has something valid to apply to.
            // Naturally idempotent: once every value is distinct, ROW_NUMBER()
            // never produces rn > 1 for the same national_id again.
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            //
            // Step 3: legacy rows created before Phase 2 may still have a blank
            // national_id (per the old Client.java comment, "blank until next
            // edited") -- a real NOT NULL constraint cannot coexist with actual
            // NULLs, so give each one a unique placeholder. Naturally idempotent:
            // once set, national_id is no longer NULL so the WHERE clause skips it.
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            //
            // Step 4: now safe to apply both constraints for real. SET NOT NULL is
            // itself idempotent in Postgres (no error re-running it once already
            // set). The UNIQUE constraint is wrapped in a DO block guarded by a
            // pg_constraint lookup, so once it exists every later boot silently
            // no-ops and logs OK instead of a red "already exists" skip.
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",

            // EXPENSES REBUILD -- flat cash-out log, replaces the old
            // committed/paid CompanyExpense model for new entries. The old
            // company_expenses table is left untouched (deprecated, not
            // deleted) so nothing already recorded there is lost.
            "CREATE TABLE IF NOT EXISTS expense_presets (" +
                "id UUID PRIMARY KEY, " +
                "name VARCHAR(100) NOT NULL UNIQUE, " +
                "created_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (" +
                "id UUID PRIMARY KEY, " +
                "category VARCHAR(150) NOT NULL, " +
                "amount NUMERIC(15,2) NOT NULL, " +
                "note TEXT, " +
                "recorded_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now(), " +
                "edited_at TIMESTAMP, " +
                "edited_by VARCHAR(100))",
            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",

            // STAGE 3 -- SOFT DELETE
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",

            // PHASE A -- FOLDER-TO-TITLE REDESIGN (Section 18.10)
            // landTitle becomes optional on LandProject (see model change),
            // and location fields move up so they are permanent even for
            // titleless folder-stage projects.
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            // Backfill: copy existing district/county from land_titles up to
            // their parent land_projects row via the title_id FK. The
            // "lp.district IS NULL" guard makes this safe to run on every
            // boot -- once a row has been backfilled its district is no
            // longer NULL, so this becomes a no-op for it from then on.
            // land_titles.district/county are left in place (deprecated,
            // not dropped) so this UPDATE is repeatable and non-destructive.
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",

            // PHASE B -- FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.3)
            // projectIndex moves up to LandProject: Section 18.3 requires it
            // be assigned at LandProject creation, before any title exists,
            // and Phase B's null-safe audit-log fallback needs it to exist
            // even when landTitle does not. land_titles.project_index is
            // left in place (deprecated, not dropped).
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            // Backfill: copy each project's existing projectIndex up from
            // its LandTitle via the title_id FK. Same "IS NULL" guard as
            // the district/county backfill above -- safe on every boot,
            // no-op once already copied.
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",

            // PHASE F -- FOLDER-TO-TITLE REDESIGN (Section 18.10)
            // Make plot_number nullable so bulk title-produced action can
            // attach an empty LandTitle record to unlock fields before
            // the unique plot numbers are known.
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
        };

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    // Column already exists or similar -- safe to ignore
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }

        } catch (Exception e) {
            // If we can't get a connection, log and continue -- don't kill startup
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is
    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,
    // EntityManager flush timing, and @Builder.Default field conflicts.
    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);

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

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
