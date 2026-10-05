package com.gesolutions.erp.config;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** fix181: the limit is per USERNAME + ADDRESS (8 wrong tries), so one person cannot lock the whole office out. */
public class LoginRateLimiterTest {

    @Test
    public void blocksTheUsernameAfterEightWrongTries() {
        LoginRateLimiter rateLimiter = new LoginRateLimiter();
        String ip = "192.168.1.1";
        for (int i = 0; i < 7; i++) {
            assertFalse(rateLimiter.recordFailure("mary", ip));
            assertFalse(rateLimiter.isBlocked("mary", ip), "Should not be blocked after " + (i + 1) + " attempt(s)");
        }
        assertTrue(rateLimiter.recordFailure("mary", ip), "the 8th failure is the one that blocks");
        assertTrue(rateLimiter.isBlocked("mary", ip));
        assertTrue(rateLimiter.isBlocked("MARY ", ip), "the username ignores capitals and spaces");
    }

    @Test
    public void twoPeopleBehindOneAddressDoNotBlockEachOther() {
        LoginRateLimiter rateLimiter = new LoginRateLimiter();
        String ip = "10.0.0.5";
        for (int i = 0; i < 8; i++) rateLimiter.recordFailure("mary", ip);
        assertTrue(rateLimiter.isBlocked("mary", ip));
        assertFalse(rateLimiter.isBlocked("john", ip));
    }

    @Test
    public void aGoodSignInClearsOnlyItsOwnPair() {
        LoginRateLimiter rateLimiter = new LoginRateLimiter();
        String ip = "10.0.0.6";
        for (int i = 0; i < 8; i++) rateLimiter.recordFailure("mary", ip);
        for (int i = 0; i < 5; i++) rateLimiter.recordFailure("john", ip);
        rateLimiter.clearRecord("john", ip);
        assertTrue(rateLimiter.isBlocked("mary", ip));
    }
}
