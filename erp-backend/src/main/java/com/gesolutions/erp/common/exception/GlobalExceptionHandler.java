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
 * NYENZ ERP - MASTER DIAGNOSTIC INTERCEPTOR (V1.1 - PRODUCTION)
 * 
 * Captures hardware and logic faults to provide feedback to the UI.
 * Standardized to always include the "message" key for React Toasts.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    // --- 1. BUSINESS LOGIC FAULTS ---
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessException(BusinessException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "OPERATIONAL_DENIAL", ex.getMessage());
    }

    // --- 2. SECURITY FAULTS ---
    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<Map<String, Object>> handleBadCredentials(BadCredentialsException ex) {
        return buildResponse(HttpStatus.UNAUTHORIZED, "AUTH_FAILURE", "Incorrect Identity or Security Key.");
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDenied(AccessDeniedException ex) {
        return buildResponse(HttpStatus.FORBIDDEN, "SECURITY_BREACH", "Rank not authorized for this command.");
    }

    // --- 3. DATA ENTRY & TYPE FAULTS ---
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        String errorMessage = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getDefaultMessage())
                .collect(Collectors.joining(" | "));
        return buildResponse(HttpStatus.BAD_REQUEST, "INPUT_VALIDATION_FAILURE", errorMessage);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> handleJsonErrors(HttpMessageNotReadableException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "DATA_FORMAT_ERROR", "Invalid data format detected.");
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParams(MissingServletRequestParameterException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required data missing.");
    }

    // --- 4. DIGITAL VAULT FAULTS ---
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleFileSizeLimit(MaxUploadSizeExceededException ex) {
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "VAULT_CAPACITY_EXCEEDED", "File size exceeds 50MB limit.");
    }

    // --- 5. DATABASE INTEGRITY FAULTS ---
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrity(DataIntegrityViolationException ex) {
        String msg = ex.getMessage().toLowerCase();
        if (msg.contains("unique") || msg.contains("duplicate")) {
            return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A record with this ID already exists.");
        }
        return buildResponse(HttpStatus.CONFLICT, "INTEGRITY_VIOLATION", "Cannot modify record: Active data links found.");
    }

    // --- 6. UNKNOWN SYSTEM CRASHES ---
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneralException(Exception ex) {
        ex.printStackTrace();
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "SYSTEM_CRITICAL_FAULT", "Core error. Contact IT Support.");
    }

    /**
     * INDUSTRIAL JSON BUILDER
     * Ensures consistent structure for the Frontend Interceptors.
     */
    private ResponseEntity<Map<String, Object>> buildResponse(HttpStatus status, String error, String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now());
        body.put("status", status.value());
        body.put("error", error);
        body.put("message", message); // React reads this field
        return new ResponseEntity<>(body, status);
    }
}