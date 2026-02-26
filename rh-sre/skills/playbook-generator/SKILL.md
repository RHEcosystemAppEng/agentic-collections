---
name: playbook-generator
description: |
  **CRITICAL**: This skill ONLY GENERATES playbooks. It does NOT EXECUTE them. For execution, use /playbook-executor skill.

  Generate production-ready Ansible remediation playbooks for CVE vulnerabilities with Red Hat best practices, error handling, and Kubernetes safety patterns. Use this skill when you need to create remediation playbooks that follow Red Hat Lightspeed patterns and incorporate RHEL-specific considerations.

  This skill orchestrates MCP tools (create_vulnerability_playbook) while consulting documentation (cve-remediation-templates.md, package-management.md) to enhance playbooks with Red Hat best practices and RHEL-specific patterns.

  **IMPORTANT**: 
  - ALWAYS use this skill instead of calling create_vulnerability_playbook directly
  - NEVER execute playbooks using ansible-playbook CLI
  - ALWAYS delegate execution to /playbook-executor skill
---

# Ansible Playbook Generator Skill

This skill generates Ansible remediation playbooks for CVE vulnerabilities, applying Red Hat best practices, RHEL-specific patterns, and Kubernetes safety considerations.

**Integration with Remediator Agent**: The sre-agents:remediator agent (invoked) orchestrates this skill as part of its Step 4 (Generate Playbook) workflow. For standalone playbook generation, you can invoke this skill directly.

## When to Use This Skill

**🚨 CRITICAL SCOPE LIMITATION**: This skill **ONLY GENERATES** playbooks. It does **NOT EXECUTE** them.

**Use this skill directly when you need**:
- Generate a remediation playbook for a specific CVE
- Create batch remediation playbooks for multiple CVEs
- Apply Red Hat best practices to playbook generation
- Standalone playbook generation without full remediation workflow

**Do NOT use this skill when you need**:
- Execute playbooks → Use `/playbook-executor` skill instead
- Run ansible-playbook CLI → Use `/playbook-executor` skill via AAP MCP
- Monitor job execution → Use `/playbook-executor` skill instead

**Use the sre-agents:remediator agent when you need**:
- End-to-end CVE remediation (analysis → validation → playbook → execution → verification)
- Integrated impact analysis before playbook generation
- System context gathering and remediation strategy determination
- Execution guidance and verification workflows

**How they work together**: 
1. The sre-agents:remediator agent (invoked) orchestrates this skill after gathering system context
2. This skill generates the optimized playbook
3. The agent then invokes `/playbook-executor` skill for execution via AAP MCP
4. Finally, `/remediation-verifier` skill confirms success

## Workflow

### 1. Documentation Consultation

**CRITICAL**: Document consultation MUST happen BEFORE playbook generation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [cve-remediation-templates.md](../../docs/ansible/cve-remediation-templates.md) using the Read tool to understand playbook patterns for this CVE type:
   - Template 1: Package Update (user-space packages)
   - Template 2: Service Restart (configuration changes)
   - Template 3: Configuration File Update (system configs)
   - Template 4: Kernel Update with Reboot (kernel CVEs)
   - Template 5: SELinux Context Update (SELinux issues)
   - Template 6: Batch Remediation (multiple CVEs)

2. **Action**: Read [package-management.md](../../docs/rhel/package-management.md) using the Read tool for RHEL-specific update considerations:
   - DNF vs YUM (RHEL 7 vs 8/9)
   - Reboot detection patterns (`needs-restarting`)
   - Service restart after package updates
   - Repository and subscription management

3. **Output to user**: "I consulted [cve-remediation-templates.md](../../docs/ansible/cve-remediation-templates.md) and [package-management.md](../../docs/rhel/package-management.md) to understand playbook patterns and RHEL-specific best practices."


### 2. CVE Type Detection

Analyze CVE metadata to determine the appropriate playbook template:

