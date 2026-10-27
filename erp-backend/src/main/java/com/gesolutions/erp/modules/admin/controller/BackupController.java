// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/BackupController.java
package com.gesolutions.erp.modules.admin.controller;

import com.gesolutions.erp.common.audit.AuditService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.sql.Types;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * fix268 (David): BACKUP TO MY COMPUTER -- for the root account only.
 *
 * GET  /data   one full copy of every table the app owns (the business tables and the kept ones, see
 *              SystemAdminController). The page turns it into a folder per client (details, projects, payments, notes,
 *              documents) and keeps this copy in DATABASE/ for restoring. Secrets are left out: key hashes and reset
 *              tokens never leave the server (after a restore every person gets a new key).
 * POST /done   the page says the backup was saved: one audit line, and the time is kept for the monthly reminder.
 * GET  /status when the last backup was saved (null = never).
 */
@RestController
@RequestMapping("/api/v1/admin/backup")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ROLE_ADMIN') and authentication.principal.isRoot")
public class BackupController {

    static final String LAST_BACKUP_FLAG = "LAST_BACKUP";
    /** Columns that are never copied out (any table). */
    static final Set<String> SECRET_COLUMNS = Set.of("password", "reset_token", "recovery_code_hash");

    private final DataSource dataSource;
    private final AuditService auditService;

    @GetMapping("/data")
    public ResponseEntity<Map<String, Object>> data() throws Exception {
        List<String> names = new ArrayList<>(SystemAdminController.TABLES_TO_WIPE);
        names.addAll(SystemAdminController.KEPT_ON_PURPOSE);
        Map<String, Object> tables = new LinkedHashMap<>();
        Map<String, Integer> counts = new LinkedHashMap<>();
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String t : names) {
                if (!SystemAdminController.tableExists(conn, t)) continue;
                List<Map<String, Object>> rows = new ArrayList<>();
                try (ResultSet rs = st.executeQuery("SELECT * FROM " + t)) {
                    ResultSetMetaData md = rs.getMetaData();
                    while (rs.next()) {
                        Map<String, Object> row = new LinkedHashMap<>();
                        for (int i = 1; i <= md.getColumnCount(); i++) {
                            String col = md.getColumnLabel(i).toLowerCase(Locale.ROOT);
                            if (SECRET_COLUMNS.contains(col)) continue;
                            row.put(col, value(rs, i, md.getColumnType(i)));
                        }
                        rows.add(row);
                    }
                }
                tables.put(t, rows);
                counts.put(t, rows.size());
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("app", "GE Solutions ERP");
        out.put("format", 1);
        out.put("createdAt", LocalDateTime.now().toString());
        out.put("createdBy", AuditService.currentOperator());
        out.put("counts", counts);
        out.put("tables", tables);
        return ResponseEntity.ok(out);
    }

    /** Numbers and yes/no stay as they are; every other kind (dates, ids, text) is written as text. */
    private static Object value(ResultSet rs, int i, int type) throws java.sql.SQLException {
        switch (type) {
            case Types.BOOLEAN, Types.BIT -> { boolean b = rs.getBoolean(i); return rs.wasNull() ? null : b; }
            case Types.INTEGER, Types.SMALLINT, Types.TINYINT, Types.BIGINT -> { long v = rs.getLong(i); return rs.wasNull() ? null : v; }
            case Types.NUMERIC, Types.DECIMAL, Types.DOUBLE, Types.FLOAT, Types.REAL -> {
                java.math.BigDecimal v = rs.getBigDecimal(i); return v == null ? null : v.toPlainString();
            }
            case Types.BINARY, Types.VARBINARY, Types.LONGVARBINARY, Types.BLOB -> {
                Object o = rs.getObject(i);   // some databases report an id (UUID) as binary
                if (o == null || o instanceof java.util.UUID) return o == null ? null : o.toString();
                byte[] b = rs.getBytes(i); return b == null ? null : java.util.Base64.getEncoder().encodeToString(b);
            }
            default -> { return rs.getString(i); }
        }
    }

    @PostMapping("/done")
    public ResponseEntity<Map<String, Object>> done(@RequestBody(required = false) Map<String, Object> body) {
        String how = body == null ? "" : String.valueOf(body.getOrDefault("mode", ""));
        Object files = body == null ? null : body.get("files");
        Object clients = body == null ? null : body.get("clients");
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            st.execute("CREATE TABLE IF NOT EXISTS app_flags (name VARCHAR(60) PRIMARY KEY, set_at TIMESTAMP)");
            st.execute("DELETE FROM app_flags WHERE name = '" + LAST_BACKUP_FLAG + "'");
            st.execute("INSERT INTO app_flags (name, set_at) VALUES ('" + LAST_BACKUP_FLAG + "', CURRENT_TIMESTAMP)");
        } catch (Exception e) {
            System.err.println(">>> [BACKUP] could not keep the time: " + e.getMessage());
        }
        auditService.logAction("BACKUP_SAVED", "Backup saved to the computer"
                + ("folder".equals(how) ? " (straight into a folder)" : "zip".equals(how) ? " (one ZIP file)" : "")
                + (clients != null ? ": " + clients + " client folders" : "")
                + (files != null ? ", " + files + " files" : "") + ".");
        Map<String, Object> out = new HashMap<>();
        out.put("lastBackupAt", lastBackup());
        return ResponseEntity.ok(out);
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        Map<String, Object> out = new HashMap<>();
        out.put("lastBackupAt", lastBackup());
        return ResponseEntity.ok(out);
    }

    private String lastBackup() {
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            if (!SystemAdminController.tableExists(conn, "app_flags")) return null;
            try (ResultSet rs = st.executeQuery("SELECT set_at FROM app_flags WHERE name = '" + LAST_BACKUP_FLAG + "'")) {
                return rs.next() ? rs.getTimestamp(1).toLocalDateTime().toString() : null;
            }
        } catch (Exception e) { return null; }
    }
}
