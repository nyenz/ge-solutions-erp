// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/recovery/payments")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class PaymentController {

    private final PaymentRecordRepository paymentRecordRepository;
    private final LandProjectRepository projectRepository;

    @GetMapping("/all")
    public ResponseEntity<List<Map<String, Object>>> getAllPayments(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "500") int size) {

        List<PaymentRecord> records = paymentRecordRepository.findAll(
                PageRequest.of(page, size, Sort.by("timestamp").descending())
        ).getContent();

        List<Map<String, Object>> result = new ArrayList<>();

        for (PaymentRecord pay : records) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id",           pay.getId());
            row.put("projectId",    pay.getProjectId());
            row.put("amountPaid",   pay.getAmountPaid());
            row.put("paymentType",  pay.getPaymentType());
            row.put("recordedBy",   pay.getRecordedBy());
            row.put("notes",        pay.getNotes());
            row.put("balanceAfter", pay.getBalanceAfter());
            row.put("timestamp",    pay.getTimestamp());

            try {
                LandProject project = projectRepository.findById(pay.getProjectId()).orElse(null);
                if (project != null) {
                    row.put("plotNumber", project.getLandTitle().getPlotNumber());
                    String ownerName = project.getProprietors().stream()
                            .findFirst()
                            .map(c -> c.getFullName())
                            .orElse("---");
                    row.put("ownerName", ownerName);
                } else {
                    row.put("plotNumber", "---");
                    row.put("ownerName",  "---");
                }
            } catch (Exception e) {
                row.put("plotNumber", "---");
                row.put("ownerName",  "---");
            }

            result.add(row);
        }

        return ResponseEntity.ok(result);
    }
}