```
CVE Type Detection Logic:
- Kernel CVE: Check if affected packages include "kernel", "vmlinuz", "grub"
  → Use Template 4 (Kernel Update with Reboot)

- Service Configuration: Check if CVE affects config files (sshd_config, httpd.conf)
  → Use Template 2 (Service Restart) or Template 3 (Config Update)

- SELinux Issue: Check if CVE description mentions SELinux, restorecon, semanage
  → Use Template 5 (SELinux Context Update)

- Multiple CVEs: If remediating 3+ CVEs simultaneously
  → Use Template 6 (Batch Remediation)

- Default: User-space package update
  → Use Template 1 (Package Update)
```

### 3. System Context Analysis

Analyze target systems to determine remediation patterns:

```
System Context Checks:
- RHEL Version: Detect RHEL 7 (use yum) vs RHEL 8/9 (use dnf)
- Kubernetes Deployment: Check if systems are K8s nodes → add pod eviction
- Environment: Production vs staging → adjust rollback/testing requirements
- Number of Systems: Single vs batch → optimize for parallelism
- Reboot Required: Kernel updates → add reboot orchestration
```

### 4. Playbook Generation

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation (see Step 1).

**MCP Tool**: `create_vulnerability_playbook` or `remediations__create_vulnerability_playbook` (from lightspeed-mcp)

**Parameters**:
- `cve_ids`: Array of CVE identifiers
  - Example: `["CVE-2024-1234"]`
  - Format: CVE-YYYY-NNNNN strings
- `system_ids`: Array of system UUIDs from Red Hat Lightspeed inventory
  - Example: `["uuid-1", "uuid-2"]`
  - Format: UUID strings (get from system-context skill)
- `auto_reboot`: Boolean controlling automatic reboot behavior
  - Example: `false` (we handle reboots explicitly in playbook)
  - Recommended: `false` to maintain control over reboot timing

**Expected Output**: Base Ansible playbook YAML that will be enhanced with patterns from documentation

### 5. Playbook Enhancement

Apply Red Hat best practices from documentation to the generated playbook:

**A. Pre-flight Checks** (from `package-management.md`):
```yaml
pre_tasks:
  - name: Verify system is RHEL
    assert:
      that:
        - ansible_distribution == "RedHat"
        - ansible_distribution_major_version in ["7", "8", "9"]
      fail_msg: "This playbook is for RHEL systems only"

  - name: Check system is registered to Red Hat
    command: subscription-manager status
    register: subscription_status
    failed_when: "'Overall Status: Current' not in subscription_status.stdout"
    changed_when: false
```

**B. Backup and Snapshot** (from `cve-remediation-templates.md`):
```yaml
  - name: Create backup point (RHEL 8/9)
    command: >
      snapshot create pre-{{ cve_id }}-{{ ansible_date_time.epoch }}
    when: ansible_distribution_major_version in ["8", "9"]
    ignore_errors: true
```

**C. Package Update** (from `package-management.md`):
```yaml
tasks:
  - name: Update vulnerable packages (RHEL 8/9)
    dnf:
      name: "{{ vulnerable_packages }}"
      state: latest
      update_cache: true
    when: ansible_distribution_major_version in ["8", "9"]
    register: package_update

  - name: Update vulnerable packages (RHEL 7)
    yum:
      name: "{{ vulnerable_packages }}"
      state: latest
      update_cache: true
    when: ansible_distribution_major_version == "7"
    register: package_update
```

**E. Reboot Detection** (from `package-management.md`):
```yaml
  - name: Check if reboot required (RHEL 8/9)
    command: needs-restarting -r
    register: reboot_required
    failed_when: false
    changed_when: reboot_required.rc == 1
    when: ansible_distribution_major_version in ["8", "9"]

  - name: Check if reboot required (RHEL 7)
    stat:
      path: /var/run/reboot-required
    register: reboot_required_file
    when: ansible_distribution_major_version == "7"
```

**F. Service Restart** (if no reboot needed):
```yaml
  - name: Restart affected services
    systemd:
      name: "{{ item }}"
      state: restarted
    loop: "{{ affected_services | default([]) }}"
    when:
      - not (reboot_required.changed | default(false))
      - affected_services is defined
```

