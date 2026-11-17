# =============================================================================
# core-api — multi-stage build: Maven (JDK 21) -> slim JRE 21 runtime
# =============================================================================

# ---- Build stage ------------------------------------------------------------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
# Cache dependencies first (layer reuse on code-only changes)
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q package -DskipTests

# ---- Runtime stage ------------------------------------------------------------
FROM eclipse-temurin:21-jre-alpine AS runtime
# wget needed for the container healthcheck
RUN apk add --no-cache wget && \
    addgroup -S app && adduser -S app -G app
USER app
WORKDIR /app
COPY --from=build /build/target/core-api-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
