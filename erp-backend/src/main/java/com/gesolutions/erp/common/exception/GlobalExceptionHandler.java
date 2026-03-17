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
import org.springframework.web.multipart.support.MissingServletRequestPartException;
import org.springframework.dao.DataIntegrityViolationException;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * NYENZ ERP - MASTER DIAGNOSTIC INTERCEPTOR
 * 
 * Captures specific hardware and logic faults to provide 
 * human-readable feedback to the Command Console.
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
        return buildResponse(HttpStatus.FORBIDDEN, "SECURITY_BREACH", "Your current rank does not authorize this command.");
    }

    // --- 3. DATA ENTRY & TYPE FAULTS ---
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        // Combines all field errors into one string (e.g., "Plot Number is required | Cost must be numeric")
        String errorMessage = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getDefaultMessage())
                .collect(Collectors.joining(" | "));
        return buildResponse(HttpStatus.BAD_REQUEST, "INPUT_VALIDATION_FAILURE", errorMessage);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> handleJsonErrors(HttpMessageNotReadableException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "DATA_FORMAT_ERROR", "Invalid data type detected. Please check that numeric fields do not contain text.");
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParams(MissingServletRequestParameterException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "PROTOCOL_INCOMPLETE", "Required parameter [" + ex.getParameterName() + "] is missing.");
    }
    
    @ExceptionHandler(MissingServletRequestPartException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParts(MissingServletRequestPartException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "TRANSMISSION_INCOMPLETE", "Required data part [" + ex.getRequestPartName() + "] was not received.");
    }

    // --- 4. DIGITAL VAULT (FILE) FAULTS ---
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleFileSizeLimit(MaxUploadSizeExceededException ex) {
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "VAULT_CAPACITY_EXCEEDED", "File size exceeds the 50MB hardware limit. Compress scan and retry.");
    }

    // --- 5. DATABASE INTEGRITY FAULTS ---
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrity(DataIntegrityViolationException ex) {
        String msg = ex.getMessage().toLowerCase();
        if (msg.contains("unique") || msg.contains("duplicate")) {
            return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A record with this ID, Phone, or Email already exists in the archive.");
        }
        return buildResponse(HttpStatus.CONFLICT, "INTEGRITY_VIOLATION", "Cannot delete or modify this record because it is linked to other active data.");
    }

    // --- 6. UNKNOWN SYSTEM CRASHES ---
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneralException(Exception ex) {
        // Print stack trace to backend console for developer debugging
        ex.printStackTrace();
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "SYSTEM_CRITICAL_FAULT", "An unexpected core error occurred. Please contact IT Support.");
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