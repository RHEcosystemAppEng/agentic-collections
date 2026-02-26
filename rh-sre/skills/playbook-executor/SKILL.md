---
name: playbook-executor
description: |
  **CRITICAL**: This skill must be used for Ansible playbook execution via AAP. DO NOT use raw MCP tools directly.

  Execute Ansible remediation playbooks through AAP (Ansible Automation Platform) with comprehensive job management, dry-run capabilities, and detailed reporting. Use this skill after generating a playbook to execute it on production systems with proper validation and monitoring.

  This skill orchestrates AAP MCP tools (job_templates_launch_retrieve, jobs_retrieve, jobs_stdout_retrieve, jobs_job_events_list, jobs_job_host_summaries_list) to provide production-grade playbook execution with dry-run testing, real-time progress monitoring, and comprehensive reporting.

  **IMPORTANT**: ALWAYS use this skill instead of calling AAP MCP tools directly.
---

# AAP Playbook Executor Skill

This skill executes Ansible remediation playbooks through AAP (Ansible Automation Platform) with full job management capabilities.

**Integration with Remediator Agent**: The sre-agents:remediator agent orchestrates this skill as part of its Step 5 (Execute Playbook) workflow. For standalone playbook execution, you can invoke this skill directly.

## Prerequisites

**Required MCP Servers**: `aap-mcp-job-management`, `aap-mcp-inventory-management` ([setup guide](https://docs.redhat.com/))

**Required MCP Tools**:
- `job_templates_list` (from aap-mcp-job-management) - List job templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Get project name and scm_url for Git Flow
- `job_templates_launch_retrieve` (from aap-mcp-job-management) - Launch jobs
- `jobs_retrieve` (from aap-mcp-job-management) - Get job status
- `jobs_stdout_retrieve` (from aap-mcp-job-management) - Get console output
- `jobs_job_events_list` (from aap-mcp-job-management) - Get task events
- `jobs_job_host_summaries_list` (from aap-mcp-job-management) - Get host statistics
- `inventories_list` (from aap-mcp-inventory-management) - List inventories
- `hosts_list` (from aap-mcp-inventory-management) - List inventory hosts

**Required Environment Variables**:
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (must point to the AAP MCP gateway)
- `AAP_API_TOKEN` - AAP API authentication token

### Prerequisite Validation

**CRITICAL**: Before executing operations, invoke the [mcp-aap-validator](../mcp-aap-validator/SKILL.md) skill to verify AAP MCP server availability.

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

**How to invoke**:
```
Use the Skill tool:
  skill: "mcp-aap-validator"
```

**Handle validation result**:
- **If validation PASSED**: Continue with playbook execution workflow
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, provide setup instructions from validator

**Human Notification on Failure**:
If prerequisites are not met:
- ❌ "Cannot proceed: AAP MCP servers are not available"
- 📋 "Setup required: Configure AAP_MCP_SERVER and AAP_API_TOKEN environment variables"
- ❓ "How would you like to proceed? (setup now / skip / abort)"
- ⏸️ Wait for user decision

## When to Use This Skill

**Use this skill directly when you need**:
- Execute a previously generated Ansible playbook via AAP
- Track the status of a running AAP job
- Monitor playbook job completion
- Run dry-run (check mode) before production execution
- Verify playbook execution succeeded

**Use the sre-agents:remediator agent when you need**:
- Full remediation workflow including playbook execution
- Integrated CVE analysis → playbook generation → execution → verification
- End-to-end remediation orchestration

**How they work together**: The sre-agents:remediator agent invokes this skill after generating a remediation playbook, managing the full workflow from analysis to verification.

## Workflow

### Phase 0: Validate AAP MCP Prerequisites

**Action**: Invoke the [mcp-aap-validator](../mcp-aap-validator/SKILL.md) skill

**Note**: Can skip if validation was performed earlier in this session and succeeded.

**How to invoke**:
```
Use the Skill tool:
  skill: "mcp-aap-validator"
```

**Handle validation result**:
- **If validation PASSED**: Continue to Phase 1
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, user must set up AAP MCP servers

### Phase 1: Job Template Selection and Playbook Preparation

**Goal**: Identify an AAP job template suitable for executing the remediation playbook, or prepare the playbook for execution via git override or template creation.

**Input**: Playbook content and metadata from playbook-generator (filename, CVE ID, target systems). Playbook path is derived from metadata: `playbooks/remediation/<filename>` (e.g., `playbooks/remediation/remediation-CVE-2025-49794.yml` or `playbooks/remediation/remediation-CVE-2025-49794-playbook.yml`).

#### Step 1.1: Derive Playbook Path

From playbook metadata (filename from playbook-generator):
- Use convention `playbooks/remediation/<filename>`
- Support both `remediation-CVE-*.yml` and `remediation-CVE-*-playbook.yml` patterns.

#### Step 1.2: List and Filter Templates

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 50 (retrieve up to 50 templates)
- `search`: "" (search for all templates)

For each template in results, call `job_templates_retrieve(id)` to get full details. Apply [job-template-remediation-validator](../job-template-remediation-validator/SKILL.md) criteria (inventory, project, playbook, credentials, become_enabled). Build two lists:
- **exact_match**: `template.playbook` equals `our_playbook_path` (normalize slashes; match if equal or basenames match)
- **compatible_other**: Passes validation but different playbook path

**Path normalization**: Normalize slashes, handle `playbooks/remediation/` prefix. Match if `template.playbook` equals `our_playbook_path` or if basenames match.

#### Step 1.3: Scenario Selection

**Scenario 1 - Same playbook path** (exact_match not empty):

Prompt:
```
Found template [name] (ID: X) with matching playbook path. The project may need to be updated with the latest playbook.

Options:
(A) Override: I'll add the playbook to the project via git. You sync the AAP project, then confirm.
(B) Manual: You add the playbook and sync. Confirm when done.

❓ Choose (A) or (B):
```

- **If A**: Execute Git Flow (see Git Flow section below). Wait for user: "Sync complete" or "done".
- **If B**: Wait for user confirmation.

**Scenario 2 - Different playbook path** (compatible_other not empty, exact_match empty):

Prompt:
```
Found template [name] (ID: X) pointing to [template.playbook]. We can use it by replacing that playbook with our content.

Note: Template name may not match the CVE being remediated.

❓ Proceed with override?
- "yes" or "proceed" - Replace playbook and continue
- "no" - Skip to template creation (invoke job-template-creator)

Please respond with your choice.
```

- **If yes**: Git Flow - write playbook content to `template.playbook` path in repo. Commit, push. Wait for sync confirmation.
- **If no**: Fall through to Scenario 3.

**Scenario 3 - No suitable template** (exact_match and compatible_other both empty, or user chose "no" in Scenario 2):

Invoke the **job-template-creator** skill:
```
Skill: job-template-creator
Instruction: "Create a job template for this remediation playbook. Playbook: [content]. Filename: [filename]. Path: [our_playbook_path]. CVE: [cve_id]. Target systems: [list]."
```

The job-template-creator skill guides the user through: (1) Adding playbook to Git repository, (2) Syncing AAP project, (3) Creating job template via AAP Web UI with correct path, inventory, credentials, privilege escalation.

After job-template-creator completes, retrieve the template ID (from skill output or user confirmation). Invoke job-template-remediation-validator to validate the newly created template. If passed, proceed to Phase 3 (Dry-Run). If failed, report issues and ask user to fix in AAP Web UI.

**Multiple matches**: If multiple exact matches, present list and ask user to choose by number. If multiple different-path matches, prefer by project name containing "remediation" or "CVE", else first.

#### Git Flow (for Scenario 1 Override and Scenario 2)

**Prerequisite**: Ask user for the local path to the Git repository for the selected project. Use `projects_list` to get project name and `scm_url` for the template's project; display these to help user identify the correct repo:
```
What is the local path to the Git repository for project [Project Name] (scm_url)?
```

**Steps**:
1. Write playbook content to `<user_provided_path>/<target_path>`
2. Use Run tool: `git add <target_path>`
3. **Checkpoint**: Display summary of changes (file path, diff or file size) and ask:
   ```
   Ready to commit and push these changes?
   Reply 'yes' or 'proceed' to continue, or 'abort' to cancel.
   ```
4. If confirmed: `git commit -m "Add/update remediation playbook for CVE-YYYY-NNNNN"`
5. `git push origin main` (or branch from project's scm_branch if available from projects_list)

**Note**: Git must be configured (user, remote). Use Run tool for git commands.

**After push**: "I've pushed the playbook. Sync the AAP project: Automation Execution > Projects > [Project] > Sync. Reply 'sync complete' when done."

### Phase 3: Dry-Run Execution (Recommended)

**Goal**: Test playbook in check mode before actual execution to simulate changes.

#### Step 3.1: Display Playbook Preview

Show user the playbook structure and explain tasks:

```markdown
# Playbook Preview

**Playbook**: remediation-CVE-2025-49794.yml
**Target Systems**: 5 systems

## Tasks Overview:
1. **Gather Facts** - Collect system information
2. **Check Disk Space** - Ensure sufficient space for updates (>500MB)
3. **Backup Configuration** - Snapshot critical configs
4. **Update Package: httpd** - Upgrade to version 2.4.57-8.el9
5. **Restart Service: httpd** - Apply changes
6. **Verify Service Status** - Confirm httpd is running
7. **Update Audit Log** - Record remediation event

**Estimated Duration**: 3-5 minutes per system
**Requires Reboot**: No
**Downtime**: Brief (~10 seconds during service restart)
```

#### Step 3.2: Offer Dry-Run

```
⚠️ Recommended: Run dry-run first

Dry-run mode (--check) simulates changes without applying them.
This helps identify:
- Package availability issues
- Permission problems
- Configuration conflicts
- Unexpected side effects

❓ Run dry-run before actual execution?
- "yes" - Run dry-run first (recommended)
- "no" - Skip to actual execution
- "abort" - Cancel execution

Please respond with your choice.
```

#### Step 3.3: Launch Dry-Run Job

**ONLY if user confirms**, proceed with dry-run.

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**:
```json
{
  "id": "10",
  "requestBody": {
    "job_type": "check",
    "extra_vars": {
      "target_cve": "CVE-2025-49794",
      "remediation_mode": "automated"
    },
    "limit": "prod-web-01,prod-web-02,prod-web-03"
  }
}
```

**Key Parameter**: `job_type: "check"` - Runs Ansible in check mode (dry-run)

**Expected Output**:
```json
{
  "job": 1234,
  "status": "pending",
  "url": "/api/controller/v2/jobs/1234/"
}
```

#### Step 3.4: Monitor Dry-Run Progress

Poll job status with `jobs_retrieve` every 2 seconds:

```
⏳ Dry-run in progress...

Job ID: 1234
Status: running
Elapsed: 0m 45s

[Live progress updates from jobs_job_events_list]
- ✓ Gathering Facts (completed)
- ✓ Checking Disk Space (completed)
- ⏳ Simulating Package Update (running)
```

#### Step 3.5: Display Dry-Run Results

**MCP Tool**: `jobs_stdout_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1234" (job ID)
- `format`: "txt" (plain text output)

Get per-host summary:

**MCP Tool**: `jobs_job_host_summaries_list` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1234"

**Display Format**:
```markdown
# Dry-Run Results

## Job Summary
**Job ID**: 1234
**Status**: ✓ Successful (Check Mode)
**Duration**: 2m 15s
**Completed**: 2024-01-20 15:32:17 UTC

## Simulated Changes
| Host | Would Change | OK | Failed | Status |
|------|--------------|-----|--------|--------|
| prod-web-01 | 3 | 8 | 0 | ✓ Ready |
| prod-web-02 | 3 | 8 | 0 | ✓ Ready |
| prod-web-03 | 3 | 8 | 0 | ✓ Ready |

## Changes That Would Be Made:
1. **httpd package** - Would update from 2.4.53-7.el9 to 2.4.57-8.el9
2. **httpd service** - Would restart
3. **audit log** - Would add remediation entry

## Dry-Run Output:
<details>
<summary>Click to expand full output</summary>

[Full stdout from jobs_stdout_retrieve]

</details>

✓ No errors detected in dry-run
✓ All systems passed pre-flight checks
```

#### Step 3.6: Proceed to Actual Execution?

```
❓ Dry-run completed successfully. Proceed with actual execution?

Options:
- "yes" or "execute" - Proceed with actual remediation
- "review" - Show dry-run output again
- "abort" - Cancel execution

Please respond with your choice.
```

### Phase 4: Actual Execution

**ONLY execute if user explicitly confirms** (either after dry-run or directly if they skipped dry-run).

#### Step 4.1: Final Confirmation

```
⚠️ CRITICAL: Playbook Execution Confirmation Required

This playbook will:
- Execute on: 3 production systems
- Update packages: httpd (2.4.53-7.el9 → 2.4.57-8.el9)
- Restart services: httpd
- Estimated downtime: ~10 seconds per system
- Requires reboot: No

Job Template: CVE Remediation Template (ID: 10)
AAP URL: https://aap.example.com/jobs/

❓ Execute this playbook now?

Options:
- "yes" or "execute" - Proceed with execution
- "abort" - Cancel execution

Please respond with your choice.
```

Wait for explicit "yes" or "execute" response.

#### Step 4.2: Launch Production Job

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**:
```json
{
  "id": "10",
  "requestBody": {
    "job_type": "run",
    "extra_vars": {
      "target_cve": "CVE-2025-49794",
      "remediation_mode": "automated",
      "verify_after": true
    },
    "limit": "prod-web-01,prod-web-02,prod-web-03"
  }
}
```

**Key Parameter**: `job_type: "run"` - Runs Ansible in execution mode (actual changes)

**Expected Output**:
```json
{
  "job": 1235,
  "status": "pending",
  "url": "/api/controller/v2/jobs/1235/"
}
```

#### Step 4.3: Monitor Execution Progress

**Polling Strategy**:
1. Call `jobs_retrieve(id=job_id)` every 2 seconds
2. Get task events with `jobs_job_events_list(id=job_id)` for progress updates
3. Display real-time task completion status
4. Continue until status is "successful", "failed", or "error"

**Progress Display**:
```
⏳ Execution in progress...

Job ID: 1235
Status: running
Elapsed: 1m 23s
AAP URL: https://aap.example.com/#/jobs/playbook/1235

Recent Events:
- ✓ Gathering Facts (completed - all hosts)
- ✓ Check Disk Space (completed - all hosts)
- ✓ Backup Configuration (completed - all hosts)
- ⏳ Update Package: httpd (running - prod-web-01, prod-web-02)
  └─ prod-web-01: Installing httpd-2.4.57-8.el9...
  └─ prod-web-02: Installing httpd-2.4.57-8.el9...
- ⏸  Restart Service: httpd (pending)
```

**Update every 2 seconds** until completion.

### Phase 5: Execution Report

**Goal**: Generate comprehensive report with job details, per-host results, and full output.

#### Step 5.1: Gather Job Details

**MCP Tool**: `jobs_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1235"

**Expected Output**:
```json
{
  "id": 1235,
  "name": "CVE Remediation Template",
  "status": "successful",
  "started": "2024-01-20T15:35:02Z",
  "finished": "2024-01-20T15:40:25Z",
  "elapsed": 323.45,
  "job_template": 10,
  "inventory": 1,
  "limit": "prod-web-01,prod-web-02,prod-web-03",
  "playbook": "playbooks/remediation/remediation-CVE-2025-49794.yml"
}
```

#### Step 5.2: Get Per-Host Statistics

**MCP Tool**: `jobs_job_host_summaries_list` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1235"

**Expected Output**:
```json
{
  "results": [
    {
      "host_name": "prod-web-01",
      "ok": 8,
      "changed": 3,
      "failed": 0,
      "unreachable": 0
    },
    {
      "host_name": "prod-web-02",
      "ok": 8,
      "changed": 3,
      "failed": 0,
      "unreachable": 0
    },
    {
      "host_name": "prod-web-03",
      "ok": 5,
      "changed": 0,
      "failed": 1,
      "unreachable": 0
    }
  ]
}
```

#### Step 5.3: Get Task Timeline

**MCP Tool**: `jobs_job_events_list` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1235"

**Expected Output**: List of task events with timestamps, task names, and status per host.

#### Step 5.4: Get Full Console Output

**MCP Tool**: `jobs_stdout_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: "1235"
- `format`: "txt"

**Expected Output**: Complete Ansible playbook execution output.

#### Step 5.5: Generate Comprehensive Report

Format all gathered data into structured report:

```markdown
# Playbook Execution Report

## Job Summary
**Job ID**: 1235
**Status**: ✅ Successful
**Duration**: 5m 23s
**Started**: 2024-01-20 15:35:02 UTC
**Completed**: 2024-01-20 15:40:25 UTC
**Job Template**: CVE Remediation Template
**Playbook**: playbooks/remediation/remediation-CVE-2025-49794.yml
**AAP URL**: [View in AAP](https://aap.example.com/#/jobs/playbook/1235)

## Per-Host Results
| Host | OK | Changed | Failed | Unreachable | Status |
|------|-----|---------|--------|-------------|--------|
| prod-web-01 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-02 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-03 | 8 | 3 | 0 | 0 | ✅ Success |

**Summary**: 3 of 3 hosts successfully remediated

## Task Timeline
1. ✅ Gather Facts (2s)
2. ✅ Check disk space (1s)  
3. ✅ Backup configuration (3s)
4. ✅ Update package httpd (45s)
   - prod-web-01: 2.4.53-7.el9 → 2.4.57-8.el9
   - prod-web-02: 2.4.53-7.el9 → 2.4.57-8.el9
   - prod-web-03: 2.4.53-7.el9 → 2.4.57-8.el9
5. ✅ Restart httpd service (15s)
6. ✅ Verify service status (2s)
7. ✅ Update audit log (1s)

## Full Console Output
<details>
<summary>Click to expand (187 lines)</summary>

[Full stdout from jobs_stdout_retrieve]

</details>

## Next Steps
1. ✅ All systems successfully remediated
2. ☐ Verify remediation with remediation-verifier skill
3. ☐ Update vulnerability tracking system
4. ☐ Schedule follow-up verification in 24-48 hours

---

**Recommendation**: Run remediation-verifier skill to confirm CVE status has been updated in Red Hat Lightspeed.
```

### Phase 6: Error Handling

**If job status is "failed" or "error"**, provide detailed troubleshooting.

#### Step 6.1: Parse Error Output

**MCP Tool**: `jobs_stdout_retrieve` (from aap-mcp-job-management)

Analyze output for common error patterns:

**Error Categories**:
1. **Connection Failures**: SSH timeout, host unreachable, authentication failed
2. **Permission Errors**: sudo required, insufficient privileges, SELinux denials
3. **Package Manager Issues**: repo unavailable, package not found, dependency conflicts
4. **Service Failures**: service not found, restart failed, timeout
5. **Disk Space**: insufficient space for updates
6. **General Failures**: playbook syntax errors, task failures

#### Step 6.2: Generate Error Report

```markdown
# Playbook Execution Failed

## Job Summary
**Job ID**: 1235
**Status**: ❌ Failed
**Duration**: 2m 45s
**Started**: 2024-01-20 15:35:02 UTC
**Failed At**: 2024-01-20 15:37:47 UTC
**Job Template**: CVE Remediation Template
**AAP URL**: [View in AAP](https://aap.example.com/#/jobs/playbook/1235)

## Per-Host Results
| Host | OK | Changed | Failed | Unreachable | Status |
|------|-----|---------|--------|-------------|--------|
| prod-web-01 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-02 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-03 | 5 | 0 | 1 | 0 | ❌ Failed |

**Summary**: 2 of 3 hosts succeeded, 1 failed

## Failed Tasks Details

### Host: prod-web-03

**Task**: Restart httpd service
**Error**: "Failed to restart httpd.service: Unit httpd.service not found."

**Error Category**: Service Failure

**Root Cause**: The httpd service is not installed or not recognized by systemd.

**Troubleshooting Steps**:
1. Check if httpd is installed:
   ```bash
   ssh prod-web-03 'rpm -q httpd'
   ```
2. If not installed, the package update may have failed:
   ```bash
   ssh prod-web-03 'dnf info httpd'
   ```
3. Check systemd service status:
   ```bash
   ssh prod-web-03 'systemctl status httpd'
   ```
4. Review package manager logs:
   ```bash
   ssh prod-web-03 'tail -50 /var/log/dnf.log'
   ```

**Recommended Action**: 
- Verify httpd package installation on prod-web-03
- Check if package update completed successfully
- Manually install httpd if needed: `dnf install httpd`
- Relaunch job for failed host only

## Console Output (Last 50 Lines)
<details>
<summary>Click to expand error context</summary>

[Relevant error output from jobs_stdout_retrieve]

</details>

## Relaunch Options

Would you like to:
1. **Relaunch for failed hosts only** - Run job again with limit="prod-web-03"
2. **Fix issues manually and relaunch** - Resolve problems first, then relaunch
3. **View full job output** - See complete execution logs
4. **Abort** - Stop remediation workflow

Please choose an option (1-4):
```

#### Step 6.3: Offer Relaunch

If user chooses to relaunch:

**MCP Tool**: `jobs_relaunch_retrieve` (from aap-mcp-job-management)

**Parameters**:
```json
{
  "id": "1235",
  "requestBody": {
    "hosts": "failed",
    "job_type": "run"
  }
}
```

This relaunches the job for only the failed hosts.

## Output Templates

### Success Template

```markdown
✅ Playbook Execution Successful

Job ID: 1235
Duration: 5m 23s
Systems Remediated: 3 of 3

View full report above for details.

Next Steps:
- Run remediation-verifier skill to confirm CVE resolution
- Update vulnerability tracking system
- Monitor systems for 24-48 hours

AAP URL: https://aap.example.com/#/jobs/playbook/1235
```

### Partial Success Template

```markdown
⚠️ Playbook Execution Completed with Failures

Job ID: 1235
Duration: 2m 45s
Systems Remediated: 2 of 3
Failed Systems: prod-web-03

See error details above for troubleshooting steps.

Options:
- Relaunch for failed hosts
- Manual remediation
- Skip failed hosts

AAP URL: https://aap.example.com/#/jobs/playbook/1235
```

### Failure Template

```markdown
❌ Playbook Execution Failed

Job ID: 1235
Duration: 1m 15s
Systems Remediated: 0 of 3

Critical errors prevented execution.
See error details above for troubleshooting.

AAP URL: https://aap.example.com/#/jobs/playbook/1235
```

## Examples

### Example 1: Full Workflow with Dry-Run

**User Request**: "Execute the CVE-2025-49794 remediation playbook"

**Skill Response**:

1. **Validate AAP Prerequisites**:
   - Invoke mcp-aap-validator skill → PASSED

2. **List Job Templates**:
   - Call `job_templates_list()` → Found 2 templates
   - Filter compatible templates → 1 matches requirements

3. **User Selects Template**:
   ```
   Found 1 compatible job template:
   1. "CVE Remediation Template" (ID: 10)
   
   Select template (1) or "create" for new: 1
   ```

4. **Playbook Preparation**:
   ```
   Guide user to add playbook to Git:
   - Commands provided
   - User syncs AAP project
   - Verification: Playbook available ✓
   ```

5. **Offer Dry-Run**:
   ```
   Run dry-run first? yes
   ```

6. **Execute Dry-Run**:
   - Launch with `job_type="check"`
   - Monitor progress → COMPLETED
   - Display dry-run results:
     ```
     Would change 3 tasks on 3 hosts
     No errors detected
     ```

7. **Proceed to Actual Execution**:
   ```
   Proceed with actual execution? yes
   ```

8. **Execute Playbook**:
   - Launch with `job_type="run"`
   - Monitor progress → COMPLETED
   - Generate report:
     ```
     ✅ 3 of 3 hosts successfully remediated
     Duration: 5m 23s
     ```

9. **Suggest Verification**:
   ```
   Recommend: Run remediation-verifier skill to confirm CVE resolution
   ```

### Example 2: Handle Execution Failure

**User Request**: "Execute remediation playbook"

**Skill Response**:

1-7. [Same as Example 1 through execution]

8. **Execute Playbook**:
   - Launch job → FAILED on 1 of 3 hosts
   - Generate error report:
     ```
     ❌ prod-web-03 failed
     Error: httpd service not found
     Troubleshooting steps provided
     ```

9. **Offer Relaunch**:
   ```
   Relaunch for failed host only? yes
   ```

10. **Relaunch Job**:
    - Call `jobs_relaunch_retrieve` with hosts="failed"
    - Monitor → COMPLETED
    - Final report:
      ```
      ✅ All 3 hosts successfully remediated (1 after retry)
      ```

### Example 3: Skip Dry-Run

**User Request**: "Execute playbook directly, skip dry-run"

**Skill Response**:

1-4. [Same as Example 1 through template selection]

5. **Offer Dry-Run**:
   ```
   Run dry-run first? no
   ```

6. **Final Confirmation**:
   ```
   ⚠️ Execute on production without dry-run?
   This will make changes immediately.
   Confirm: yes
   ```

7. **Execute Playbook**:
   - Launch with `job_type="run"`
   - Monitor and report as in Example 1

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - AAP job management and execution
- `aap-mcp-inventory-management` - AAP inventory management

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management) - List templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Get project name and scm_url for Git Flow
- `job_templates_launch_retrieve` (from aap-mcp-job-management) - Launch jobs
- `jobs_retrieve` (from aap-mcp-job-management) - Get job status
- `jobs_stdout_retrieve` (from aap-mcp-job-management) - Get console output
- `jobs_job_events_list` (from aap-mcp-job-management) - Get task events
- `jobs_job_host_summaries_list` (from aap-mcp-job-management) - Get host statistics
- `inventories_list` (from aap-mcp-inventory-management) - List inventories
- `hosts_list` (from aap-mcp-inventory-management) - List hosts

### Related Skills
- `mcp-aap-validator` - **PREREQUISITE** - Validates AAP MCP servers (invoke in Phase 0)
- `job-template-remediation-validator` - Validates job template meets remediation requirements before execution
- `job-template-creator` - Creates/guides AAP job template setup
- `playbook-generator` - Generates playbooks for execution
- `remediation-verifier` - Verifies success after execution

### Reference Documentation
- [AAP Job Execution Guide](../../docs/ansible/aap-job-execution.md) - AAP job execution best practices
- [Playbook Integration with AAP](../../docs/ansible/playbook-integration-aap.md) - Playbook-to-AAP workflow

## Critical: Human-in-the-Loop Requirements

This skill executes code on production systems. **Explicit user confirmation is REQUIRED** at multiple stages.

**Before Git commit/push** (Scenario 1 Override, Scenario 2):
1. **Display change summary**: File path, diff or file size
2. **Ask for confirmation**: "Ready to commit and push these changes? Reply 'yes' or 'proceed' to continue, or 'abort' to cancel."
3. **Wait for explicit "yes" or "proceed"**: Do not commit/push without confirmation

**Before Dry-Run Execution** (if user chooses dry-run):
1. **Display Playbook Preview**: Show tasks and explain changes
2. **Ask for Dry-Run Confirmation**:
   ```
   ❓ Run dry-run to simulate changes?
   
   Options:
   - "yes" - Run dry-run (recommended)
   - "no" - Skip to actual execution
   - "abort" - Cancel

   Please respond with your choice.
   ```
3. **Wait for Explicit Response**: Do not proceed without confirmation

**Before Actual Execution** (REQUIRED):
1. **Display Execution Summary**: Show systems, changes, downtime estimate
2. **Ask for Final Confirmation**:
   ```
   ⚠️ CRITICAL: Execute playbook on production systems?
   
   This will make real changes to N systems.
   
   Options:
   - "yes" or "execute" - Proceed
   - "abort" - Cancel
   
   Please respond with your choice.
   ```
3. **Wait for Explicit "yes" or "execute"**: Do not proceed without confirmation

**Never assume approval** - always wait for explicit user confirmation before executing playbooks.

## Best Practices

1. **Always validate AAP prerequisites** - Invoke mcp-aap-validator in Phase 0
2. **Recommend dry-run** - Offer check mode before production execution
3. **Filter compatible templates** - Check inventory, project, and credentials match
4. **Monitor in real-time** - Display task progress during execution
5. **Comprehensive reporting** - Include per-host stats, task timeline, full output
6. **Error categorization** - Parse errors and provide specific troubleshooting
7. **Relaunch capability** - Offer to retry failed hosts
8. **Link to AAP** - Provide direct URL to job in AAP Web UI
9. **Suggest verification** - Always recommend remediation-verifier after success
10. **Document job details** - Save job ID and template info for audit trail

## Integration with Other Skills

- **playbook-generator**: Generates playbooks that this skill executes
- **job-template-creator**: Creates AAP job templates when needed
- **remediation-verifier**: Verifies success after this skill completes execution
- **sre-agents:remediator agent**: Orchestrates full workflow including playbook execution

**Orchestration Example** (from sre-agents:remediator agent):
1. Agent invokes playbook-generator skill → Creates playbook YAML
2. playbook-generator asks for confirmation → User approves playbook content
3. Agent invokes playbook-executor skill (this skill) → Execution workflow
4. Skill guides template selection → User selects or creates template
5. Skill offers dry-run → User runs check mode
6. Skill asks for execution confirmation → User approves
7. Skill executes and monitors → Reports completion
8. Agent invokes remediation-verifier skill → Confirms CVE resolved

**Note**: Both playbook-generator and playbook-executor require separate confirmations for different purposes:
- playbook-generator: Confirms playbook content is acceptable
- playbook-executor: Confirms execution on production systems is approved

This two-step approval ensures user control over both what to run and when to run it.
