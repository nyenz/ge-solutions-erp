package com.gesolutions.erp.config;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** fix284 (B5): a real server must refuse to start with the public fallback secrets. */
class StartupSecretGuardTest {

    private static final String PG = "jdbc:postgresql://db:5432/ges";
    private static final String OWN_JWT = "b3duLXNlY3JldC1tYWRlLWJ5LWRlcGxveS1zaA==";

    @Test
    void realServerWithOwnSecretsIsFine() {
        assertTrue(StartupSecretGuard.problems(false, PG, OWN_JWT, "a1b2c3d4e5f60718", "zx81QpLm20").isEmpty());
    }

    @Test
    void realServerWithAllThreeFallbacksIsRefused() {
        List<String> p = StartupSecretGuard.problems(false, PG,
                StartupSecretGuard.PUBLIC_JWT_SECRET, StartupSecretGuard.PUBLIC_ADMIN_KEY, StartupSecretGuard.PUBLIC_DB_PASSWORD);
        assertEquals(3, p.size());
    }

    @Test
    void eachFallbackIsCaughtOnItsOwn() {
        assertEquals(1, StartupSecretGuard.problems(false, PG, StartupSecretGuard.PUBLIC_JWT_SECRET, "k", "p").size());
        assertEquals(1, StartupSecretGuard.problems(false, PG, OWN_JWT, StartupSecretGuard.PUBLIC_ADMIN_KEY, "p").size());
        assertEquals(1, StartupSecretGuard.problems(false, PG, OWN_JWT, "k", StartupSecretGuard.PUBLIC_DB_PASSWORD).size());
    }

    @Test
    void emptySecretsAreRefused() {
        assertEquals(3, StartupSecretGuard.problems(false, PG, "", " ", null).size());
    }

    @Test
    void practiceCopyWithDemoDataIsNotChecked() {
        assertTrue(StartupSecretGuard.problems(true, PG,
                StartupSecretGuard.PUBLIC_JWT_SECRET, StartupSecretGuard.PUBLIC_ADMIN_KEY, StartupSecretGuard.PUBLIC_DB_PASSWORD).isEmpty());
    }

    @Test
    void inMemoryTestDatabaseIsNotChecked() {
        assertTrue(StartupSecretGuard.problems(false, "jdbc:h2:mem:x;MODE=PostgreSQL",
                StartupSecretGuard.PUBLIC_JWT_SECRET, StartupSecretGuard.PUBLIC_ADMIN_KEY, "").isEmpty());
    }
}
