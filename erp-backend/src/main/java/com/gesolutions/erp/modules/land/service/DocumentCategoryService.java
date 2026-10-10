// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/DocumentCategoryService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.DocumentCategory;
import com.gesolutions.erp.modules.land.repository.DocumentCategoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * GE SOLUTIONS - DOCUMENT CATEGORIES (fix136)
 *
 * Seeds the six built-in categories on first use (no DataInitializer edit
 * needed), lists them, validates the category an upload asks for, and lets
 * Secretary / Manager / Admin / Director add new ones.
 */
@Service
@RequiredArgsConstructor
public class DocumentCategoryService {

    private static final String[][] DEFAULTS = {
        {"APPLICATION_FORM",   "Application Forms"},
        {"OFFER_LETTER",       "Offer Letters"},
        {"FORWARDING_LETTER",  "Forwarding Letters"},
        {"DEED_PLAN",          "Deed Plan"},
        {"COPY_OF_TITLE",      "Copy of Title"},
        {"PAYMENT_RECEIPT",    "Payment Receipts"},
        {"INVOICE",            "Invoices"},   // fix174
        // fix199 (David, test note 22): every stage of the project types has its own document type, so the upload
        // window can pick it by itself when a file is attached from a stage. The label is the stage's own name.
        {"FIELD_MEASUREMENT",         "Field Measurement"},
        {"AREA_LAND_COMMITTEE",       "Area Land Committee"},
        {"PHYSICAL_PLANNING_CONSENT", "Physical Planning Consent"},
        {"BOARD_MINUTE",              "Board Minute"},
        {"INSTRUCTION_TO_SURVEY",     "Instruction to Survey"},
        {"JOB_RECORD_JACKET",         "Job Record Jacket (JRJ)"},
        {"CONSENT_FOR_SUBDIVISION",   "Consent for Subdivision"},
        {"TRANSFER_FORM",             "Transfer Form"},
        {"STAMP_DUTY",                "Stamp Duty"},
        {"SURVEY_REPORT",             "Survey Report"},
        {"CONTRACT",                  "Contracts"},
        {"PROGRESS_REPORT",           "Progress Reports"},
    };

    private final DocumentCategoryRepository repository;
    private final AuditService auditService;

    private volatile boolean seeded = false;

    /** Idempotent: inserts any built-in that is missing, once per app run. */
    private synchronized void ensureDefaults() {
        if (seeded) return;
        for (int i = 0; i < DEFAULTS.length; i++) {
            String code = DEFAULTS[i][0];
            if (repository.findByCode(code).isEmpty()) {
                repository.save(DocumentCategory.builder()
                        .code(code)
                        .label(DEFAULTS[i][1])
                        .builtIn(true)
                        .sortOrder(i + 1)
                        .createdBy("SYSTEM")
                        .build());
            }
        }
        seeded = true;
    }

    public List<DocumentCategory> list() {
        ensureDefaults();
        return repository.findAllByOrderByBuiltInDescSortOrderAscLabelAsc();
    }

    /**
     * Turns what the client sent into a stored category code.
     * null / blank -> null (uncategorised). Unknown -> BusinessException, so the
     * whole upload is refused before a single file is stored.
     */
    public String requireCode(String raw) {
        if (raw == null || raw.isBlank()) return null;
        ensureDefaults();
        String code = toCode(raw);
        if (code.isEmpty() || repository.findByCode(code).isEmpty()) {
            throw new BusinessException("Unknown document category: " + raw.trim());
        }
        return code;
    }

    @Transactional
    public DocumentCategory create(String label) {
        String clean = label == null ? "" : label.trim().replaceAll("\\s+", " ");
        if (clean.length() < 2) throw new BusinessException("Category name is too short.");
        if (clean.length() > 120) throw new BusinessException("Category name is too long (120 characters max).");
        String code = toCode(clean);
        if (code.isEmpty()) throw new BusinessException("Category name needs letters or numbers.");
        ensureDefaults();
        Optional<DocumentCategory> existing = repository.findByCode(code);
        if (existing.isPresent()) return existing.get();
        DocumentCategory saved = repository.save(DocumentCategory.builder()
                .code(code)
                .label(clean)
                .builtIn(false)
                .sortOrder(100)
                .createdBy(currentOperator())
                .build());
        auditService.logActionAfterCommit("DOCUMENT_CATEGORY_ADDED",
                "Operator [" + currentOperator() + "] added document category: " + saved.getLabel());
        return saved;
    }

    private static String toCode(String raw) {
        String code = raw.trim().toUpperCase(Locale.ROOT)
                .replaceAll("[^A-Z0-9]+", "_")
                .replaceAll("^_+|_+$", "");
        return code.length() > 60 ? code.substring(0, 60) : code;
    }

    private String currentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }
}
