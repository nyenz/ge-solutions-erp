// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notification/service/NotificationTypes.java
package com.gesolutions.erp.modules.notification.service;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * fix181 (17.1, 17.2): THE ONE LIST of bell alerts. Each type says its group, default severity, how often it may repeat
 * and WHO gets it (one row per audience role, exact role match; there is no "ALL" any more, 17.5).
 * The Employee is never in an audience (17.0b). The Admin (the designer) gets only SYSTEM, STAFF and BOOKS_MISMATCH.
 * The page catalog (erp-frontend notification catalog) must have an entry for every code here.
 */
public final class NotificationTypes {

    private NotificationTypes() {}

    public enum Group { MONEY, PIPELINE, RECOVERY, STAFF, SYSTEM }

    /**
     * EVERY_TIME: written each time. ONCE_PER_ENTITY: never again for the same thing and role.
     * ONCE_PER_DAY: at most once a day per thing and role. ONCE_PER_EVENT_DATE: once per thing + a date the caller gives
     * (for example the day a project went into receivables), so a second, later event is not silenced.
     */
    public enum Repeat { EVERY_TIME, ONCE_PER_ENTITY, ONCE_PER_DAY, ONCE_PER_EVENT_DATE }

    public record Type(String code, Group group, String severity, Repeat repeat, List<String> audience) {}

    private static final String DIR = "ROLE_DIRECTOR";
    private static final String ADM = "ROLE_ADMIN";
    private static final String MGR = "ROLE_MANAGER";
    private static final String SEC = "ROLE_SECRETARY";

    private static final Map<String, Type> TYPES = new LinkedHashMap<>();

    private static void add(String code, Group g, String severity, Repeat r, String... audience) {
        TYPES.put(code, new Type(code, g, severity, r, List.of(audience)));
    }

    static {
        // MONEY
        add("PAYMENT_ON_RECEIVABLE", Group.MONEY, "POSITIVE", Repeat.EVERY_TIME, DIR);
        add("PAYMENT_REVERSED",      Group.MONEY, "WARN",     Repeat.EVERY_TIME, DIR);
        add("COST_CHANGED",          Group.MONEY, "WARN",     Repeat.EVERY_TIME, DIR);
        add("FEES_REDUCED",          Group.MONEY, "WARN",     Repeat.EVERY_TIME, DIR);
        add("RECEIVABLE_EXIT",       Group.MONEY, "POSITIVE", Repeat.EVERY_TIME, DIR);
        add("STORAGE_FEE_APPLIED",   Group.MONEY, "INFO",     Repeat.ONCE_PER_DAY, DIR);
        add("EXPENSE_LOGGED",        Group.MONEY, "INFO",     Repeat.EVERY_TIME, DIR);
        add("EXPENSE_EDITED",        Group.MONEY, "WARN",     Repeat.EVERY_TIME, DIR);
        add("EXPENSE_DELETED",       Group.MONEY, "WARN",     Repeat.EVERY_TIME, DIR);
        add("BOOKS_MISMATCH",        Group.MONEY, "CRITICAL", Repeat.ONCE_PER_DAY, DIR, ADM);
        // PIPELINE
        add("PENDING_CREATED",       Group.PIPELINE, "INFO",     Repeat.ONCE_PER_ENTITY, SEC, MGR);
        add("NEW_INTAKE",            Group.PIPELINE, "INFO",     Repeat.ONCE_PER_ENTITY, MGR);
        add("STATUS_ADVANCED",       Group.PIPELINE, "POSITIVE", Repeat.EVERY_TIME, MGR);
        add("DOC_UPLOADED",          Group.PIPELINE, "INFO",     Repeat.EVERY_TIME, MGR);
        add("TITLE_COMPLETED",       Group.PIPELINE, "POSITIVE", Repeat.EVERY_TIME, DIR);
        add("TITLE_RELEASE_UNDONE",  Group.PIPELINE, "WARN",     Repeat.EVERY_TIME, DIR);
        add("PROBLEM_FLAGGED",       Group.PIPELINE, "CRITICAL", Repeat.EVERY_TIME, SEC, MGR, DIR);
        add("PROBLEM_CLEARED",       Group.PIPELINE, "POSITIVE", Repeat.EVERY_TIME, DIR);
        add("PROJECT_DELETED",       Group.PIPELINE, "CRITICAL", Repeat.EVERY_TIME, DIR, ADM);
        add("PROJECT_RESTORED",      Group.PIPELINE, "POSITIVE", Repeat.EVERY_TIME, DIR);
        add("AUTO_RECEIVABLE_365",   Group.PIPELINE, "WARN",     Repeat.ONCE_PER_EVENT_DATE, DIR);
        add("PENDING_STALE",         Group.PIPELINE, "WARN",     Repeat.ONCE_PER_EVENT_DATE, SEC, MGR);
        add("NEGOTIATION_DEADLINE",  Group.PIPELINE, "WARN",     Repeat.ONCE_PER_EVENT_DATE, MGR);
        // RECOVERY
        add("LOCKED",                Group.RECOVERY, "INFO", Repeat.EVERY_TIME, SEC, MGR);
        add("UNLOCK",                Group.RECOVERY, "INFO", Repeat.ONCE_PER_EVENT_DATE, SEC, MGR);
        add("SITE_VISIT_AUTO",       Group.RECOVERY, "WARN", Repeat.EVERY_TIME, SEC, MGR, DIR);
        add("NIN_CONFLICT",          Group.RECOVERY, "WARN", Repeat.ONCE_PER_DAY, SEC, MGR);
        // STAFF
        add("STAFF_PROVISIONED",     Group.STAFF, "INFO",     Repeat.EVERY_TIME, DIR, ADM);
        add("STAFF_ROLE_CHANGED",    Group.STAFF, "WARN",     Repeat.EVERY_TIME, DIR, ADM);
        add("STAFF_SUSPENDED",       Group.STAFF, "WARN",     Repeat.EVERY_TIME, DIR, ADM);
        add("STAFF_ACTIVATED",       Group.STAFF, "POSITIVE", Repeat.EVERY_TIME, DIR, ADM);
        add("KEY_RESET",             Group.STAFF, "WARN",     Repeat.EVERY_TIME, DIR, ADM);
        // SYSTEM
        add("SYSTEM_WIPE",           Group.SYSTEM, "CRITICAL", Repeat.EVERY_TIME, DIR, ADM);
        add("LOGIN_BLOCKED",         Group.SYSTEM, "WARN",     Repeat.EVERY_TIME, DIR, ADM);
    }

    /** Old rows may still carry these; nothing writes them any more (UNLOCK_M became UNLOCK with two audience rows). */
    public static final List<String> RETIRED = List.of("UNLOCK_M");

    public static Type of(String code) { return code == null ? null : TYPES.get(code); }

    public static Map<String, Type> all() { return Collections.unmodifiableMap(TYPES); }
}
