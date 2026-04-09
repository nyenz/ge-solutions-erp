# PATH: erp-backend/Dockerfile

# --- STAGE 1: BUILD THE ENGINE ---
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY erp-backend/pom.xml .
COPY erp-backend/src ./src
RUN mvn clean package -DskipTests

# --- STAGE 2: RUN THE ENGINE ---
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

# Create scan vault
RUN mkdir -p /ge_uploads
VOLUME /ge_uploads

EXPOSE 8080

# VITAL: Set memory limit to 256MB to leave room for the OS (prevents 'OOM' crashes)
ENTRYPOINT ["java", "-Xmx256m", "-jar", "app.jar"]