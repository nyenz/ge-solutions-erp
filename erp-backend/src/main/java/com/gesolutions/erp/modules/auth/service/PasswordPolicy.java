// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/PasswordPolicy.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.common.exception.BusinessException;

import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * fix279: the ONE place that says what a new key must look like (own key change and owner recovery both use it).
 */
public final class PasswordPolicy {

    private PasswordPolicy() { }

    /** Throws a BusinessException with a plain sentence when the new key is not allowed. */
    public static void check(String np, String username) {
        if (np == null || np.length() < 8) {
            throw new BusinessException("PASSWORD_POLICY: The new key needs at least 8 characters.");
        }
        if (np.getBytes(StandardCharsets.UTF_8).length > 72) {
            throw new BusinessException("PASSWORD_POLICY: The new key is too long (at most 72 characters).");
        }
        if (np.chars().noneMatch(Character::isUpperCase) || np.chars().noneMatch(Character::isDigit)) {
            throw new BusinessException("PASSWORD_POLICY: The new key needs at least one capital letter and one number.");
        }
        if (username != null && np.toLowerCase(Locale.ROOT).contains(username.toLowerCase(Locale.ROOT))) {
            throw new BusinessException("PASSWORD_POLICY: The new key must not contain your username.");
        }
        if (np.toUpperCase(Locale.ROOT).startsWith("NY-")) {
            throw new BusinessException("PASSWORD_POLICY: Choose your own key, not one that looks like a temporary key.");
        }
    }
}
