// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/LoginRateLimiter.java
package com.gesolutions.erp.config;

import org.springframework.stereotype.Component;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Simple in-memory rate limiter for the login endpoint.
 * Blocks an IP for 15 minutes after 10 failed attempts.
 */
@Component
public class LoginRateLimiter {

    private static final int  MAX_ATTEMPTS  = 10;
    private static final long BLOCK_SECONDS = 10 * 60; // 10 minutes

    private final ConcurrentHashMap<String, int[]> attempts = new ConcurrentHashMap<>();
    // int[0] = count, int[1] = first-attempt epoch-second

    public boolean isBlocked(String ip) {
        int[] entry = attempts.get(ip);
        if (entry == null) return false;
        long elapsed = Instant.now().getEpochSecond() - entry[1];
        if (elapsed > BLOCK_SECONDS) {
            attempts.remove(ip);
            return false;
        }
        return entry[0] >= MAX_ATTEMPTS;
    }

    public void recordFailure(String ip) {
        attempts.compute(ip, (k, v) -> {
            if (v == null) return new int[]{ 1, (int) Instant.now().getEpochSecond() };
            long elapsed = Instant.now().getEpochSecond() - v[1];
            if (elapsed > BLOCK_SECONDS) return new int[]{ 1, (int) Instant.now().getEpochSecond() };
            return new int[]{ v[0] + 1, v[1] };
        });
    }

    public void clearRecord(String ip) {
        attempts.remove(ip);
    }
}
