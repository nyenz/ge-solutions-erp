// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/util/DeleteReason.java
package com.gesolutions.erp.common.util;

import com.gesolutions.erp.common.exception.BusinessException;

/**
 * fix223 (David): every delete of something saved asks WHY. The reason is checked here (the page asks too, but the
 * server is the one that cannot be skipped) and written into the audit line and, where there is a project, its Notes.
 */
public final class DeleteReason {
    private DeleteReason() {}

    public static final int MIN = 3;
    public static final int MAX = 500;

    /** The trimmed reason, or an error the page shows next to the reason box. */
    public static String require(String reason) {
        String r = reason == null ? "" : reason.trim().replaceAll("\\s+", " ");
        if (r.length() < MIN) {
            throw new BusinessException("REASON_REQUIRED: Type why this is being deleted (a few words).");
        }
        return r.length() > MAX ? r.substring(0, MAX) : r;
    }

    /** " Reason: ..." for an audit line, or nothing. */
    public static String tail(String reason) {
        return reason == null || reason.isBlank() ? "" : " Reason: " + reason.trim();
    }
}
