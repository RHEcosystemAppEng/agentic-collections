# Step 05: Git Flow Prompts

Read this reference when executing Git Flow (Scenario 1 Override or Scenario 2).

## Scenario 1 Prompt (Same path)

The template already points to our playbook path. The project may need the latest content.

```
Found template [name] (ID: X) with matching playbook path. The project may need to be updated with the latest playbook.

Options:
(A) Override: I'll add/update the playbook in the project via git. You sync the AAP project, then confirm.
(B) Manual: You add the playbook and sync. Confirm when done.

❓ Choose (A) or (B):
```

- **If A**: Execute Git Flow (see Git Flow section below). Wait for user: "Sync complete" or "done".
- **If B**: Wait for user confirmation.

## Scenario 2 Prompt (Different path)

**CRITICAL**: The template points to a DIFFERENT playbook than our generated playbook. You MUST NOT launch the job without Git Flow. AAP executes from synced project content—there is no "override at launch". The playbook MUST be in the repo before any job launch.

```
Found template [name] (ID: X) pointing to [template.playbook]. Our generated playbook is [our_playbook_path].

⚠️ The template's playbook path does NOT match. We must update the playbook in the project before execution.

Options:
- "yes" or "proceed" - I'll add our playbook to the project via git (you'll confirm commit/push, then sync AAP)
- "no" - Create a new template via `/job-template-creator` skill

❓ Proceed with playbook update (git flow)?
```

- **If yes**: Execute Git Flow. **Do NOT proceed to Phase 3 until Git Flow completes.**
- **If no**: Fall through to Scenario 3 (job-template-creator).

## Repo Path Question

```
What is the local path to the Git repository for project [Project Name] (scm_url)?
```

Use `projects_list` to get project name and `scm_url`; display to help user identify the repo.

**Path format**: Ask for the **absolute path** (e.g. `/Users/dmartino/projects/AI/ai5/ai5-demo/test-aap-project`). When writing the playbook, the Write tool path MUST be `<user_path>/playbooks/remediation/<filename>` — the full absolute path. Do NOT use a relative path like `test-aap-project/playbooks/...`; that causes "Error writing file".

## Git Flow: Write Step (FAST)

**CRITICAL**: The playbook is ALREADY generated. During Git Flow you must WRITE the existing content to disk—nothing more.

- **DO**: Single file write of the playbook content already in context (from playbook-generator or remediation)
- **DO NOT**: Invoke playbook-generator again, call create_vulnerability_playbook, re-fetch from MCP, or validate/transform the content
- **Expected duration**: Seconds. If it takes minutes, you are doing unnecessary work.

### Write Path (ABSOLUTE REQUIRED)

**⚠️ WRITE PATH MUST START WITH `/`** — The Write tool path MUST be an absolute path. Relative paths cause "Error writing file" because the repo is often outside the workspace.

**Formula**: `write_path = user_provided_path + "/" + target_path`

- `user_provided_path` = exactly what the user typed (e.g. `/Users/dmartino/projects/AI/ai5/ai5-demo/test-aap-project`)
- `target_path` = e.g. `playbooks/remediation/cve-remediation.yml`

**Correct**: `/Users/dmartino/projects/AI/ai5/ai5-demo/test-aap-project/playbooks/remediation/cve-remediation.yml`

**WRONG** (will fail):
- `test-aap-project/playbooks/remediation/cve-remediation.yml`
- `playbooks/remediation/cve-remediation.yml`

**Before calling Write**: Verify the path starts with `/`. If it does not, prepend the user's repo path.

## Git Flow HITL Checkpoint

**REQUIRED** before commit/push:

```
Ready to commit and push these changes?
- File: [target_path]
- CVE: [cve_id]
- This will update the playbook in the AAP project.

Reply 'yes' or 'proceed' to continue, or 'abort' to cancel.
```

**Wait for user confirmation.** If "yes" or "proceed": `git commit -m "Add/update remediation playbook for CVE-YYYY-NNNNN"` then `git push origin main`.

## After Push Message

```
I've pushed the playbook. Sync the AAP project: Automation Execution > Projects > [Project] > Sync. Reply 'sync complete' when done.
```

**Do NOT proceed to Phase 3 (Dry-Run) until user confirms sync complete.**