**G. Audit Logging** (from `cve-remediation-templates.md`):
```yaml
  - name: Log remediation success
    lineinfile:
      path: /var/log/cve-remediation.log
      line: "{{ ansible_date_time.iso8601 }} - {{ cve_id }} remediated - {{ package_update.results | length }} packages updated"
      create: true

  - name: Notify if reboot required
    debug:
      msg: "REBOOT REQUIRED - Schedule maintenance window for {{ inventory_hostname }}"
    when: reboot_required.changed | default(false)
```

### 6. Playbook Validation

Validate the generated playbook:

```
Validation Checks:
✓ YAML syntax is valid (use ansible-playbook --syntax-check)
✓ All variable references are defined
✓ Pre-flight checks included (OS validation, subscription check)
✓ Backup/snapshot step present
✓ Package manager matches RHEL version (dnf for 8/9, yum for 7)
✓ Reboot detection logic present
✓ Service restart conditional on reboot status
✓ If K8s: Pod eviction before remediation
✓ If K8s: Node uncordon after remediation
✓ Audit logging included
✓ Error handling present (failed_when, ignore_errors where appropriate)
```

## Critical: Human-in-the-Loop Requirements

This skill generates code that will execute on production systems. **Explicit user confirmation is REQUIRED** before returning the playbook.

**Before Playbook Return** (REQUIRED):
1. **Display Playbook Preview**: Show complete playbook YAML to user
2. **Display Metadata**: Show CVE IDs, target systems, reboot requirements, Kubernetes considerations
3. **Ask for Confirmation**:
   ```
   ❓ Review the playbook above. This playbook will:
   - Update packages on N systems
   - Require reboot: [Yes/No]
   - Affect Kubernetes pods: [Yes/No]

   Should I provide this playbook for execution?

   Options:
   - "yes" or "proceed" - Provide playbook for execution
   - "modify" - Request changes to playbook
   - "abort" - Cancel playbook generation

   Please respond with your choice.
   ```
4. **Wait for Explicit Confirmation**: Do not provide playbook without "yes" or "proceed"

**Never assume approval** - always wait for explicit user confirmation before providing executable playbooks.

### 7. Return Playbook

**🚨 CRITICAL**: This skill **ONLY GENERATES** playbooks. It does **NOT EXECUTE** them.

**ONLY after receiving explicit user confirmation**, return the production-ready playbook with metadata:

```yaml
# Playbook metadata to return:
playbook:
  file: remediation-CVE-YYYY-NNNNN.yml
  path: playbooks/remediation/remediation-CVE-YYYY-NNNNN.yml  # Full path for playbook-executor template matching
  content: |
    [Complete YAML playbook]

  metadata:
    cve_ids: ["CVE-YYYY-NNNNN"]
    target_systems: ["uuid-1", "uuid-2"]
    rhel_versions_supported: ["7", "8", "9"]
    requires_reboot: true/false
    kubernetes_safe: true/false
    estimated_duration_minutes: 15
    risk_level: "medium"  # based on reboot requirement

  execution_notes:
    - "Test in staging environment first"
    - "Schedule maintenance window if reboot required"
    - "Ensure kubectl access if Kubernetes systems"
    - "Back up critical data before execution"
```

## Critical: Execution Handoff

**🚨 THIS SKILL DOES NOT EXECUTE PLAYBOOKS**

After generating the playbook, if the user requests execution:

❌ **WRONG** - Do NOT use `ansible-playbook` CLI:
```bash
ansible-playbook remediation.yml --check  # ❌ This skill cannot do this
```

✅ **CORRECT** - Delegate to the `/playbook-executor` skill:
```markdown
I've generated the remediation playbook. To execute it in dry-run mode, I'll invoke the playbook-executor skill:

[Invoke /playbook-executor skill with the playbook content]
```

**When user asks to execute**:
1. Save the playbook to a file (if needed for reference)
2. Invoke `/playbook-executor` skill with instruction:
   ```
   "Execute this playbook for CVE-XXXX-YYYY in dry-run mode using AAP job template [ID]. Monitor job status and report results."
   ```
