# Step 04: Dry-Run Display Templates

Read this reference when displaying Phase 3 dry-run content.

## Playbook Preview

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

## Dry-Run Offer

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

## Dry-Run Results Display

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

## Proceed to Actual Execution Prompt

```
❓ Dry-run completed successfully. Proceed with actual execution?

Options:
- "yes" or "execute" - Proceed with actual remediation
- "review" - Show dry-run output again
- "abort" - Cancel execution

Please respond with your choice.
```
