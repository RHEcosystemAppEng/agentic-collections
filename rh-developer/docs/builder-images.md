# S2I Builder Image Reference Tables

> **Note:** Versions marked "Recommended" may change. Always verify with `skopeo inspect` before use. Prefer matching the project's version requirements over these defaults.

For use-case-aware image selection, use the `/recommend-image` skill.

## Red Hat UBI-based Images

### Node.js

| Version | Full Image | Minimal Image | Use Case |
|---------|------------|---------------|----------|
| 18 LTS | `registry.access.redhat.com/ubi9/nodejs-18` | `registry.access.redhat.com/ubi9/nodejs-18-minimal` | Long-term support |
| 20 LTS | `registry.access.redhat.com/ubi9/nodejs-20` | `registry.access.redhat.com/ubi9/nodejs-20-minimal` | **Recommended** |
| 22 | `registry.access.redhat.com/ubi9/nodejs-22` | `registry.access.redhat.com/ubi9/nodejs-22-minimal` | Current |

**Choose minimal for:** Production, security-focused, smaller image size
**Choose full for:** Development, native module compilation

### Python

| Version | Image | Notes |
|---------|-------|-------|
| 3.9 | `registry.access.redhat.com/ubi9/python-39` | |
| 3.11 | `registry.access.redhat.com/ubi9/python-311` | **Recommended** |
| 3.12 | `registry.access.redhat.com/ubi9/python-312` | Latest |

### Java / OpenJDK

| Version | Build Image | Runtime Image | Notes |
|---------|-------------|---------------|-------|
| 11 LTS | `registry.access.redhat.com/ubi8/openjdk-11` | `registry.access.redhat.com/ubi8/openjdk-11-runtime` | LTS |
| 17 LTS | `registry.access.redhat.com/ubi9/openjdk-17` | `registry.access.redhat.com/ubi9/openjdk-17-runtime` | **Recommended** |
| 21 LTS | `registry.access.redhat.com/ubi9/openjdk-21` | `registry.access.redhat.com/ubi9/openjdk-21-runtime` | Latest LTS |

**Choose runtime for:** Production with pre-built JARs, smallest footprint
**Choose build for:** S2I builds, Maven/Gradle compilation needed

### Go

| Version | Image | Notes |
|---------|-------|-------|
| 1.20 | `registry.access.redhat.com/ubi9/go-toolset:1.20` | |
| 1.21 | `registry.access.redhat.com/ubi9/go-toolset:1.21` | **Recommended** |

### Ruby

| Version | Image | Notes |
|---------|-------|-------|
| 3.1 | `registry.access.redhat.com/ubi9/ruby-31` | |
| 3.3 | `registry.access.redhat.com/ubi9/ruby-33` | **Recommended** |

### .NET

| Version | Build Image | Runtime Image | Notes |
|---------|-------------|---------------|-------|
| 6.0 LTS | `registry.access.redhat.com/ubi8/dotnet-60` | `registry.access.redhat.com/ubi8/dotnet-60-runtime` | LTS |
| 7.0 | `registry.access.redhat.com/ubi8/dotnet-70` | `registry.access.redhat.com/ubi8/dotnet-70-runtime` | |
| 8.0 LTS | `registry.access.redhat.com/ubi9/dotnet-80` | `registry.access.redhat.com/ubi9/dotnet-80-runtime` | **Recommended** |

**Choose runtime for:** Production with pre-built assemblies
**Choose build for:** S2I builds, dotnet build/publish needed

### PHP

| Version | Image | Notes |
|---------|-------|-------|
| 8.0 | `registry.access.redhat.com/ubi9/php-80` | |
| 8.1 | `registry.access.redhat.com/ubi9/php-81` | **Recommended** |

### Perl

| Version | Image | Notes |
|---------|-------|-------|
| 5.32 | `registry.access.redhat.com/ubi9/perl-532` | |

## OpenShift Built-in ImageStreams

These are often pre-configured in OpenShift clusters under the `openshift` namespace:

| ImageStream | Usage |
|-------------|-------|
| `nodejs:20-ubi9` | Node.js 20 on UBI 9 |
| `python:3.11-ubi9` | Python 3.11 on UBI 9 |
| `openjdk-17-ubi8` | Java 17 on UBI 8 |
| `ruby:3.1-ubi9` | Ruby 3.1 on UBI 9 |
| `php:8.0-ubi9` | PHP 8.0 on UBI 9 |

When using OpenShift ImageStreams, reference them as:
```yaml
from:
  kind: ImageStreamTag
  namespace: openshift
  name: nodejs:20-ubi9
```

## Framework-Specific Recommendations

### Quarkus (Java)
- **Native build**: `quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-21`
- **JVM build**: `registry.access.redhat.com/ubi9/openjdk-21`

### Spring Boot (Java)
- Use: `registry.access.redhat.com/ubi9/openjdk-17` or `openjdk-21`
- Ensure `spring-boot-maven-plugin` is configured for packaging

### Next.js / React (Node.js)
- Use: `registry.access.redhat.com/ubi9/nodejs-20`
- Ensure build outputs to `build/` or `.next/`

### Django / Flask (Python)
- Use: `registry.access.redhat.com/ubi9/python-311`
- Ensure `requirements.txt` or `Pipfile` exists at root

### Express.js (Node.js)
- Use: `registry.access.redhat.com/ubi9/nodejs-18` or higher
- Ensure `npm start` script is defined in `package.json`
