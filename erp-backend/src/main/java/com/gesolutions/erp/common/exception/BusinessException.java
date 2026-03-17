// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/exception/BusinessException.java
package com.gesolutions.erp.common.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.BAD_REQUEST)
public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
}