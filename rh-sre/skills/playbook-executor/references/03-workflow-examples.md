# Step 03: Workflow Examples

Read this reference when demonstrating end-to-end workflow patterns.

## Example 1: Full Workflow with Dry-Run

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

## Example 2: Handle Execution Failure

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

## Example 3: Skip Dry-Run

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