3. The playbook-executor skill handles all execution via AAP MCP tools

**Never attempt to**:
- Run `ansible-playbook` command directly
- Execute playbooks via Shell/Bash tool
- Use any local Ansible execution method

**Always delegate execution to** `/playbook-executor` skill.

## Output Template

When completing playbook generation, provide output in this format:

```markdown
# Remediation Playbook Generated

## CVE Information
**CVE ID**: CVE-YYYY-NNNNN
**Target Systems**: N systems
**RHEL Versions**: 7, 8, 9
**Requires Reboot**: Yes/No
**Kubernetes Safe**: Yes/No

## Playbook Features
✓ Pre-flight checks (OS validation, subscription check)
✓ Backup/snapshot creation
✓ RHEL version-specific package management (dnf/yum)
✓ Reboot detection and handling
✓ Service restart logic
✓ Kubernetes pod eviction (if applicable)
✓ Error handling and rollback
✓ Audit logging

## Playbook File: remediation-CVE-YYYY-NNNNN.yml

```yaml
[Complete playbook YAML]
```

## Next Steps: Execution

**🔴 IMPORTANT**: Do NOT execute this playbook using `ansible-playbook` CLI.

**✅ To execute this playbook**, invoke the `/playbook-executor` skill:

```markdown
Ready to execute? The playbook-executor skill will:
1. Add this playbook to your AAP Git project
2. Create/use an AAP job template
3. Execute in dry-run mode first (if requested)
4. Launch actual execution (with your approval)
5. Monitor job status and report results

Would you like me to invoke the playbook-executor skill now?
Options:
- "yes" or "execute" - Invoke playbook-executor skill
- "dry-run first" - Execute in check mode first
- "save only" - Just save the playbook file for later
```

**Execution Flow**:
1. **This skill** → Generates playbook (DONE ✓)
2. **playbook-executor skill** → Executes via AAP MCP tools
3. **remediation-verifier skill** → Verifies success after execution

**Safety Notes**:
- Playbook includes rollback capability via snapshots (RHEL 8/9)
- Kubernetes pod eviction ensures zero-downtime updates
- Service restarts are conditional on reboot status
- All actions logged to /var/log/cve-remediation.log
```

## Examples

### Example 1: Simple Package CVE

**User Request**: "Generate playbook for CVE-2024-1234 affecting httpd package on 5 RHEL 8 systems"

**Skill Response**:
1. Consult `docs/ansible/cve-remediation-templates.md` (Template 1: Package Update)
2. Check `docs/rhel/package-management.md` (DNF workflows for RHEL 8)
3. Call `create_vulnerability_playbook` with CVE and system IDs
4. Enhance playbook with:
   - Pre-flight checks (OS validation)
   - Backup creation
   - DNF package update
   - Service restart (httpd)
   - Audit logging
5. Return production-ready playbook

### Example 2: Kernel CVE

**User Request**: "Generate playbook for kernel CVE on 10 RHEL nodes"

**Skill Response**:
1. Detect kernel CVE → Use Template 4 (Kernel Update with Reboot)
2. Consult `docs/rhel/package-management.md` for kernel update patterns
3. Call `create_vulnerability_playbook`
4. Enhance playbook with:
   - Pre-flight checks
   - Kernel package update
   - Reboot detection
   - Reboot execution (if needed)
   - Audit logging
5. Return production-ready kernel update playbook

### Example 3: Batch Remediation

**User Request**: "Generate playbook for CVE-2024-1234, CVE-2024-5678, CVE-2024-9012 on 20 web servers"

**Skill Response**:
1. Detect multiple CVEs → Use Template 6 (Batch Remediation)
2. Consult `docs/ansible/cve-remediation-templates.md` for batch patterns
3. Check `docs/rhel/package-management.md` for batch update considerations
4. Call `create_vulnerability_playbook` with multiple CVE IDs
5. Enhance playbook with:
   - Pre-flight checks
   - Batch package update (all affected packages)
   - Consolidated reboot detection
   - Service restart logic
   - Progress tracking
   - Audit logging with batch details
