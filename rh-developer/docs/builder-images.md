# S2I Builder Image Reference

Use this reference when recommending S2I builder images to users.

> **Note:** Versions marked "Recommended" may change. Always verify with `skopeo inspect` before use. Prefer matching the project's version requirements over these defaults.

For use-case-aware image selection, use the `/recommend-image` skill.

---

## Dynamic Lookup and Verification

**This reference may be outdated.** Always verify image availability before recommending.

### Verify with Skopeo (Recommended)

```bash
# Check if an image exists and get metadata
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20

# Get specific fields
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{.Created}}'
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{.Architecture}}'

# List all available tags
skopeo list-tags docker://registry.access.redhat.com/ubi9/nodejs-20
```

**If skopeo is not installed**, prompt the user:
```
Install with: sudo dnf install skopeo (Fedora/RHEL)
              sudo apt install skopeo (Ubuntu/Debian)
              brew install skopeo (macOS)
```

### Check Security Status (Red Hat Security Data API)

Query CVE information (no authentication required):

```bash
# Check for critical CVEs affecting UBI9
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq 'length'

# Get CVE details
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq '.[] | {cve: .CVE, severity: .severity}'
```

### Verify with Red Hat Catalog API (Alternative)

```bash
# Search for available Node.js images
curl -s "https://catalog.redhat.com/api/containers/v1/repositories?filter=repository=like=ubi9/nodejs" | jq '.data[].repository'

# Search for available Python images
curl -s "https://catalog.redhat.com/api/containers/v1/repositories?filter=repository=like=ubi9/python" | jq '.data[].repository'
```

---

## Project Detection and Version Mapping

### Extract Version from Project Files

Before recommending an image, check the project's version requirements:

| Project File | How to Extract Version |
|--------------|------------------------|
| `package.json` | `.engines.node` field |
| `requirements.txt` | `python_requires` or comments |
| `pyproject.toml` | `[project].requires-python` |
| `pom.xml` | `<maven.compiler.source>` or `<java.version>` |
| `go.mod` | `go` directive (e.g., `go 1.21`) |
| `*.csproj` | `<TargetFramework>` (e.g., `net8.0`) |

### Detect Language from Files

| Indicator File(s) | Language | Framework | Version Source |
|-------------------|----------|-----------|----------------|
| `package.json` | Node.js | - | `.engines.node` |
| `package.json` + `next.config.js` | Node.js | Next.js | `.engines.node` |
| `package.json` + `angular.json` | Node.js | Angular | `.engines.node` |
| `pom.xml` | Java | Maven | `<java.version>` or `<maven.compiler.source>` |
| `pom.xml` + quarkus dep | Java | Quarkus | `<java.version>` (prefer 21+) |
| `pom.xml` + spring-boot dep | Java | Spring Boot | `<java.version>` |
| `build.gradle` / `build.gradle.kts` | Java | Gradle | `sourceCompatibility` or `java.toolchain` |
| `requirements.txt` | Python | - | `python_requires` or shebang |
| `Pipfile` | Python | Pipenv | `[requires].python_version` |
| `pyproject.toml` | Python | Poetry/Modern | `[project].requires-python` |
| `go.mod` | Go | - | `go` directive line |
| `Gemfile` | Ruby | - | `ruby` directive or `.ruby-version` |
| `*.csproj` / `*.sln` | .NET | - | `<TargetFramework>` (e.g., net8.0 → 80) |
| `composer.json` | PHP | - | `require.php` field |
| `Cargo.toml` | Rust | - | Custom (no official S2I) |

### Map Version to Image

**Quick lookup pattern:** `ubi9/{language}-{version}` (e.g., `ubi9/nodejs-20`, `ubi9/python-311`)

| Language | Version Mapping | Image Pattern |
|----------|-----------------|---------------|
| Node.js | 18.x → 18, 20.x → 20, 22.x → 22 | `ubi9/nodejs-{major}` |
| Python | 3.9 → 39, 3.11 → 311, 3.12 → 312 | `ubi9/python-{majmin}` |
| Java | 11, 17, 21 (use nearest LTS) | `ubi9/openjdk-{version}` |
| Go | 1.21 → 1.21, 1.22 → 1.22 | `ubi9/go-toolset:{version}` |
| Ruby | 3.1 → 31, 3.3 → 33 | `ubi9/ruby-{majmin}` |
| .NET | net6.0 → 60, net8.0 → 80 | `ubi9/dotnet-{version}` |
| PHP | 8.0 → 80, 8.1 → 81 | `ubi9/php-{majmin}` |

### Verify and Fallback

1. **Verify image exists**: `skopeo inspect docker://registry.access.redhat.com/ubi9/{image}`
2. **If version not found**: Use nearest available LTS version
3. **If no version in project**: Use current LTS (check catalog API)

---

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

---

## Image Variants and Use-Case Selection

### Quick Use-Case Matrix

| Use Case | Variant | Priority | Example |
|----------|---------|----------|---------|
| Production | Minimal/Runtime | Security, Size | `nodejs-20-minimal` |
| Development | Full | Tools, Debug | `nodejs-20` |
| Serverless | Minimal | Startup Time | `openjdk-21-runtime` |
| Edge/IoT | Minimal | Size | `nodejs-20-minimal` |

### Image Variants

| Variant | Description | Has Build Tools | Size |
|---------|-------------|-----------------|------|
| Full | Complete development environment | Yes | Largest |
| Minimal | Essential packages only | Limited | Medium |
| Runtime | Runtime only, no build tools | No | Smallest |

**Availability by language:**

| Language | Full | Minimal | Runtime |
|----------|------|---------|---------|
| Node.js | `nodejs-{ver}` | `nodejs-{ver}-minimal` | - |
| Python | `python-{ver}` | - | - |
| Java | `openjdk-{ver}` | - | `openjdk-{ver}-runtime` |
| Go | `go-toolset:{ver}` | - | (produces static binary) |
| .NET | `dotnet-{ver}` | - | `dotnet-{ver}-runtime` |
| Ruby | `ruby-{ver}` | - | - |
| PHP | `php-{ver}` | - | - |

### When to Recommend Each Variant

**Full variant:**
- User needs to compile native extensions
- Development/debugging environment
- CI/CD build stages

**Minimal variant:**
- Production deployments
- Security-focused environments
- When size matters but some tools needed

**Runtime variant:**
- Pre-compiled applications (JARs, .NET assemblies)
- Maximum security posture
- Smallest possible footprint

---

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

---

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

---

## Python S2I Entry Point Requirements

**Quick reference:**
- Default entry point: `app.py` (works without configuration)
- Custom entry points require: `gunicorn` + `APP_MODULE` environment variable
- Format: `APP_MODULE=module:variable` (e.g., `main:app`)
