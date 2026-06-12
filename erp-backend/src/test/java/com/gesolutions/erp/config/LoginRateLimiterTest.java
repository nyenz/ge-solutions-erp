package com.gesolutions.erp.config;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class LoginRateLimiterTest {

    @Test
    public void testRateLimiterBlocksAfter10Tries() {
        LoginRateLimiter rateLimiter = new LoginRateLimiter();
        String ip = "192.168.1.1";

        for (int i = 0; i < 9; i++) {
            rateLimiter.recordFailure(ip);
            assertFalse(rateLimiter.isBlocked(ip), "Should not be blocked after " + (i + 1) + " attempt(s)");
        }

        rateLimiter.recordFailure(ip);
        assertTrue(rateLimiter.isBlocked(ip), "Should be blocked after 10 attempts");
    }
}
