# PATH: erp-backend/Dockerfile

# ════════════════════════════════════════════════════════
# STAGE 1: THE BUILDER
# We use Maven to compile the Java source code into a JAR file.
# This stage is thrown away after building — it never reaches production.
# ════════════════════════════════════════════════════════
FROM maven:3.8.5-openjdk-17 AS build

WORKDIR /app

# VITAL FIX: Because dockerContext in render.yaml is '.' (the repo root),
# Docker runs this file FROM the repo root. So we must include
# 'erp-backend/' in the path, not just 'pom.xml'.
# We copy pom.xml first (alone) so Docker can cache the dependency
# download step. If you only change Java code, it won't re-download
# all libraries — saving 3-4 minutes on every deploy.
COPY erp-backend/pom.xml .
RUN mvn dependency:go-offline -B

# Now copy the actual source code and build it
COPY erp-backend/src ./src
RUN mvn clean package -DskipTests

# ════════════════════════════════════════════════════════
# STAGE 2: THE RUNNER
# We take only the compiled JAR (a single file) and run it.
# The result is a small, fast image with no build tools inside.
# ════════════════════════════════════════════════════════
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

RUN mkdir -p /ge_uploads
VOLUME /ge_uploads

EXPOSE 10000

# VITAL: $JAVA_OPTS picks up the memory flags we set in render.yaml.
# ${PORT:-10000} means: use PORT if set, otherwise use 10000.
# This prevents a crash if the environment variable arrives late.
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar --server.port=${PORT:-10000}"]