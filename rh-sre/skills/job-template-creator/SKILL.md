---
name: job-template-creator
description: |
  Create AAP (Ansible Automation Platform) job templates for executing playbooks. Use when users request:
  - "Create a job template for this playbook"
  - "Set up a template to run remediation playbooks"
  - "Configure AAP to execute this playbook"
  - "Add a new job template for CVE remediation"
  
  This skill guides through adding playbooks to Git projects and creating job templates via AAP Web UI.
model: inherit
color: blue
---

# AAP Job Template Creator Skill

This skill helps SREs create AAP job templates for executing Ansible playbooks, particularly for CVE remediation workflows.

## Prerequisites

**Required AAP Components**:
- AAP (Ansible Automation Platform) instance with API access
- Projects configured with playbooks
- Inventories with target hosts
- Credentials for authentication

**Required MCP Servers**: `aap-mcp-job-management` ([setup guide](https://docs.redhat.com/))

**Currently Available MCP Tools** (read-only):
- `job_templates_list` - List existing templates
- `job_templates_retrieve` - Get template details
- `projects_list` - List available projects
- `inventories_list` - List available inventories

**Missing MCP Tools** (needed for creation):
- ⚠️ `job_templates_create` - **NOT CURRENTLY AVAILABLE**
- ⚠️ `job_templates_update` - **NOT CURRENTLY AVAILABLE**

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
- **If validation PASSED**: Continue with job template creation workflow
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, provide setup instructions from validator

## Current Limitation: No Create Tools Available

⚠️ **IMPORTANT**: The current AAP MCP implementation does **NOT** include tools to create job templates programmatically. The available MCP tools are read-only (list, retrieve, launch).

**Current Approach**:
- Job templates must be created through the **AAP Web UI**
- This skill provides step-by-step instructions for Web UI creation
- Future MCP tool additions will enable programmatic template creation

This skill documents both the **current manual workflow** and the **intended automated workflow** for when creation tools become available.

## When to Use This Skill

**Use this skill when you need**:
- Create a new job template for a remediation playbook
- Configure AAP to execute dynamically generated playbooks
- Set up templates for CVE remediation workflows
- Automate job template creation as part of remediation setup

**Do NOT use this skill when**:
- Job templates already exist (use `playbook-executor` skill instead)
- Only need to execute existing templates (use `job_templates_launch_retrieve`)
- Need to modify existing templates (requires AAP Web UI currently)

## Invocation from playbook-executor

When invoked from the [playbook-executor](../playbook-executor/SKILL.md) skill (Scenario 3 - No suitable template), this skill receives playbook content in context. The playbook-executor invokes with an instruction such as:

```
Create a job template for this remediation playbook. Playbook: [content]. Filename: [filename]. Path: [our_playbook_path]. CVE: [cve_id]. Target systems: [list].
```

**When playbook content is provided**:
- Use the provided content for Phase 1 (Prepare Playbook in Git) instead of asking the user to supply it
- Write the playbook to the specified path in the user's Git repository (ask for repo path if not provided)
- Follow the Git flow: add, commit (with checkpoint for confirmation), push
- Then guide template creation via AAP Web UI (Phase 4)
- **Output**: Include the created template ID and name in the final report so playbook-executor can retrieve and validate it

**Phase 0 - Check context**: If playbook content is provided by the invoking skill, execute the git flow (write, add, commit with confirmation checkpoint, push) before guiding template creation. Otherwise, use the existing manual flow where the user supplies the playbook.

## Workflow

### Phase 0: Validate AAP MCP Prerequisites

**Action**: Invoke the [mcp-aap-validator](../mcp-aap-validator/SKILL.md) skill

**Note**: Can skip if validation was performed earlier in this session and succeeded. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

**How to invoke**:
```
Use the Skill tool:
  skill: "mcp-aap-validator"
```

**Handle validation result**:
- **If validation PASSED**: Continue to Phase 1
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, user must set up AAP MCP servers

### Phase 1: Prepare Playbook in Git Project

**Goal**: Add your remediation playbook to a Git repository that AAP can access.

**Prerequisites**:
- You have a remediation playbook file ready (e.g., `remediation-CVE-2025-49794.yml`)
- Git is installed and configured
- You have access to a Git repository (GitHub, GitLab, Bitbucket, etc.)

**Choose your approach**:

#### Option A: Add to Existing Git Project

If you already have a Git repository configured in AAP:

**Step 1: Identify Your Git Repository**

Ask the user:
```
❓ Where is your playbooks Git repository?

Please provide:
1. Repository URL (e.g., https://github.com/org/playbooks.git)
2. Local path (if already cloned)
3. Or: "I don't have one" (to create new repository)
```

**Step 2: Clone or Navigate to Repository**

If not already cloned:
```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>
```

If already cloned:
```bash
cd /path/to/your/playbooks-repo
```

**Step 3: Add Playbook to Repository**

```bash
# Create playbooks directory if it doesn't exist
mkdir -p playbooks/remediation

# Copy your playbook
cp /path/to/remediation-CVE-2025-49794.yml playbooks/remediation/

# Verify the file
ls -l playbooks/remediation/remediation-CVE-2025-49794.yml
```

**Step 4: Commit and Push Changes**

```bash
# Add the playbook
git add playbooks/remediation/remediation-CVE-2025-49794.yml

# Commit with descriptive message
git commit -m "Add remediation playbook for CVE-2025-49794"

# Push to remote
git push origin main  # or master, depending on your default branch
```

**Step 5: Sync AAP Project**

AAP needs to pull the latest changes from Git:

**Via AAP Web UI**:
1. Navigate to AAP Web UI
2. Click **Automation Execution** in the left sidebar
3. Click **Projects**
4. Find your project (e.g., "Remediation Playbooks")
5. Click the **Sync** button (🔄 icon) on the project row
6. Wait for status to change to "Successful"
7. Verify playbook appears in the project's playbook list

**Troubleshooting**:
- If sync fails, check the project's SCM URL and credentials
- View project sync logs by clicking on the project → **Jobs** tab
- Ensure your Git branch is correct (main/master)

**Step 6: Verify Playbook Availability**

Once synced, note the playbook path for template creation:
```
Playbook path in AAP: playbooks/remediation/remediation-CVE-2025-49794.yml
```

#### Option B: Create New Git Repository

If you don't have an existing repository:

**Step 1: Create Local Repository**

```bash
# Create new directory
mkdir ansible-remediation-playbooks
cd ansible-remediation-playbooks

# Initialize Git
git init

# Create directory structure
mkdir -p playbooks/remediation
mkdir -p playbooks/roles
mkdir -p inventories

# Add README
cat > README.md << 'EOF'
# Ansible Remediation Playbooks

CVE remediation playbooks for Red Hat systems.

## Structure
- `playbooks/remediation/` - CVE remediation playbooks
- `playbooks/roles/` - Shared Ansible roles
- `inventories/` - Inventory files
EOF

# Copy your playbook
cp /path/to/remediation-CVE-2025-49794.yml playbooks/remediation/

# Create .gitignore
cat > .gitignore << 'EOF'
*.retry
.vault_pass
*.swp
*~
EOF
```

**Step 2: Create Remote Repository**

On GitHub/GitLab/Bitbucket:
1. Create new repository (e.g., "ansible-remediation-playbooks")
2. Copy the repository URL
3. Do NOT initialize with README (you already have one)

**Step 3: Commit and Push**

```bash
# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Add CVE remediation playbooks structure"

# Add remote
git remote add origin <your-repository-url>

# Push to remote
git branch -M main
git push -u origin main
```

**Step 4: Add Project to AAP**

Via AAP Web UI:
1. Click **Automation Execution** in the left sidebar
2. Click **Projects**
3. Click **Add** button (top right)
4. Fill in the project form:
   - **Name**: "Remediation Playbooks"
   - **Organization**: Select your organization (typically "Default")
   - **Source Control Type**: Git
   - **Source Control URL**: `<your-repository-url>`
   - **Source Control Branch/Tag/Commit**: `main` (or your default branch)
   - **Source Control Credential**: Select credential (if private repo)
5. Click **Save**
6. AAP will automatically sync the project from Git
7. Wait for project status to show "Successful" (green checkmark)

**Step 5: Note Playbook Path**

For template creation:
```
Playbook path: playbooks/remediation/remediation-CVE-2025-49794.yml
```

#### Verification Checklist

Before proceeding to Phase 2, verify:
- ✅ Playbook committed to Git repository
- ✅ Changes pushed to remote
- ✅ AAP project synced successfully
- ✅ Playbook path noted for template creation
- ✅ Project ID identified (check AAP Web UI or use `projects_list` MCP tool)

**Report to user**:
```
✓ Playbook prepared in Git project

Repository: <repository-url>
Playbook path: playbooks/remediation/remediation-CVE-2025-49794.yml
AAP Project: <project-name> (ID: <project-id>)
Status: Ready for job template creation

Proceeding to Phase 2: Gather Template Configuration...
```

### Phase 2: Gather Required Information

Before creating a job template, collect:

1. **Playbook Information**:
   - Playbook name/path (e.g., `remediation-CVE-2025-49794.yml`)
   - Project where playbook is stored
   - Required variables/parameters

2. **Target Information**:
   - Inventory containing target hosts
   - Host groups or specific hosts to target
   - Any host limits or filters

3. **Credentials**:
   - SSH credentials for host access
   - Vault passwords (if playbook uses Ansible Vault)
   - Cloud credentials (if targeting cloud resources)

4. **Execution Settings**:
   - Job type (run/check)
   - Verbosity level
   - Concurrent execution limits
   - Timeout settings

### Phase 3: Verify Prerequisites

**Step 1: List Available Projects**

**MCP Tool**: `projects_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 50 (retrieve up to 50 projects)
- `search`: "remediation" (optional - filter by keyword)

**Expected Output**:
```json
{
  "count": 1,
  "results": [
    {
      "id": 6,
      "name": "Remediation Playbooks",
      "scm_type": "git",
      "scm_url": "https://github.com/org/playbooks.git",
      "status": "successful"
    }
  ]
}
```

**Action**: Identify the project ID where your playbook is stored.

**Step 2: List Available Inventories**

**MCP Tool**: `inventories_list` (from aap-mcp-inventory-management)

**Parameters**:
- `page_size`: 50
- `search`: "production" (optional - filter by keyword)

**Expected Output**:
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "Production Inventory",
      "total_hosts": 150,
      "has_active_failures": false
    }
  ]
}
```

**Action**: Identify the inventory ID containing your target hosts.

**Step 3: Verify Credentials**

**Note**: The current AAP MCP doesn't expose credential listing tools. You'll need credential IDs from AAP Web UI or administrator.

### Phase 4: Create Job Template via AAP Web UI

⚠️ **CURRENT LIMITATION**: AAP MCP servers currently provide read-only access to job templates. Template creation must be done through the AAP Web UI.

#### Step-by-Step Instructions

**Step 1: Navigate to AAP Web Interface**

1. Open your browser and go to your AAP Web UI (the main AAP instance URL; this may differ from the MCP endpoint)
2. Log in with your AAP credentials

**Step 2: Navigate to Templates**

From the AAP Web UI:
1. Click on **Automation Execution** in the left sidebar
2. Click on **Templates**
3. You'll see the Templates list showing existing job templates

**Step 3: Create New Job Template**

1. Click the **Add** button (top right)
2. Select **Job Template** from the dropdown menu

**Step 4: Fill Job Template Form**

Configure the template with these settings:

**Basic Information**:
- **Name**: `Remediate CVE-2025-49794`
  - Use descriptive name including CVE ID
  - Example: "Remediate CVE-YYYY-NNNNN"
  
- **Description**: `Auto-generated CVE remediation playbook for CVE-2025-49794`
  - Include CVE details and purpose

- **Job Type**: `Run`
  - Use "Run" for actual execution
  - Use "Check" for dry-run testing

**Required Fields**:
- **Inventory**: Select the inventory containing your target hosts
  - Example: "Production Inventory" (from Phase 3 Step 2)
  
- **Project**: Select the project containing your playbook
  - Example: "Remediation Playbooks" (from Phase 3 Step 1)
  - Ensure project status is "Successful" (synced)
  
- **Playbook**: Select your playbook from the dropdown
  - Example: `playbooks/remediation/remediation-CVE-2025-49794.yml`
  - Dropdown will show available playbooks from the selected project

- **Credentials**: Select appropriate credentials
  - **Machine Credential** (SSH): For host access
  - **Vault Credential** (optional): If playbook uses Ansible Vault
  - Click "Select" to choose from existing credentials

**Optional Fields**:

- **Limit**: Leave empty (or specify host pattern to limit execution)
  - Example: `production-*` to target only production hosts
  
- **Verbosity**: `0 (Normal)` (or increase for debugging)
  - 0: Normal
  - 1: Verbose (-v)
  - 2: More Verbose (-vv)
  - 3: Debug (-vvv)

- **Job Tags**: Leave empty (or specify tags from playbook)

- **Skip Tags**: Leave empty (or specify tags to skip)

- **Extra Variables**: Add CVE-specific variables
  ```yaml
  ---
  target_cve: "CVE-2025-49794"
  remediation_mode: "automated"
  verify_after: true
  ```

**Options** (checkboxes at bottom):
- ✅ **Enable Privilege Escalation**: Yes (required for package updates and system changes)
- ✅ **Prompt on Launch**: Check fields you want to override at launch time:
  - ☑️ **Variables** (recommended for dynamic CVE targeting)
  - ☑️ **Limit** (recommended for targeting specific hosts)
- ☐ **Allow Simultaneous**: No (prevent conflicts during remediation)
- ☐ **Enable Webhook**: No (unless integrating with CI/CD)

**Step 5: Save the Template**

1. Click the **Save** button at the bottom
2. AAP will validate the configuration
3. If validation succeeds, you'll be redirected to the template details page
4. Note the template ID from the URL or template details

**Step 6: Verify Template Creation**

Use the AAP MCP to confirm:
```
job_templates_list(search="CVE-2025-49794")
```

Expected result: Template appears in search results with ID

### Phase 5: Verify Template Creation

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)

**Parameters**:
- `search`: "CVE-2025-49794" (search for your template)
- `page_size`: 10

**Expected Output**:
```json
{
  "results": [
    {
      "id": 42,
      "name": "Remediate CVE-2025-49794",
      "playbook": "remediation-CVE-2025-49794.yml",
      "project": 6,
      "inventory": 1,
      "status": "never updated"
    }
  ]
}
```

**Success Criteria**:
- ✓ Template appears in search results
- ✓ Playbook path matches your playbook
- ✓ Project and inventory IDs are correct
- ✓ Template status is valid

### Phase 6: Test Template Execution (Optional)

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: "42" (template ID from Phase 5)

**Expected Output**:
```json
{
  "job": 1234,
  "status": "pending",
  "url": "/api/controller/v2/jobs/1234/"
}
```

**Follow-up**: Use `playbook-executor` skill to track job execution status.

## Output Template

When completing job template creation, provide:

```markdown
# AAP Job Template Created

## Template Details
**Name**: Remediate CVE-2025-49794
**ID**: 42
**Project**: Remediation Playbooks (ID: 6)
**Playbook**: playbooks/remediation/remediation-CVE-2025-49794.yml
**Inventory**: Production Inventory (ID: 1)
**Status**: Ready for execution

## Verification
✓ Template exists in AAP
✓ Project contains the playbook
✓ Inventory has target hosts
✓ Credentials configured

## Next Steps

1. **Execute the template**:
   - Via AAP Web UI: Automation Execution → Templates → Select template → Launch
   - Via MCP: job_templates_launch_retrieve(id="42")

2. **Monitor execution**:
   - Via AAP Web UI: Automation Execution → Jobs → View job details
   - Via MCP: jobs_retrieve(id=job_id) and jobs_stdout_retrieve(id=job_id)

3. **Verify remediation**:
   - Use `remediation-verifier` skill after execution completes
   - Confirm CVE status in Red Hat Insights
```

## Examples

### Example 1: Create Template for CVE Remediation Playbook

**User Request**: "Create a job template for my CVE-2025-49794 remediation playbook"

**Skill Response**:

1. **Check if Playbook is in Git**:
   - Ask user: "Is this playbook already in a Git repository configured in AAP?"
   - User responds: "No, I just generated it"

2. **Guide Through Git Setup** (Phase 1):
   ```
   I'll help you add the playbook to a Git repository.
   
   Do you have an existing Git repository for playbooks, or should we create one?
   
   User: "I have https://github.com/myorg/remediation-playbooks"
   
   Great! Let's add your playbook:
   1. Clone or navigate to the repository
   2. Add the playbook file
   3. Commit and push changes
   4. Sync the AAP project
   
   [Provide step-by-step Git commands]
   ```

3. **Verify Playbook in Git**:
   - Confirm playbook pushed to remote
   - Note playbook path: `playbooks/remediation/remediation-CVE-2025-49794.yml`
   - Confirm AAP project synced

4. **Gather Template Information** (Phase 2):
   - Playbook: `remediation-CVE-2025-49794.yml`
   - Ask user: "Which project contains this playbook?"
   - Ask user: "Which inventory should be targeted?"

5. **List Available Projects** (Phase 3):
   ```
   projects_list() → Found "Remediation Playbooks" (ID: 6)
   ```

6. **List Available Inventories** (Phase 3):
   ```
   inventories_list() → Found "Production Inventory" (ID: 1)
   ```

7. **Report Limitation** (Phase 4):
   ```
   ⚠️ AAP MCP doesn't currently support creating templates programmatically.
   I'll provide instructions for manual creation.
   ```

8. **Provide Web UI Instructions** (Phase 4):
   ```
   Navigate to AAP Web UI:
   1. Automation Execution → Templates
   2. Click Add → Job Template
   3. Fill in the form:
      - Name: "Remediate CVE-2025-49794"
      - Job Type: Run
      - Inventory: Production Inventory
      - Project: Remediation Playbooks
      - Playbook: playbooks/remediation/remediation-CVE-2025-49794.yml
      - Credentials: Select SSH credential
      - Options: Enable Privilege Escalation (Yes)
   4. Save
   ```

9. **Verify After Manual Creation** (Phase 5):
   ```
   job_templates_list(search="CVE-2025-49794") → Template ID: 42
   ```

10. **Report Success**:
   ```
   ✓ Template created with ID: 42
   ✓ Playbook integrated: playbooks/remediation/remediation-CVE-2025-49794.yml
   Ready to execute via AAP job launcher
   ```

### Example 2: Create Template with Custom Variables

**User Request**: "Set up a template for dynamic CVE remediation with variable CVE ID"

**Skill Response**:

1. **Explain Variable Approach**:
   ```
   For dynamic CVE targeting, enable "Ask variables on launch"
   This allows passing different CVE IDs at execution time
   ```

2. **Provide Web UI Configuration**:
   ```
   In AAP Web UI (Automation Execution → Templates → Add → Job Template):
   
   Name: "Dynamic CVE Remediation"
   Job Type: Run
   Inventory: [Select your inventory]
   Project: [Select remediation playbooks project]
   Playbook: playbooks/remediation/remediation-dynamic.yml
   
   Options:
     ✅ Enable Privilege Escalation: Yes
     
   Prompt on Launch (check these):
     ☑️ Variables (allows passing different CVE IDs at runtime)
     ☑️ Limit (allows targeting specific hosts at runtime)
   
   Extra Variables:
   ---
   cve_id: "CVE-YYYY-NNNNN"
   remediation_mode: "automated"
   verify_after: true
   ```

3. **Explain Launch Usage**:
   ```
   When launching this template, you can override variables:
   - In Web UI: Launch button → Prompted for Variables → Enter custom values
   - Via MCP: job_templates_launch_retrieve(id="template_id") with launch-time prompts
   ```

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - AAP job management API access

### Required MCP Tools (Current)
- `job_templates_list` - List existing templates (verification)
- `job_templates_retrieve` - Get template details (verification)
- `projects_list` - List available projects (prerequisite)
- `inventories_list` (from aap-mcp-inventory-management) - List inventories (prerequisite)

### Missing MCP Tools (Needed for Full Automation)
- `job_templates_create` - Create new job templates
- `job_templates_update` - Modify existing templates
- `credentials_list` - List available credentials

### Related Skills
- `mcp-aap-validator` - **PREREQUISITE** - Validates AAP MCP server before creation (invoke in Phase 0 if not validated in session)
- `job-template-remediation-validator` - Validates created template meets remediation requirements
- `playbook-executor` - Execute templates after creation
- `playbook-generator` - Generate remediation playbooks for templates
- `system-context` - Identify target systems for inventory selection

### Reference Documentation
- [AAP 2.6 Job Templates Documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-job-templates)
- [AAP 2.6 Creating Projects](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-projects)

## Best Practices

1. **Use descriptive template names** - Include CVE ID or purpose: "Remediate CVE-2025-49794"
2. **Enable variable prompts for flexibility** - Check "Variables" in the "Prompt on Launch" section for dynamic values
3. **Set appropriate timeouts** - CVE remediation can take time; set generous timeouts
4. **Use privilege escalation** - Most remediation requires sudo/root access
5. **Document template purpose** - Use description field to explain usage
6. **Version playbooks** - Keep playbooks in Git for change tracking
7. **Test templates first** - Use check mode or test inventory before production
8. **Set concurrent limits** - Prevent overwhelming infrastructure with simultaneous jobs
9. **Enable notifications** - Configure email/webhook alerts for job completion
10. **Regular template audits** - Review and update templates as playbooks evolve

## Human-in-the-Loop Requirements

This skill requires user confirmation for:

1. **Git Operations** (adding playbook to repository):
   - Display: "I'll help you add the playbook to your Git repository"
   - Ask: "Proceed with Git operations (clone, commit, push)?"
   - Wait for confirmation

2. **Manual Template Creation** (AAP Web UI):
   - Display: "Template creation requires using the AAP Web UI"
   - Ask: "I'll provide step-by-step instructions. Ready to proceed?"
   - Wait for confirmation

3. **Test Execution** (optional verification):
   - Ask: "Should I test the template by launching a job?"
   - Wait for confirmation before launching

**Never assume approval** - always wait for explicit user confirmation.

## Future Enhancement: When MCP Tools Become Available

When `job_templates_create` MCP tool is added, the workflow will become:

### Step 1: Create Template via MCP

**MCP Tool**: `job_templates_create` (from aap-mcp-job-management) - **FUTURE**

**Parameters**:
```json
{
  "name": "Remediate CVE-2025-49794",
  "description": "Auto-generated remediation template",
  "job_type": "run",
  "inventory": 1,
  "project": 6,
  "playbook": "remediation-CVE-2025-49794.yml",
  "become_enabled": true,
  "ask_variables_on_launch": true,
  "ask_limit_on_launch": true,
  "extra_vars": "{\"target_cve\": \"CVE-2025-49794\"}"
}
```

**Expected Output**:
```json
{
  "id": 42,
  "name": "Remediate CVE-2025-49794",
  "url": "/api/controller/v2/job_templates/42/",
  "status": "success"
}
```

This will enable fully automated template creation as part of the remediation workflow.
