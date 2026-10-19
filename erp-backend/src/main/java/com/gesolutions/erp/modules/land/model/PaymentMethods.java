// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentMethods.java
package com.gesolutions.erp.modules.land.model;

import com.gesolutions.erp.common.exception.BusinessException;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * fix214 (David): THE list of payment methods. Keep it in step with erp-frontend/src/utils/paymentMethods.js.
 * OFFICE = cash paid at the office, MOBILE_MONEY, BANK, OTHER (OTHER needs a few words saying how).
 */
public final class PaymentMethods {

    private PaymentMethods() {}

    public static final String OFFICE = "OFFICE";
    public static final String MOBILE_MONEY = "MOBILE_MONEY";
    public static final String BANK = "BANK";
    public static final String OTHER = "OTHER";

    /** code -> the words people see */
    public static final Map<String, String> LABELS = new LinkedHashMap<>();
    static {
        LABELS.put(OFFICE, "Office");
        LABELS.put(MOBILE_MONEY, "Mobile Money");
        LABELS.put(BANK, "Bank");
        LABELS.put(OTHER, "Other");
    }

    public static final int MAX_REFERENCE = 80;

    /** The words for a stored code; old lines (no method) say "Not recorded". */
    public static String label(String code) {
        if (code == null || code.isBlank()) return "Not recorded";
        String l = LABELS.get(code);
        return l != null ? l : code;
    }

    /** The checked method + reference, ready to store. */
    public record Checked(String method, String reference) {}

    /**
     * Checks a method typed on a page. Accepts the code or the words ("Mobile Money", "mobile_money").
     * required = a payment is being saved: an empty method is refused.
     */
    public static Checked check(String method, String reference, boolean required) {
        String ref = reference == null ? null : reference.trim().replaceAll("\\s+", " ");
        if (ref != null && ref.isEmpty()) ref = null;
        if (ref != null && ref.length() > MAX_REFERENCE) {
            throw new BusinessException("PAYMENT_REFERENCE_TOO_LONG: The payment reference can be at most " + MAX_REFERENCE + " characters.");
        }
        String m = method == null ? "" : method.trim().toUpperCase(Locale.ROOT).replace(' ', '_');
        if (m.isEmpty()) {
            if (required) {
                throw new BusinessException("PAYMENT_METHOD_REQUIRED: Pick how the money was paid: Office, Mobile Money, Bank or Other.");
            }
            return new Checked(null, ref);
        }
        if (!LABELS.containsKey(m)) {
            throw new BusinessException("PAYMENT_METHOD_INVALID: The payment method must be Office, Mobile Money, Bank or Other.");
        }
        if (OTHER.equals(m) && (ref == null || ref.length() < 3)) {
            throw new BusinessException("PAYMENT_METHOD_DETAIL_REQUIRED: For Other, write how the money was paid (for example: cheque no. 1042).");
        }
        return new Checked(m, ref);
    }
}