6. Return optimized batch playbook

## Error Handling

**CVE has no automated remediation**:
```
CVE-YYYY-NNNNN does not have an automated remediation playbook available in Red Hat Lightspeed.

Manual remediation required:
1. Affected packages: package-name-version
2. Recommended action: dnf update package-name
3. Verification: package-name --version

Would you like me to create a manual playbook template based on Red Hat best practices?
```

**Unsupported RHEL version**:
```
Target systems include RHEL 6, which is not supported by this skill.

Supported RHEL versions: 7, 8, 9

Please filter target systems to supported versions or consult Red Hat documentation for RHEL 6 remediation guidance.
```

**Kubernetes context missing**:
```
Target systems appear to be Kubernetes nodes but kubectl access is not configured.

To generate Kubernetes-safe playbooks, ensure:
1. kubectl is installed and configured
2. Access to cluster is available
3. Appropriate RBAC permissions for node operations

Proceeding with standard playbook (without pod eviction). Add pod eviction manually if needed.
```

## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed platform access

### Required MCP Tools
- `create_vulnerability_playbook` or `remediations__create_vulnerability_playbook` (from lightspeed-mcp) - Generate base remediation playbook from Red Hat Lightspeed
  - Parameters: cve_ids (array of strings), system_ids (array of UUID strings), auto_reboot (boolean)
  - Returns: Base Ansible playbook YAML for remediation

### Related Skills
- `cve-impact` - Provides CVE severity and risk assessment to inform playbook complexity
- `system-context` - Provides system inventory and deployment context for playbook targeting
- `remediation-verifier` - Verifies playbook execution success after deployment
- `playbook-executor` - Executes generated playbooks and tracks job status

### Reference Documentation
- [cve-remediation-templates.md](../../docs/ansible/cve-remediation-templates.md) - Ansible playbook templates for different CVE types
- [package-management.md](../../docs/rhel/package-management.md) - RHEL package management best practices (DNF vs YUM, reboot detection)

## Best Practices

1. **🚨 NEVER EXECUTE PLAYBOOKS** - This skill generates only. Always delegate execution to `/playbook-executor` skill
2. **Always consult documentation first** - Read [cve-remediation-templates.md] and [package-management.md] BEFORE calling MCP tools
3. **Detect CVE type** - Use appropriate template for kernel vs package vs service CVEs
4. **Check Kubernetes context** - Add pod eviction for K8s-deployed systems
5. **RHEL version awareness** - Use dnf for RHEL 8/9, yum for RHEL 7
6. **Include pre-flight checks** - Validate OS, subscription status before proceeding
7. **Add rollback capability** - Use snapshots, backups for safety
8. **Audit everything** - Log all actions to /var/log/cve-remediation.log
9. **Require user approval** - ALWAYS get explicit confirmation before providing playbooks
10. **Test first** - Always recommend testing in staging before production
11. **Clear handoff** - After generation, explicitly tell user to invoke `/playbook-executor` for execution

## Tools Reference

This skill primarily uses:
- `create_vulnerability_playbook` (remediations toolset) - Generate base playbook from Red Hat Lightspeed
- Read tool - Access documentation for best practices
  - `docs/ansible/cve-remediation-templates.md` - Playbook templates
  - `docs/rhel/package-management.md` - RHEL-specific patterns

All MCP tools are provided by the lightspeed-mcp server configured in `.mcp.json`.
All documentation is available in the `docs/` directory.

## Integration with Other Skills

- **cve-impact**: Provides CVE severity and risk assessment to inform playbook complexity
- **system-context**: Provides system inventory and deployment context for playbook targeting
- **remediation-verifier**: Verifies playbook execution success after deployment

**Orchestration Example** (from sre-agents:remediator agent - invoked):
1. Agent invokes cve-impact skill → Gets risk assessment
2. Agent gathers context → Determines deployment requirements
3. Agent invokes playbook-generator skill → Generates production-ready playbook
4. Agent provides execution guidance → User deploys playbook
5. Agent invokes remediation-verifier skill → Confirms success
