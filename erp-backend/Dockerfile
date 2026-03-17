# PATH: erp-backend/Dockerfile
# Switch to Eclipse Temurin - The current standard for stable Java containers
FROM eclipse-temurin:17-jdk-alpine

# Physically create the folder for physical document scans
RUN mkdir -p /ge_uploads

# Volume for cross-platform persistence
VOLUME /ge_uploads

# VITAL: This copies the Production JAR you built with Maven
# Ensure you ran './mvnw clean package -DskipTests' inside erp-backend first!
COPY target/erp-backend-1.0.0-PROD.jar app.jar

# Define standard API port
EXPOSE 8080

# Execute the engine with optimized memory settings for small servers
ENTRYPOINT ["java", "-Xmx512m", "-jar", "app.jar"]