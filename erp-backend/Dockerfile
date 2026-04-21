# PATH: erp-backend/Dockerfile

# STAGE 1: BUILD
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY erp-backend/pom.xml .
COPY erp-backend/src ./src
RUN mvn clean package -DskipTests

# STAGE 2: RUN
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

RUN mkdir -p /ge_uploads
VOLUME /ge_uploads

# VITAL: Render uses PORT 10000. We tell the JAR to listen to the environment.
EXPOSE 10000

# Optimized for 512MB RAM limits
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar --server.port=${PORT}"]