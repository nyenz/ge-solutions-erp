package com.gesolutions.erp.modules.land.model;

import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class LandProjectTest {

    @Test
    public void testActiveTotalOwed() {
        LandProject project = new LandProject();
        project.setTotalCost(new BigDecimal("5000000"));
        project.setAmountPaid(new BigDecimal("1000000"));
        project.setReceivable(false);

        assertEquals(new BigDecimal("4000000"), project.activeTotalOwed());
    }

    @Test
    public void testReceivableTotalOwed() {
        LandProject project = new LandProject();
        project.setTotalCost(new BigDecimal("3500000"));
        project.setAmountPaid(new BigDecimal("1500000"));
        project.setStorageFeesAccumulated(new BigDecimal("50000"));
        project.setReceivable(true);

        assertEquals(new BigDecimal("2050000"), project.receivableTotalOwed());
    }

    // fix181 (3.6, 11.2): on a RECEIVABLE project the storage money inside amountPaid is not title money
    @Test
    public void receivableTitleMoneyExcludesStoragePaid() {
        LandProject p = new LandProject();
        p.setTotalCost(new BigDecimal("1000000"));
        p.setReceivable(true);
        p.setStorageFeesAccumulated(new BigDecimal("300000"));
        p.setStorageFeesPaid(new BigDecimal("300000"));
        p.setAmountPaid(new BigDecimal("1000000"));   // 700,000 title + 300,000 storage
        assertEquals(new BigDecimal("700000"), p.titlePaid());
        assertEquals(new BigDecimal("300000"), p.titleOwed());
        org.junit.jupiter.api.Assertions.assertNotNull(p.releaseBlocker(), "the hand-over must be refused");
    }

    // fix181 (3.6): the receivable formula is NOT changed (fees are added gross; amountPaid holds the money that paid them)
    @Test
    public void receivableOwedUnchanged() {
        LandProject p = new LandProject();
        p.setTotalCost(new BigDecimal("1000000"));
        p.setReceivable(true);
        p.setStorageFeesAccumulated(new BigDecimal("200000"));
        p.setStorageFeesPaid(new BigDecimal("200000"));
        p.setAmountPaid(new BigDecimal("300000"));    // 100,000 title + 200,000 storage
        assertEquals(new BigDecimal("900000"), p.receivableTotalOwed());
    }

    // fix181 (5.7): a price lowered below what was paid shows 0 owed, not a negative number
    @Test
    public void titleOwedNeverNegative() {
        LandProject p = new LandProject();
        p.setTotalCost(new BigDecimal("500000"));
        p.setAmountPaid(new BigDecimal("800000"));
        p.setReceivable(false);
        assertEquals(0, p.titleOwed().signum());
    }

    // fix181 (2.3, 11.3): no price = not paid; kept fees block the hand-over
    @Test
    public void zeroPriceIsNotPaidAndKeptFeesBlock() {
        LandProject p = new LandProject();
        p.setTotalCost(BigDecimal.ZERO);
        p.setAmountPaid(BigDecimal.ZERO);
        p.setReceivable(false);
        org.junit.jupiter.api.Assertions.assertFalse(p.isTitleFullyPaid());

        LandProject k = new LandProject();
        k.setTotalCost(new BigDecimal("100"));
        k.setAmountPaid(new BigDecimal("100"));
        k.setReceivable(false);
        k.setStorageFeesAccumulated(new BigDecimal("50"));
        k.setLandTitle(new LandTitle());
        assertEquals(new BigDecimal("50"), k.keptFees());
        org.junit.jupiter.api.Assertions.assertTrue(k.releaseBlocker().contains("set-aside"));
    }
}
