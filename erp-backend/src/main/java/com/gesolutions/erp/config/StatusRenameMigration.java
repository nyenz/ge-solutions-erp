// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/StatusRenameMigration.java
package com.gesolutions.erp.config;

import org.springframework.boot.autoconfigure.orm.jpa.EntityManagerFactoryDependsOnPostProcessor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.Statement;

/**
 * fix180: "Stage" is now "Status" everywhere, database included:
 *   stage_templates  -> status_templates   (stage_name -> status_name)
 *   project_stages   -> project_statuses   (stage_name -> status_name)
 *   land_projects.current_stage_index -> current_status_index
 *
 * This MUST run before Hibernate starts: with ddl-auto=update Hibernate would otherwise create new EMPTY tables and
 * columns for the new names and leave every existing row behind in the old ones (the trap described for the
 * is_backlog columns). The EntityManagerFactory is made to wait for this bean. Every step checks first, so a second
 * start does nothing; a failed step is printed and never stops the server.
 */
@Configuration
public class StatusRenameMigration {

    @Bean(name = "statusRenameMigrator")
    public Object statusRenameMigrator(DataSource dataSource) {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            DatabaseMetaData md = c.getMetaData();
            renameTable(md, st, "stage_templates", "status_templates");
            renameTable(md, st, "project_stages", "project_statuses");
            renameColumn(md, st, "status_templates", "stage_name", "status_name");
            renameColumn(md, st, "project_statuses", "stage_name", "status_name");
            renameColumn(md, st, "land_projects", "current_stage_index", "current_status_index");
            if (tableExists(md, "project_statuses")) {
                run(st, "ALTER INDEX IF EXISTS idx_project_stage_project RENAME TO idx_project_status_project");
            }
        } catch (Exception e) {
            System.err.println(">>> [STATUS_RENAME] skipped: " + e.getMessage());
        }
        return Boolean.TRUE;
    }

    @Bean
    public static EntityManagerFactoryDependsOnPostProcessor statusRenameBeforeHibernate() {
        return new EntityManagerFactoryDependsOnPostProcessor("statusRenameMigrator");
    }

    private static void renameTable(DatabaseMetaData md, Statement st, String from, String to) throws Exception {
        if (tableExists(md, from) && !tableExists(md, to)) {
            run(st, "ALTER TABLE " + from + " RENAME TO " + to);
        }
    }

    private static void renameColumn(DatabaseMetaData md, Statement st, String table, String from, String to) throws Exception {
        if (tableExists(md, table) && columnExists(md, table, from) && !columnExists(md, table, to)) {
            run(st, "ALTER TABLE " + table + " RENAME COLUMN " + from + " TO " + to);
        }
    }

    private static boolean tableExists(DatabaseMetaData md, String name) throws Exception {
        for (String n : new String[] { name, name.toUpperCase() }) {
            try (ResultSet rs = md.getTables(null, null, n, new String[] { "TABLE" })) {
                if (rs.next()) return true;
            }
        }
        return false;
    }

    private static boolean columnExists(DatabaseMetaData md, String table, String column) throws Exception {
        for (String[] n : new String[][] { { table, column }, { table.toUpperCase(), column.toUpperCase() } }) {
            try (ResultSet rs = md.getColumns(null, null, n[0], n[1])) {
                if (rs.next()) return true;
            }
        }
        return false;
    }

    private static void run(Statement st, String sql) {
        try {
            st.execute(sql);
            System.out.println(">>> [STATUS_RENAME] " + sql);
        } catch (Exception e) {
            System.err.println(">>> [STATUS_RENAME] failed: " + sql + " -- " + e.getMessage());
        }
    }
}
