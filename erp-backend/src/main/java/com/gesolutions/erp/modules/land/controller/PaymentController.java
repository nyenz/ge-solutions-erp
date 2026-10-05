// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.service.PaymentQueryService;
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
    private final PaymentQueryService queryService;
    private final com.gesolutions.erp.modules.land.service.BooksCheckService booksCheckService;

    /** fix181 (16.12c): projects whose payment lines do not add up to their amount paid (report only). */
    @GetMapping("/books-check")
    public ResponseEntity<Map<String, Object>> booksCheck() {
        List<Map<String, Object>> diff = booksCheckService.differences();
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("ok", diff.isEmpty());
        m.put("differences", diff);
        return ResponseEntity.ok(m);
    }

    /** fix181 (16.7): one page of the list with the filters, sorted and paged on the server. */
    @GetMapping("/list")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public Map<String, Object> list(@RequestParam(required = false) String from, @RequestParam(required = false) String to,
                                    @RequestParam(defaultValue = "ALL") String tab, @RequestParam(required = false) String projectType,
                                    @RequestParam(required = false) String q, @RequestParam(defaultValue = "false") boolean includeDeleted,
                                    @RequestParam(defaultValue = "false") boolean missingReceipt,
                                    @RequestParam(defaultValue = "date") String sort, @RequestParam(defaultValue = "desc") String dir,
                                    @RequestParam(defaultValue = "0") int page, @RequestParam(defaultValue = "50") int size) {
        return queryService.page(filter(from, to, tab, projectType, q, includeDeleted, missingReceipt, sort, dir), page, size);
    }

    /** fix181 (16.7): the card numbers for the same filters, over every row (not one page). */
    @GetMapping("/totals")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public Map<String, Object> totals(@RequestParam(required = false) String from, @RequestParam(required = false) String to,
                                      @RequestParam(defaultValue = "ALL") String tab, @RequestParam(required = false) String projectType,
                                      @RequestParam(required = false) String q, @RequestParam(defaultValue = "false") boolean missingReceipt) {
        return queryService.totals(filter(from, to, tab, projectType, q, false, missingReceipt, "date", "desc"));
    }

    private static PaymentQueryService.Filter filter(String from, String to, String tab, String projectType, String q,
                                                     boolean includeDeleted, boolean missingReceipt, String sort, String dir) {
        java.time.LocalDate f = from == null || from.isBlank() ? null : java.time.LocalDate.parse(from);
        java.time.LocalDate t = to == null || to.isBlank() ? null : java.time.LocalDate.parse(to);
        return new PaymentQueryService.Filter(f, t, tab, projectType, q, includeDeleted, missingReceipt, sort, dir);
    }
}