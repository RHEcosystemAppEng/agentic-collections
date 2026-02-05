---
name: recommend-image
description: |
  Intelligently recommend the optimal S2I builder image or container base image for a project based on detected language/framework, use-case requirements, security posture, and deployment target. Supports GitHub URLs for remote project analysis (delegates to /detect-project). Use this skill when the user needs a container image recommendation, wants to compare image options, or asks about production vs development images. Triggers on /recommend-image command, or when advanced image selection beyond basic version matching is needed. Supports Node.js, Python, Java, Go, Ruby, .NET, PHP, and Perl on Red Hat UBI.
---

# /recommend-image Skill

Provide intelligent, use-case-aware container image recommendations that go beyond simple language-to-image mapping.

## When to Use This Skill

- User asks for the "best" image for their use case
- User needs to choose between production vs development images
- User wants to compare image options (minimal vs full-featured)
- `/detect-project` completed and user wants a tailored recommendation
- User asks about image size, security, or performance trade-offs

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires user input and confirmation. You MUST:
1. **Wait for user responses** to all questions before proceeding
2. **Do NOT assume** user preferences - always ask
3. **Present options clearly** and wait for selection
4. **Confirm final recommendation** before saving to session state

## Workflow

### Step 1: Gather Context

**If invoked after `/detect-project`:**
Use the already-detected values:
- `LANGUAGE` - Programming language
- `FRAMEWORK` - Framework (if detected)
- `VERSION` - Language version

**If invoked with a GitHub URL:**

Example: `/recommend-image for https://github.com/RHEcosystemAppEng/sast-ai-frontend`

When a GitHub URL is provided:

```markdown
## Analyzing Remote Repository

I'll analyze the repository to detect the project type first.

Invoking `/detect-project` for: `[github-url]`
```

**Delegate to `/detect-project`:**
- Pass the GitHub URL to `/detect-project`
- `/detect-project` will use GitHub MCP to analyze the repository
- Receive back: `LANGUAGE`, `FRAMEWORK`, `VERSION`, `APP_NAME`
- Continue to Step 2 (Use-Case Assessment)

**If invoked standalone (no URL, no prior detection):**
Ask the user:

```markdown
## Image Recommendation

To recommend the best image, I need some information:

**Option 1:** Provide a GitHub URL
- Example: `/recommend-image for https://github.com/user/repo`

**Option 2:** Tell me about your project
1. **What language/framework is your project?**
   (e.g., Python 3.11, Node.js 20, Java 17 with Spring Boot)

2. **What version do you need?**
   (or say "latest LTS" if unsure)
```

### Step 2: Use-Case Assessment

Present use-case questions:

```markdown
## Use-Case Assessment

To recommend the optimal image, please tell me about your requirements:

**1. Deployment Environment:**
- **Production** - Stability, security, long-term support critical
- **Development** - Tooling, debugging features preferred
- **Edge/IoT** - Minimal footprint essential

**2. Security Priority:**
- **Standard** - Red Hat UBI with regular updates
- **Hardened** - Minimal attack surface, fewer packages
- **Compliance** - FIPS or specific compliance requirements

**3. Performance Priority:**
- **Fast startup** - Serverless, scale-to-zero workloads
- **Low memory** - High-density deployments
- **Balanced** - General purpose applications

**4. Build Requirements:**
- **Need build tools** - Native extensions, compilation during build
- **Runtime only** - Pre-compiled, no build tools needed

Please describe your use case or select from the options above.
```

**WAIT for user to provide their requirements.** Do NOT proceed until user describes their use case or selects options.

### Step 3: Evaluate Image Options

For each language, evaluate available variants:

**Image Variant Types:**

| Variant | Description | Best For |
|---------|-------------|----------|
| Full | Includes build tools, dev utilities | Development, native extensions |
| Minimal | Smaller base, essential packages only | Production, security-focused |
| Runtime | No build tools, runtime only | Pre-compiled apps, smallest size |

**Scoring Criteria:**

| Criteria | Weight (Production) | Weight (Development) |
|----------|---------------------|----------------------|
| Image Size | High | Low |
| Security (fewer packages) | High | Medium |
| Build Tools | Low | High |
| Startup Time | Medium | Low |
| LTS Status | High | Medium |

### Step 3.5: Dynamic Image Validation

Before presenting recommendations, validate with dynamic sources to provide accurate, real-time data.

#### Check if Skopeo is Available

First, verify skopeo is installed:

```bash
which skopeo
```

**If skopeo is NOT installed**, present:

```markdown
## Skopeo Required for Image Validation

To provide accurate image recommendations, I need `skopeo` to inspect container images.

