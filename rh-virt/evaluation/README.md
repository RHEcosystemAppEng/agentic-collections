# RH-Virt Evaluation

Everything needed to benchmark how well AI agents use the rh-virt skills. We measure whether giving an agent our skills actually improves its performance compared to relying on general knowledge alone.

## How it works

An agent is dropped into a container with a mock OpenShift Virtualization environment and asked to complete VM operations (cloning, migration, provisioning, decommissioning). We run each task twice — once with skills available, once without — and compare scores.

Scoring combines deterministic checks (did the agent produce the right files with the right values?) with an LLM judge (did the agent demonstrate skill-specific knowledge, like referencing `storage-errors.md` or checking `kubevirt.io/schedulable` labels?).

## Skills vs no-skills: what changes

The "with skills" and "without skills" variants use different Dockerfiles. The skilled variant (`common/Dockerfile`) copies skills, docs, and helper scripts into the container so the agent can discover and read them. The no-skills variant (`common/Dockerfile.no-skills`) intentionally **does not** copy any of these — the agent only gets the mock MCP server and a kubeconfig. Same task, same tests, but the agent must rely entirely on its own knowledge.

## What's in this folder

```
evaluation/
├── README.md
├── common/                        # Shared across all variants
│   ├── Dockerfile                 # With-skills container build
│   ├── Dockerfile.no-skills       # No-skills container build
│   └── mcp-servers/
│       └── mock-virt-mcp.py       # Mock OpenShift Virtualization MCP server
├── sonnet/
│   ├── monolit/                   # All 4 parts in one task
│   │   ├── instruction.md
│   │   ├── task.toml
│   │   └── tests/
│   │       ├── test.sh
│   │       ├── test_outputs.py
│   │       └── llm_judge.py
│   └── parts/                     # Each part as its own task
│       ├── part_1/ ... part_4/    # Same structure as monolit
└── haiku/
    ├── README.md
    ├── monolit/
    │   └── instruction.md         # Only differing file — Haiku-specific prompting
    └── parts/
        └── part_1/ ... part_4/    # Only instruction.md per part
```

**Haiku folders only contain `instruction.md` files** — tests, `task.toml`, Dockerfiles, and MCP server are all reused from Sonnet. See `haiku/README.md` for details.

**`parts/`** are included for reference. They show how to split the monolithic task into focused per-skill evaluations for cleaner measurements.

## Sonnet vs Haiku instructions

The task content is identical — same deliverables, same expectations. The difference is how forcefully we remind the agent to read its skills:

- **Sonnet** — a brief note at the top and bottom: "check whether skills are available and read them."
- **Haiku** — aggressive reminders in CAPS throughout: "CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE", "YOU MUST READ EVERY SKILL FILE", per-section nudges, and numbered sub-steps. Haiku tends to skip skill files without this level of emphasis.

## Reproducing evaluations

### Prerequisites

1. [Harbor](https://github.com/redhat-et/agent-frameworks-bench) — the benchmark runner
2. [SkillsBench](https://github.com/redhat-et/skillsbench) — cloned locally
3. Podman (or Docker) for container builds
4. An Anthropic API key (for the agent and the LLM judge)

### Step-by-step

1. **Assemble full task folders in SkillsBench.** Harbor expects self-contained task directories. For each variant you want to run, create a folder under `skillsbench/tasks/` (with skills) and `skillsbench/tasks-no-skills/` (without skills) following this structure:

```
tasks/rh-virt/
├── instruction.md         # From evaluation/sonnet/monolit/ (or haiku/)
├── task.toml              # From evaluation/sonnet/monolit/
├── environment/
│   ├── Dockerfile         # From evaluation/common/Dockerfile
│   ├── mcp-servers/
│   │   └── mock-virt-mcp.py   # From evaluation/common/mcp-servers/
│   └── skills/            # Copy from rh-virt/skills/ in this repo
├── tests/
│   ├── test.sh            # From evaluation/sonnet/monolit/tests/
│   ├── test_outputs.py
│   └── llm_judge.py
```

For no-skills variants, use `Dockerfile.no-skills` and omit the `skills/` folder.

2. **Create a sweep config.** Save a YAML file in the Harbor directory:

```yaml
job_name: skills-vs-no-skills-rh-virt
jobs_dir: jobs
n_attempts: 4

orchestrator:
  type: local
  n_concurrent_trials: 1

environment:
  type: podman
  force_build: true
  delete: true

agents:
  - name: claude-code
    model_name: claude-sonnet-4-5

tasks:
  - path: /path/to/skillsbench/tasks/rh-virt
  - path: /path/to/skillsbench/tasks-no-skills/rh-virt
```

3. **Run:**

```bash
harbor run --config sweep-rh-virt.yaml
```

Harbor builds the container, runs the agent, evaluates the output, and writes results to `jobs/<job_name>/`.

## Results summary

Sonnet (monolithic, 4 trials each):

| Variant | Mean Score | Pytest | LLM Judge |
|---------|-----------|--------|-----------|
| With skills | 0.929 | ~30/33 | ~12/15 |
| Without skills | 0.694 | ~22/33 | ~8/15 |
| **Skill uplift** | **+0.235** | | |

Haiku (monolithic, 4 trials each):

| Variant | Mean Score | Pytest | LLM Judge |
|---------|-----------|--------|-----------|
| With skills | 0.728 | ~24/33 | ~9/15 |
| Without skills | 0.397 | ~13/33 | ~5/15 |
| **Skill uplift** | **+0.331** | | |

Skills improve both models, with a larger relative lift for Haiku (+33%) than Sonnet (+24%). See the [blog post](../blog/) for detailed analysis including cost breakdowns and per-part results.
