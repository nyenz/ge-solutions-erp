# PATH: erp-backend/Dockerfile

# --- STAGE 1: BUILD THE ENGINE ---
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
# Copy the pom and source code to the cloud builder
COPY pom.xml .
COPY src ./src
# Physically compile the JAR in the cloud
RUN mvn clean package -DskipTests

# --- STAGE 2: RUN THE ENGINE ---
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
# Copy the JAR we just built in Stage 1
COPY --from=build /app/target/*.jar app.jar

# Create scan vault
RUN mkdir -p /ge_uploads
VOLUME /ge_uploads

EXPOSE 8080

# Run with memory optimization for Render's free tier
ENTRYPOINT ["java", "-Xmx400m", "-jar", "app.jar"]