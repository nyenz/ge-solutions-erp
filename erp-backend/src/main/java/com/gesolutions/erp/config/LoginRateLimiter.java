// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/LoginRateLimiter.java
package com.gesolutions.erp.config;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Locale;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory limiter for sign-in and other key checks (fix181).
 *
 * The office and many phones share ONE internet address, so the old "10 failures per address" rule locked the whole
 * office out after one person's mistakes, and one good sign-in by anybody cleared it. Now:
 *  - per USERNAME + ADDRESS: 8 wrong tries in 15 minutes = wait 15 minutes, counted from the LAST wrong try;
 *    a good sign-in clears only that pair.
 *  - per ADDRESS alone: 60 wrong tries in 15 minutes (stops someone trying many names).
 * It lives in memory, so it resets when the server restarts or sleeps (Render free plan). The audit lines
 * (LOGIN_FAILED, LOGIN_BLOCKED) are the lasting record.
 */
@Component
public class LoginRateLimiter {

    public static final int PAIR_LIMIT = 8;
    public static final int ADDRESS_LIMIT = 60;
    public static final long WINDOW_SECONDS = 15 * 60;

    // value[0] = count, value[1] = last failure (epoch seconds)
    private final ConcurrentHashMap<String, long[]> pairs = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, long[]> addresses = new ConcurrentHashMap<>();

    private static String pairKey(String username, String ip) {
        return (username == null ? "" : username.trim().toLowerCase(Locale.ROOT)) + "|" + ip;
    }

    private static long now() { return Instant.now().getEpochSecond(); }

    private static boolean over(ConcurrentHashMap<String, long[]> map, String key, int limit) {
        long[] v = map.get(key);
        if (v == null) return false;
        if (now() - v[1] > WINDOW_SECONDS) { map.remove(key); return false; }
        return v[0] >= limit;
    }

    private static long count(ConcurrentHashMap<String, long[]> map, String key) {
        return map.compute(key, (k, v) -> {
            long t = now();
            if (v == null || t - v[1] > WINDOW_SECONDS) return new long[]{1, t};
            return new long[]{v[0] + 1, t};
        })[0];
    }

    public boolean isBlocked(String username, String ip) {
        return over(pairs, pairKey(username, ip), PAIR_LIMIT) || over(addresses, ip, ADDRESS_LIMIT);
    }

    /** Counts one failure. Returns true when THIS failure is the one that reached the limit (write LOGIN_BLOCKED once). */
    public boolean recordFailure(String username, String ip) {
        long p = count(pairs, pairKey(username, ip));
        long a = count(addresses, ip);
        return p == PAIR_LIMIT || a == ADDRESS_LIMIT;
    }

    /** Minutes left before this pair may try again (rounded up, at least 1). */
    public long minutesLeft(String username, String ip) {
        long[] v = pairs.get(pairKey(username, ip));
        long[] w = addresses.get(ip);
        long last = Math.max(v == null ? 0 : v[1], w == null ? 0 : w[1]);
        long left = WINDOW_SECONDS - (now() - last);
        return Math.max(1, (left + 59) / 60);
    }

    public void clearRecord(String username, String ip) {
        pairs.remove(pairKey(username, ip));
    }

    // ---- generic counters (old-key checks on the password change, owner recovery requests) ----
    private final ConcurrentHashMap<String, long[]> other = new ConcurrentHashMap<>();

    public boolean isOverLimit(String key, int limit) { return over(other, key, limit); }

    public void recordOther(String key) { count(other, key); }

    public void clearOther(String key) { other.remove(key); }
}
