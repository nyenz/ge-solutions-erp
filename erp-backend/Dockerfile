# PATH: erp-backend/Dockerfile

# --- STAGE 1: BUILD THE ENGINE ---
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app

# Copy from current directory (which is now erp-backend)
COPY pom.xml .
COPY src ./src

# Compile the JAR
RUN mvn clean package -DskipTests

# --- STAGE 2: RUN THE ENGINE ---
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app

# Copy the JAR from the build stage
COPY --from=build /app/target/*.jar app.jar

# Create scan vault
RUN mkdir -p /ge_uploads
VOLUME /ge_uploads

EXPOSE 8080

# Production memory optimization for Free Tier (Reduced to 350MB)
ENTRYPOINT ["java", "-Xmx350m", "-jar", "app.jar"]