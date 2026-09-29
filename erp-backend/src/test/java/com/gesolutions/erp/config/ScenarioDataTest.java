// PATH: erp-backend/src/test/java/com/gesolutions/erp/config/ScenarioDataTest.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.common.util.PhoneUtil;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Guards the seed dataset: if someone edits ScenarioData and the money stops
 * adding up (overpayment, wrong storage-fee months, duplicate plot, unknown
 * owner or staff name) this fails before the bad data can reach a database.
 */
class ScenarioDataTest {

    @Test
    void datasetMoneyAndReferencesAreConsistent() {
        assertDoesNotThrow(() -> { ScenarioData.selfCheck(); });
    }

    /** Every seeded phone must already be in the exact form PhoneUtil stores, or search and tap-to-call break. */
    @Test
    void seededPhonesAreInTheStandardStoredFormat() {
        int i = 0;
        for (ScenarioData.Person p : ScenarioData.people()) {
            i++;
            String stored = ScenarioData.phoneFor(p.key, i);
            assertEquals(stored, PhoneUtil.normalizeList(stored), "phone of " + p.key);
        }
    }
}
