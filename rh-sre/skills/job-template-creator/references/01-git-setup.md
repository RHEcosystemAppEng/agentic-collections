# Git Setup for Playbooks

Read when guiding user through Phase 1 (Prepare Playbook in Git).

## Option A: Add to Existing Project

1. Ask: repo URL, local path, or "I don't have one"
2. Clone or `cd` to repo
3. `mkdir -p playbooks/remediation`; copy playbook; `git add`; `git commit`; `git push`
4. Sync AAP project (Automation Execution → Projects → Sync)
5. Note playbook path: `playbooks/remediation/remediation-CVE-YYYY-NNNNN.yml`

## Option B: Create New Repository

1. `mkdir ansible-remediation-playbooks`; `git init`; `mkdir -p playbooks/remediation`
2. Copy playbook; create README, .gitignore; `git add .`; `git commit`
3. Create remote repo; `git remote add origin <url>`; `git push -u origin main`
4. Add project in AAP Web UI (Automation Execution → Projects → Add)
5. Note playbook path

## Verification Checklist

- Playbook committed and pushed
- AAP project synced
- Playbook path noted for template creation
