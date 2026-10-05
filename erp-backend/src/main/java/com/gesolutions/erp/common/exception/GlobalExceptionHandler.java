// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/exception/GlobalExceptionHandler.java
package com.gesolutions.erp.common.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.dao.DataIntegrityViolationException;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * GOLDEN SEED ERP - MASTER DIAGNOSTIC INTERCEPTOR (V1.3 - LOUD REPORTING)
 * 
 * Physically prints hardware and logic faults to the cloud terminal 
 * so we can diagnose failures via the Render Logs window.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    // fix181 (13.6d): every refused @PreAuthorize is written to the audit trail HERE, once per person and path per hour
    private final com.gesolutions.erp.common.audit.AuditService auditService;
    private final java.util.concurrent.ConcurrentHashMap<String, Long> deniedSeen = new java.util.concurrent.ConcurrentHashMap<>();

    public GlobalExceptionHandler(com.gesolutions.erp.common.audit.AuditService auditService) {
        this.auditService = auditService;
    }

    private void auditDenied() {
        try {
            var attrs = org.springframework.web.context.request.RequestContextHolder.getRequestAttributes();
            if (!(attrs instanceof org.springframework.web.context.request.ServletRequestAttributes sra)) return;
            var req = sra.getRequest();
            String who = com.gesolutions.erp.common.audit.AuditService.currentOperator();
            String key = who + "|" + req.getMethod() + "|" + req.getRequestURI();
            long now = System.currentTimeMillis();
            Long last = deniedSeen.get(key);
            if (last != null && now - last < 3_600_000L) return;
            deniedSeen.put(key, now);
            if (deniedSeen.size() > 5000) deniedSeen.clear();
            auditService.logAction("ACCESS_DENIED", "Refused: " + req.getMethod() + " " + req.getRequestURI() + " (rank not allowed).");
        } catch (Exception e) {
            System.err.println(">>> [AUDIT] access-denied line not written: " + e.getMessage());
        }
    }

    // fix181: an unknown address is a 404, not a server error
    @ExceptionHandler(org.springframework.web.servlet.resource.NoResourceFoundException.class)
    public ResponseEntity<Map<String, Object>> handleNotFound(org.springframework.web.servlet.resource.NoResourceFoundException ex) {
        return buildResponse(HttpStatus.NOT_FOUND, "NOT_FOUND", "No such address.");
    }

    // --- 1. BUSINESS LOGIC FAULTS ---
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessException(BusinessException ex) {
        System.err.println(">>> [LOGIC_FAULT]: " + ex.getMessage());
        return buildResponse(HttpStatus.BAD_REQUEST, "OPERATIONAL_DENIAL", ex.getMessage());
    }

    // --- 2. SECURITY FAULTS ---
    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<Map<String, Object>> handleBadCredentials(BadCredentialsException ex) {
        System.err.println(">>> [SECURITY_FAULT]: Incorrect password or username attempt detected.");
        return buildResponse(HttpStatus.UNAUTHORIZED, "AUTH_FAILURE", "Incorrect Identity or Security Key.");
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDenied(AccessDeniedException ex) {
        System.err.println(">>> [SECURITY_BREACH]: Unauthorized Rank attempt to access restricted data.");
        auditDenied();
        return buildResponse(HttpStatus.FORBIDDEN, "SECURITY_BREACH", "Rank not authorized for this command.");
    }

    // --- 3. DATA ENTRY & TYPE FAULTS ---
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        String errorMessage = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getDefaultMessage())
                .collect(Collectors.joining(" | "));
        System.err.println(">>> [VALIDATION_FAULT]: " + errorMessage);
        return buildResponse(HttpStatus.BAD_REQUEST, "INPUT_VALIDATION_FAILURE", errorMessage);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> handleJsonErrors(HttpMessageNotReadableException ex) {
        System.err.println(">>> [DATA_FAULT]: JSON payload malformed or incorrect types provided.");
        return buildResponse(HttpStatus.BAD_REQUEST, "DATA_FORMAT_ERROR", "Invalid data format detected.");
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParams(MissingServletRequestParameterException ex) {
        System.err.println(">>> [PROTOCOL_FAULT]: Missing mandatory parameter: " + ex.getParameterName());
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required data missing: " + ex.getParameterName() + ".");
    }

    // fix165: a missing file part and a wrongly typed value used to fall into the generic 500 "Core error".
    @ExceptionHandler(org.springframework.web.multipart.support.MissingServletRequestPartException.class)
    public ResponseEntity<Map<String, Object>> handleMissingPart(org.springframework.web.multipart.support.MissingServletRequestPartException ex) {
        System.err.println(">>> [PROTOCOL_FAULT]: Missing file part: " + ex.getRequestPartName());
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required file missing: " + ex.getRequestPartName() + ".");
    }

    @ExceptionHandler(org.springframework.web.method.annotation.MethodArgumentTypeMismatchException.class)
    public ResponseEntity<Map<String, Object>> handleTypeMismatch(org.springframework.web.method.annotation.MethodArgumentTypeMismatchException ex) {
        System.err.println(">>> [DATA_FAULT]: Bad value for " + ex.getName());
        return buildResponse(HttpStatus.BAD_REQUEST, "DATA_FORMAT_ERROR", "Invalid value for " + ex.getName() + ".");
    }

    // --- 4. DIGITAL VAULT FAULTS ---
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleFileSizeLimit(MaxUploadSizeExceededException ex) {
        // VITAL FIX: message now reflects the ACTUAL configured limits in
        // application.properties (50MB per file, 250MB per full upload batch),
        // instead of the old hardcoded text that did not match reality.
        System.err.println(">>> [HARDWARE_LIMIT]: Upload exceeded configured size threshold. " + ex.getMessage());
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "VAULT_CAPACITY_EXCEEDED",
            "File too large. Each file must be under 50MB, and the total of all files in one upload must be under 250MB.");
    }

    // --- 5. DATABASE INTEGRITY FAULTS ---
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrity(DataIntegrityViolationException ex) {
        String msg = ex.getMessage() != null ? ex.getMessage().toLowerCase() : "";
        System.err.println(">>> [DB_CONFLICT]: " + msg);
        if (msg.contains("unique") || msg.contains("duplicate")) {
            if (msg.contains("plot_number") || msg.contains("plot number") || msg.contains("plotnumber")) {
                return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A plot with this ID already exists in the system.");
            }
            return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A record with this ID already exists.");
        }
        return buildResponse(HttpStatus.CONFLICT, "INTEGRITY_VIOLATION", "Cannot modify record: Active data links found.");
    }

    // --- 6. UNKNOWN SYSTEM CRASHES ---
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneralException(Exception ex) {
        // Sends the FULL technical history to the Render Logs tab
        System.err.println("!!! CRITICAL_SYSTEM_FAULT_DETECTED !!!");
        ex.printStackTrace(); 
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "SYSTEM_CRITICAL_FAULT", "Core error (" + ex.getClass().getSimpleName() + "). Look at Render Logs for Trace.");
    }

    /**
     * INDUSTRIAL JSON BUILDER
     */
    private ResponseEntity<Map<String, Object>> buildResponse(HttpStatus status, String error, String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", status.value());
        body.put("error", error);
        body.put("message", message);
        return new ResponseEntity<>(body, status);
    }
}