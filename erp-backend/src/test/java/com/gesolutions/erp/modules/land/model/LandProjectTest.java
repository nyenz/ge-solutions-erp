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
        project.setBacklog(false);

        assertEquals(new BigDecimal("4000000"), project.activeTotalOwed());
    }

    @Test
    public void testBacklogTotalOwed() {
        LandProject project = new LandProject();
        project.setTotalCost(new BigDecimal("3500000"));
        project.setAmountPaid(new BigDecimal("1500000"));
        project.setStorageFeesAccumulated(new BigDecimal("50000"));
        project.setBacklog(true);

        assertEquals(new BigDecimal("2050000"), project.backlogTotalOwed());
    }
}
