# Per-Skill Evaluation: Skill Path Fixes

This document records all modifications made to SKILL.md files and environment
directories to ensure paths resolve correctly when the agent runs inside the
Harbor container.

## Container Layout

The Dockerfile copies environment contents into:

```
/root/
├── .claude/skills/<skill-name>/SKILL.md    # from environment/skills/
├── .claude/docs/...                         # from environment/docs/
├── docs/...                                 # second copy of docs
├── .mcp.json                                # generated or copied
└── .mcp-servers/                            # from environment/mcp-servers/
```

From a SKILL.md at `/root/.claude/skills/<skill>/SKILL.md`:
- `../../docs/` resolves to `/root/.claude/docs/`
- `../../../docs/` resolves to `/root/docs/` (second copy)
- `../references/` resolves to `/root/.claude/skills/references/`
- `./` resolves to `/root/.claude/skills/<skill>/`

---

## Fixes Applied

### 1. rh-ai-engineer (7 tasks): Added shared `skills/references/`

**Tasks**: ai-observability, debug-inference, ds-project-setup, model-deploy,
nim-setup, serving-runtime-config, workbench-manage

**Problem**: SKILL.md files reference `../references/skill-conventions.md`,
`../references/live-doc-lookup.md`, and `../references/common-issues.md`.
These expect `environment/skills/references/` to exist. It was missing.

**Fix**: Copied `agentic-collections/rh-ai-engineer/skills/references/` into
each task's `environment/skills/references/` directory.

**Files added** (per task):
- `environment/skills/references/skill-conventions.md`
- `environment/skills/references/live-doc-lookup.md`
- `environment/skills/references/common-issues.md`

---

### 2. ocp-admin__cluster-report: Added `scripts/` and `.mcp.json`

**Problem**: SKILL.md references `../../scripts/cluster-report/assemble.py`,
`../../scripts/cluster-report/aggregate.py`,
`../../scripts/cluster-report/build-kubeconfig.py`, and `../../.mcp.json`.
None were present in the environment.

**Fix**: Copied from `agentic-collections/ocp-admin/`:
- `scripts/cluster-report/` (6 files) into `environment/scripts/cluster-report/`
- `.mcp.json` into `environment/.mcp.json`

---

### 3. rh-sre (7 tasks): Added cross-referenced skill directories

**Problem**: Several SRE skills reference other skills via `../other-skill/SKILL.md`.
In the per-skill evaluation, only the evaluated skill is included, so cross-refs
broke.

**Fix**: Copied the referenced skill directories from
`agentic-collections/rh-sre/skills/` into each task's `environment/skills/`:

| Task | Added skills |
|------|-------------|
| rh-sre__cve-impact | mcp-lightspeed-validator |
| rh-sre__cve-validation | mcp-lightspeed-validator |
| rh-sre__fleet-inventory | mcp-lightspeed-validator |
| rh-sre__job-template-creator | mcp-aap-validator, playbook-executor |
| rh-sre__job-template-remediation-validator | mcp-aap-validator, playbook-executor, job-template-creator |
| rh-sre__playbook-executor | mcp-aap-validator |
| rh-sre__remediation | cve-validation |

---

### 4. rh-developer (5 tasks): Added `templates/`

**Tasks**: containerize-deploy, deploy, detect-project, helm-deploy, rhel-deploy

**Problem**: SKILL.md files reference `templates/deployment.yaml.template`,
`templates/helm/`, `templates/systemd/`, etc. The templates directory was
not present in the environment.

**Fix**: Copied `agentic-collections/rh-developer/templates/` into each
task's `environment/templates/` directory.

---

### 5. rh-sre__cve-impact: Fixed dangling doc references (SKILL.md modified)

**Problem**: SKILL.md referenced `insights-api.md` and `fleet-management.md`
in `../../docs/insights/`. These files do not exist in the source
agentic-collections repository.

**Fix**: Replaced broken links with references to
`vulnerability-logic.md` (which exists at `../../docs/insights/vulnerability-logic.md`
and covers related content):

| Original reference | Replaced with |
|-------------------|---------------|
| `../../docs/insights/insights-api.md` | `../../docs/insights/vulnerability-logic.md` |
| `../../docs/insights/fleet-management.md` | `../../docs/insights/vulnerability-logic.md` |

Lines changed: 221-222, 252-253, 394-395

---

### 6. rh-sre__fleet-inventory: Fixed dangling doc references (SKILL.md modified)

**Problem**: Same as cve-impact — references to non-existent `insights-api.md`
and `fleet-management.md`.

**Fix**: Same replacement to `vulnerability-logic.md`.

Lines changed: 101-102, 127-128, 219-220

---

### 7. rh-sre__cve-impact: Fixed path depth `../../../docs/` → `../../docs/`

**Problem**: Two references used `../../../docs/references/` (three levels up)
instead of `../../docs/references/` (two levels up). Both paths work inside
the container (docs is at both `/root/.claude/docs/` and `/root/docs/`), but
`../../docs/` is the canonical path.

**Fix**: Changed `../../../docs/` to `../../docs/` in two places:
- Line 23: `skill-invocation.md`
- Line 325: `lightspeed-mcp-tool-failures.md`

---

### 8. rh-sre__cve-validation: Fixed path depth `../../../docs/` → `../../docs/`

**Problem**: Same path depth issue as cve-impact.

**Fix**: Changed `../../../docs/references/skill-invocation.md` path from
`../../../docs/` to `../../docs/`.

Line changed: 24

---

### 9. rh-virt__vm-rebalance: Fixed citation paths (SKILL.md modified)

**Problem**: SKILL.md uses absolute-style paths
`rh-virt/skills/vm-rebalance/REBALANCE_MANUAL.md` in agent output citation
text. These don't resolve from the skill directory. The actual Read
instructions correctly use `./REBALANCE_MANUAL.md`.

**Fix**: Changed citation paths to use relative `./` prefix:
- `rh-virt/skills/vm-rebalance/REBALANCE_MANUAL.md` → `./REBALANCE_MANUAL.md`
- `rh-virt/skills/vm-rebalance/REBALANCE_AUTOMATIC.md` → `./REBALANCE_AUTOMATIC.md`

Lines changed: 94, 103

---

## Remaining Non-Issues (false positives)

| Task | Pattern | Explanation |
|------|---------|-------------|
| rh-developer__debug-rhel | `[path](/.*)? ` | SELinux fcontext regex, not a file link |
| rh-developer__rhel-deploy | `[app-name](/.*)? ` | SELinux fcontext regex, not a file link |

These appear in `semanage fcontext` shell command examples. The markdown
link syntax parser matches them, but they are regex patterns, not file
references.

---

## Validation Results

After all fixes: **269 paths OK, 0 real broken references**.
