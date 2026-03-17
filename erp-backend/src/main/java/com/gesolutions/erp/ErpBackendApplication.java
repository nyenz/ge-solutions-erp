// PATH: erp-backend/src/main/java/com/gesolutions/erp/ErpBackendApplication.java
package com.gesolutions.erp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * Main Entry Point for GE Solutions ERP.
 * 
 * Includes @ConfigurationPropertiesScan to ensure 'JwtProperties' 
 * and other configuration classes are mapped to 'application.properties'
 * automatically, ensuring professional property management and IDE safety.
 */
@SpringBootApplication
@ConfigurationPropertiesScan("com.gesolutions.erp.config")
public class ErpBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(ErpBackendApplication.class, args);
	}

}