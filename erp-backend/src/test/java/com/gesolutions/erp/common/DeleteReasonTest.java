package com.gesolutions.erp.common;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.common.util.DeleteReason;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/** fix223 (David): every delete of something saved needs a reason of a few words. */
class DeleteReasonTest {

    @Test
    void anEmptyOrTinyReasonIsRefusedWithAPlainSentence() {
        for (String bad : new String[] { null, "", "   ", "ok" }) {
            BusinessException e = assertThrows(BusinessException.class, () -> DeleteReason.require(bad));
            assertTrue(e.getMessage().startsWith("REASON_REQUIRED:"));
        }
    }

    @Test
    void aGoodReasonIsTrimmedAndKeptShort() {
        assertEquals("Uploaded by mistake", DeleteReason.require("  Uploaded   by mistake "));
        assertEquals(DeleteReason.MAX, DeleteReason.require("x".repeat(900)).length());
        assertEquals(" Reason: Logged twice", DeleteReason.tail("Logged twice"));
        assertEquals("", DeleteReason.tail(null));
    }
}
