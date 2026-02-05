# Image Selection Criteria Reference

This document provides detailed criteria for selecting the optimal container image based on use case requirements.

## Scoring Matrix

Use this matrix to score image options based on user requirements.

### Criteria Weights by Environment

| Criteria | Production | Development | Edge/IoT | Serverless |
|----------|------------|-------------|----------|------------|
| Image Size | 3 | 1 | 5 | 4 |
| Security Posture | 5 | 2 | 4 | 3 |
| Build Tools | 1 | 5 | 1 | 1 |
| Startup Time | 3 | 1 | 3 | 5 |
| LTS Status | 5 | 2 | 4 | 3 |
| Debug Tools | 1 | 5 | 1 | 1 |

**Scale:** 1 (low importance) to 5 (high importance)

### Image Variant Scores

| Variant | Size | Security | Build Tools | Startup | Debug |
|---------|------|----------|-------------|---------|-------|
| Full | 2 | 2 | 5 | 2 | 5 |
| Minimal | 4 | 4 | 2 | 4 | 2 |
| Runtime | 5 | 5 | 1 | 5 | 1 |

**Scale:** 1 (poor) to 5 (excellent)

## Image Size Reference

Approximate compressed image sizes:

### Node.js
| Image | Size |
|-------|------|
| `ubi9/nodejs-20` | ~250MB |
| `ubi9/nodejs-20-minimal` | ~150MB |

### Python
| Image | Size |
|-------|------|
| `ubi9/python-311` | ~280MB |

### Java
| Image | Size |
|-------|------|
| `ubi9/openjdk-17` | ~400MB |
| `ubi9/openjdk-17-runtime` | ~200MB |

### Go
| Image | Size |
|-------|------|
| `ubi9/go-toolset:1.21` | ~500MB |
| Final binary | ~10-50MB |

### .NET
| Image | Size |
|-------|------|
| `ubi9/dotnet-80` | ~350MB |
| `ubi9/dotnet-80-runtime` | ~150MB |

## LTS Support Timeline

### Node.js
| Version | Status | End of Life |
|---------|--------|-------------|
| 18 LTS | Active | April 2025 |
| 20 LTS | Active | April 2026 |
| 22 LTS | Active | April 2027 |

### Python
| Version | Status | End of Life |
|---------|--------|-------------|
| 3.9 | Security | October 2025 |
| 3.11 | Active | October 2027 |
| 3.12 | Active | October 2028 |

### Java (OpenJDK)
| Version | Status | Extended Support |
|---------|--------|------------------|
| 11 LTS | Active | Red Hat until 2027 |
| 17 LTS | Active | Red Hat until 2029 |
| 21 LTS | Active | Red Hat until 2031 |

### .NET
| Version | Status | End of Life |
|---------|--------|-------------|
| 6.0 LTS | Active | November 2024 |
| 8.0 LTS | Active | November 2026 |

## Security Considerations

### Minimal Images - When to Use
- Fewer installed packages = smaller attack surface
- Recommended for production workloads
- May lack debugging tools when issues occur

### Full Images - When to Use
- Include development tools (gcc, make, etc.)
- Needed for native extensions (Python C extensions, Node native modules)
- Better for development and debugging

### Runtime Images - When to Use
- No build tools at all
- Smallest possible footprint
- Requires pre-compiled application (JAR, static binary)

## Framework-Specific Considerations

### Quarkus (Java)
**For JVM mode:**
- Use `ubi9/openjdk-21` for build
- Use `ubi9/openjdk-21-runtime` for production

**For Native mode:**
- Build: `quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-21`
- Run: `quay.io/quarkus/quarkus-micro-image:2.0`
- Dramatically faster startup (~50ms vs ~2s)

### Spring Boot (Java)
**Standard:**
- Build and run: `ubi9/openjdk-17`

**Optimized production:**
- Build with layered JAR: `spring-boot-maven-plugin` with layers
- Run on: `ubi9/openjdk-17-runtime`

### Next.js (Node.js)
**Development:**
- Use `ubi9/nodejs-20`

**Production (multi-stage recommended):**
1. Build stage: `ubi9/nodejs-20`
2. Run stage: `ubi9/nodejs-20-minimal` with `.next` output

### Django/Flask (Python)
- Always use full image (may need compilation for dependencies)
- `ubi9/python-311` recommended
- Consider `gunicorn` for production

## Decision Tree

```
START
  |
  v
Is this production?
  |
  +-- YES --> Need native compilation?
  |             |
  |             +-- YES --> Use FULL variant
  |             |
  |             +-- NO --> Is app pre-compiled?
  |                          |
  |                          +-- YES --> Use RUNTIME variant
  |                          |
  |                          +-- NO --> Use MINIMAL variant
  |
  +-- NO (Development) --> Use FULL variant
```

## Multi-Stage Build Recommendations

For optimal production images, consider multi-stage builds:

### Node.js Example
```dockerfile
# Build stage
FROM registry.access.redhat.com/ubi9/nodejs-20 AS builder
COPY . .
RUN npm ci && npm run build

# Production stage
FROM registry.access.redhat.com/ubi9/nodejs-20-minimal
COPY --from=builder /app/dist /app
CMD ["node", "/app/index.js"]
```

### Java Example
```dockerfile
# Build stage
FROM registry.access.redhat.com/ubi9/openjdk-21 AS builder
COPY . .
RUN mvn package -DskipTests

# Production stage
FROM registry.access.redhat.com/ubi9/openjdk-21-runtime
COPY --from=builder /app/target/*.jar /app/app.jar
CMD ["java", "-jar", "/app/app.jar"]
```

### Go Example
Go produces static binaries, so minimal base is ideal:
```dockerfile
# Build stage
FROM registry.access.redhat.com/ubi9/go-toolset:1.21 AS builder
COPY . .
RUN go build -o /app/server

# Production stage
FROM registry.access.redhat.com/ubi9/ubi-micro
COPY --from=builder /app/server /server
CMD ["/server"]
```