**Skopeo is not installed.** This tool allows me to:
- Verify the image exists before recommending it
- Get exact image size (not estimates)
- Check architecture support (amd64, arm64)
- Show when the image was last built

**Install skopeo:**

| OS | Command |
|----|---------|
| Fedora/RHEL/CentOS | `sudo dnf install skopeo` |
| Ubuntu/Debian | `sudo apt install skopeo` |
| macOS (Homebrew) | `brew install skopeo` |

After installing, run `/recommend-image` again for enhanced recommendations.

**Continue without skopeo?**
- **yes** - Use static reference data only (less accurate)
- **install** - I'll install skopeo first
```

**WAIT for user to select an option.** Do NOT proceed until user chooses.

If user continues without skopeo, proceed with static data and note: "Image metadata from static reference (not verified)".

#### Skopeo Verification

For each candidate image, verify availability and get metadata:

```bash
# Verify image exists and get metadata
skopeo inspect docker://registry.access.redhat.com/ubi9/[candidate-image]
```

**Note:** The `docker://` transport is OCI-standard and works with Podman registries - it's not Docker-specific.

### Step 4: Present Recommendation

Format your recommendation:

```markdown
## Image Recommendation

Based on your requirements:

| Factor | Your Input |
|--------|------------|
| Language | [language] [version] |
| Framework | [framework or "None"] |
| Environment | [Production/Development/Edge] |
| Security | [Standard/Hardened/Compliance] |
| Priority | [startup/memory/balanced] |
| Build Tools | [needed/not needed] |

---

### Recommended Image

`registry.access.redhat.com/ubi9/[image-name]`

**Why this image:**
- [Reason 1 - matches primary requirement]
- [Reason 2 - matches secondary requirement]
- [Reason 3 - version/LTS consideration]

**Image Details:**
| Property | Value | Source |
|----------|-------|--------|
| Base | UBI 9 | Static |
| Variant | [Full/Minimal/Runtime] | Static |
| Size | [exact-size]MB | Skopeo |
| Built | [build-date] | Skopeo |
| Architecture | amd64, arm64 | Skopeo |
| LTS | [Yes/No - EOL date] | Static |

**Security Status:** [status-icon] [status-message]
- Last checked: [timestamp]
- Source: Red Hat Security Data API

*(If skopeo unavailable: "Image metadata from static reference - install skopeo for verified data")*

**Trade-offs:**
- [What you give up with this choice]
- [When you might choose differently]

---

### Alternative Options

| Image | Best For | Trade-off |
|-------|----------|-----------|
| `[alternative-1]` | [use case] | [trade-off] |
| `[alternative-2]` | [use case] | [trade-off] |

---

**Confirm this recommendation?**
- Type **yes** to use `[recommended-image]`
- Type **alternative N** to use an alternative
- Tell me if you have different requirements
```

**WAIT for user to confirm or select an alternative.** Do NOT save configuration until user explicitly confirms.

### Step 5: Handle Confirmation

**If user confirms:**

```markdown
## Image Selected

| Setting | Value |
|---------|-------|
| Builder Image | `[full-image-reference]` |
| Variant | [variant] |
| Rationale | [brief reason] |

Configuration saved. You can now:
- Run `/s2i-build` to build with this image
- Run `/containerize-deploy` for the full workflow
```

**If user selects alternative:**
Update the selection and confirm.

**If user has different requirements:**
Return to Step 2 with new inputs.

## Image Reference

### Quick Use-Case Matrix

| Use Case | Variant | Pattern |
|----------|---------|---------|
| Production | Minimal/Runtime | `ubi9/{lang}-{ver}-minimal` or `-runtime` |
| Development | Full | `ubi9/{lang}-{ver}` |
| Serverless | Smallest | Minimal variants or native builds |

**Framework-Specific (common):**
- **Quarkus**: `openjdk-21` (JVM) or Mandrel builder (native)
- **Spring Boot**: `openjdk-17-runtime` for production
- **Next.js/React**: `nodejs-20` with multi-stage build
- **Django/Flask**: `python-311` with `requirements.txt`

## Output Variables

After successful recommendation:

| Variable | Description | Example |
|----------|-------------|---------|
| `BUILDER_IMAGE` | Full image reference | `registry.access.redhat.com/ubi9/nodejs-20-minimal` |
| `IMAGE_VARIANT` | Variant type | `minimal` |
| `SELECTION_RATIONALE` | Why this image | "Minimal variant for production security" |
| `ALTERNATIVES` | Fallback options | `["ubi9/nodejs-20", "ubi9/nodejs-22-minimal"]` |
