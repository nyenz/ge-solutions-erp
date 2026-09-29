// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/util/PhoneUtil.java
package com.gesolutions.erp.common.util;

import com.gesolutions.erp.common.exception.BusinessException;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;

/**
 * fix139 -- ONE standard format for phone numbers. Twin of
 * erp-frontend/src/utils/phone.js: keep the two in step.
 *
 * Accepts 0772 123 456, +256772123456, 256772123456, 772123456. Stores
 * +256772123456. Several numbers are joined with " / " (max 3). A foreign
 * number is only accepted when typed with its + country code.
 *
 * To tighten the Uganda prefix check later (e.g. only 70-79 mobiles), change
 * the UG_NSN pattern below -- nowhere else.
 */
public final class PhoneUtil {
    private PhoneUtil() {}

    public static final int MAX_NUMBERS = 3;
    public static final int MAX_LENGTH = 50; // clients.phone_number column size
    private static final String SPLIT = "[/,;\\r\\n]+";
    private static final String UG_NSN = "[734]\\d{8}";
    private static final String HELP = "Use 10 digits like 0772 123 456, or +256 772 123 456.";

    public static String normalizeList(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new BusinessException("PHONE_INVALID: A phone number is required (use / for multiple numbers).");
        }
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (String part : raw.split(SPLIT)) {
            if (part.isBlank()) continue;
            out.add(normalizeOne(part));
        }
        if (out.isEmpty()) {
            throw new BusinessException("PHONE_INVALID: A phone number is required (use / for multiple numbers).");
        }
        if (out.size() > MAX_NUMBERS) {
            throw new BusinessException("PHONE_INVALID: At most " + MAX_NUMBERS + " numbers per person.");
        }
        String joined = String.join(" / ", out);
        if (joined.length() > MAX_LENGTH) {
            throw new BusinessException("PHONE_INVALID: Too many long numbers. Keep to " + MAX_NUMBERS + " or fewer.");
        }
        return joined;
    }

    private static String normalizeOne(String part) {
        String shown = part.trim();
        String s = shown.replaceAll("[\\s\\-.()]", "");
        boolean plus = s.startsWith("+");
        if (plus) s = s.substring(1);
        if (!s.matches("\\d+")) throw bad(shown, "has letters or symbols. " + HELP);
        if (s.startsWith("256") && s.length() == 12) return finishUg(shown, s.substring(3));
        if (plus && s.startsWith("256")) throw bad(shown, "is not a full +256 number (9 digits should follow 256).");
        if (plus) { // a client living abroad: + and their country code
            if (s.length() < 8 || s.length() > 15 || s.charAt(0) == '0' || looksFake(s)) {
                throw bad(shown, "does not look like a real international number.");
            }
            return "+" + s;
        }
        if (s.length() == 10 && s.charAt(0) == '0') return finishUg(shown, s.substring(1));
        if (s.length() == 9 && s.charAt(0) == '7') return finishUg(shown, s);
        throw bad(shown, "is not a valid Uganda number. " + HELP);
    }

    private static String finishUg(String shown, String nsn) {
        if (!nsn.matches(UG_NSN)) throw bad(shown, "is not a valid Uganda mobile or landline number. " + HELP);
        if (looksFake(nsn)) throw bad(shown, "looks like a made-up number. Please enter the real number.");
        return "+256" + nsn;
    }

    private static BusinessException bad(String shown, String why) {
        return new BusinessException("PHONE_INVALID: \"" + shown + "\" " + why);
    }

    /** 6+ of the same digit in a row, or a run of 7+ counting up / down. */
    private static boolean looksFake(String d) {
        int rep = 1, up = 1, down = 1;
        for (int i = 1; i < d.length(); i++) {
            int a = d.charAt(i - 1), b = d.charAt(i);
            rep = (a == b) ? rep + 1 : 1;
            up = (b == a + 1) ? up + 1 : 1;
            down = (b == a - 1) ? down + 1 : 1;
            if (rep >= 6 || up >= 7 || down >= 7) return true;
        }
        return false;
    }

    /**
     * Every way staff might type a stored number, for search. Never throws,
     * so old-format numbers in the database are searchable too.
     */
    public static List<String> searchForms(String raw) {
        List<String> forms = new ArrayList<>();
        if (raw == null) return forms;
        for (String part : raw.split(SPLIT)) {
            String d = part.replaceAll("[^0-9]", "");
            if (d.isEmpty()) continue;
            forms.add(d);
            String nsn = null;
            if (d.startsWith("256") && d.length() == 12) nsn = d.substring(3);
            else if (d.startsWith("0") && d.length() == 10) nsn = d.substring(1);
            else if (d.length() == 9 && d.startsWith("7")) nsn = d;
            if (nsn != null) {
                forms.add("0" + nsn);
                forms.add("256" + nsn);
                forms.add("+256" + nsn);
            }
        }
        return forms;
    }
}
