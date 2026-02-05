---
name: s2i-builder-images
description: |
  Reference table of Red Hat UBI-based S2I builder images for Node.js, Python, Java, Go, Ruby, .NET, PHP, and Perl. Includes dynamic lookup methods (Red Hat Catalog API, skopeo), version extraction patterns from project files, framework-specific recommendations (Quarkus, Spring Boot, Next.js, Django), and OpenShift built-in ImageStreams. Used by /detect-project skill to recommend appropriate builder images. Note - verify image availability before recommending as versions may change.
---

# S2I Builder Image Reference

Use this reference when recommending S2I builder images to users.

## Important: Dynamic Lookup First

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

---

## Image Reference Tables

**Quick lookup pattern:** `ubi9/{language}-{version}` (e.g., `ubi9/nodejs-20`, `ubi9/python-311`)

---

## Project Detection Mapping

### Step 1: Detect Language from Files

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

### Step 2: Map Version to Image

| Language | Version Mapping | Image Pattern |
|----------|-----------------|---------------|
| Node.js | 18.x → 18, 20.x → 20, 22.x → 22 | `ubi9/nodejs-{major}` |
| Python | 3.9 → 39, 3.11 → 311, 3.12 → 312 | `ubi9/python-{majmin}` |
| Java | 11, 17, 21 (use nearest LTS) | `ubi9/openjdk-{version}` |
| Go | 1.21 → 1.21, 1.22 → 1.22 | `ubi9/go-toolset:{version}` |
| Ruby | 3.1 → 31, 3.3 → 33 | `ubi9/ruby-{majmin}` |
| .NET | net6.0 → 60, net8.0 → 80 | `ubi9/dotnet-{version}` |
| PHP | 8.0 → 80, 8.1 → 81 | `ubi9/php-{majmin}` |

### Step 3: Verify and Fallback

1. **Verify image exists**: `skopeo inspect docker://registry.access.redhat.com/ubi9/{image}`
2. **If version not found**: Use nearest available LTS version
3. **If no version in project**: Use current LTS (check catalog API)

---

## Use-Case Aware Selection

For advanced image selection based on use case, see the `/recommend-image` skill.

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

## Python S2I Entry Point Requirements

**Quick reference:**
- Default entry point: `app.py` (works without configuration)
- Custom entry points require: `gunicorn` + `APP_MODULE` environment variable
- Format: `APP_MODULE=module:variable` (e.g., `main:app`)
