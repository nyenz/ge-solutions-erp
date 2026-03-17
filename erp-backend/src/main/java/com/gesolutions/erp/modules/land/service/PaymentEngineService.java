// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/PaymentEngineService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentSchedule;
import com.gesolutions.erp.modules.land.repository.PaymentScheduleRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode; // ADDED FOR MODERN MATH
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

/**
 * GE SOLUTIONS - FINANCIAL VELOCITY ENGINE
 * Generates the 3+1 Weekly Schedule and calculates Prepayment Priority.
 */
@Service
@RequiredArgsConstructor
public class PaymentEngineService {

    private final PaymentScheduleRepository scheduleRepository; // RESOLVED: Import error

    /**
     * GENERATES THE FULL INDUSTRIAL CALENDAR
     * Every 4th iteration is physically marked as a Grace Week.
     */
    @Transactional
    public void generateSchedule(@NonNull LandProject project, int durationMonths) {
        LandProject verifiedProject = Objects.requireNonNull(project);
        UUID projectId = Objects.requireNonNull(verifiedProject.getId());

        List<PaymentSchedule> schedules = new ArrayList<>();
        LocalDate startDate = LocalDate.now();
        
        int totalWeeks = durationMonths * 4;

        for (int w = 1; w <= totalWeeks; w++) {
            boolean isGrace = (w % 4 == 0);
            
            PaymentSchedule entry = PaymentSchedule.builder()
                    .projectId(projectId)
                    .dueDate(startDate.plusWeeks(w))
                    .expectedAmount(isGrace ? BigDecimal.ZERO : verifiedProject.getWeeklyInstallment())
                    .actualPaid(BigDecimal.ZERO)
                    .isGraceWeek(isGrace)
                    .isSatisfied(isGrace) 
                    .build();
            
            schedules.add(entry);
        }
        
        scheduleRepository.saveAll(schedules);
    }

    /**
     * PRIORITY ANALYSIS LOGIC (The 10-Week Rule)
     * FIXED: Removed deprecated divide() and rounding constants.
     */
    public boolean hasTenWeekBuffer(@NonNull LandProject project) {
        BigDecimal paid = Objects.requireNonNull(project.getAmountPaid());
        BigDecimal installment = Objects.requireNonNull(project.getWeeklyInstallment());
        
        if (installment.compareTo(BigDecimal.ZERO) <= 0) return false;

        // MODERN MATH: Uses RoundingMode.HALF_UP instead of BigDecimal.ROUND_HALF_UP
        BigDecimal weeksCovered = paid.divide(installment, 2, RoundingMode.HALF_UP);
        
        return weeksCovered.compareTo(new BigDecimal("10")) >= 0;
    }
}