# RH-Virt Evaluation

Everything needed to benchmark how well AI agents use the rh-virt skills. We measure whether giving an agent our skills actually improves its performance compared to relying on general knowledge alone.

## How it works

An agent is dropped into a container with a mock OpenShift Virtualization environment and asked to complete VM operations (cloning, migration, provisioning, decommissioning). We run each task twice — once with skills available, once without — and compare scores.

Scoring combines deterministic checks (did the agent produce the right files with the right values?) with an LLM judge (did the agent demonstrate skill-specific knowledge, like referencing `storage-errors.md` or checking `kubevirt.io/schedulable` labels?).

## Skills vs no-skills: what changes

The "with skills" and "without skills" variants use different Dockerfiles. The skilled variant copies skills, docs, and helper scripts into the container so the agent can discover and read them. The no-skills variant intentionally **does not** copy any of these — the agent only gets the mock MCP server and a kubeconfig. Same task, same tests, but the agent must rely entirely on its own knowledge.

## What's in this folder

**`sonnet/`** and **`haiku/`** contain task instructions and tests tailored for each model.

Within each, there are two layouts:

- **`monolit/`** — all 4 parts in one task. The agent gets a single instruction covering cloning, migration, provisioning, and decommissioning. Simpler to run, but if the agent gets stuck on Part 1, it drags down the entire score.
- **`parts/`** — each part is its own task with focused instructions and tests. Gives cleaner per-skill measurements and avoids cascading failures.

**`common/`** has the shared Dockerfile, no-skills Dockerfile, and mock MCP server used across all variants.

## Sonnet vs Haiku instructions

The task content is identical — same deliverables, same expectations. The difference is how forcefully we remind the agent to read its skills:

- **Sonnet** — a brief note at the top and bottom: "check whether skills are available and read them."
- **Haiku** — aggressive reminders in CAPS throughout: "CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE", "YOU MUST READ EVERY SKILL FILE", per-section nudges, and numbered sub-steps. Haiku tends to skip skill files without this level of emphasis.

## SkillsBench task structure

Harbor expects each task to follow the SkillsBench folder layout. A task is a self-contained directory with everything needed to build the environment, run the agent, and verify its output:

```
tasks/rh-virt_part_1/
├── instruction.md                 # What the agent is asked to do
├── task.toml                      # Metadata (id, timeouts, env vars for the judge)
├── environment/
│   ├── Dockerfile                 # Builds the container the agent runs in
│   ├── mcp-servers/               # Mock MCP server(s)
│   └── skills/                    # Skills the agent can discover (omitted in no-skills)
├── tests/
│   ├── test.sh                    # Entry point — installs deps, runs pytest + LLM judge
│   ├── test_outputs.py            # Deterministic pytest checks
│   └── llm_judge.py               # LLM-based evaluation of skill-specific knowledge
└── solution/
    └── solve.sh                   # Oracle solution (must score 100%)
```

The "no-skills" counterpart lives under `tasks-no-skills/` with the same structure, but its Dockerfile does not copy skills or docs into the container.

For a sweep, Harbor needs at least the `tasks/` and `tasks-no-skills/` paths to exist with this layout. The sweep YAML just points to them.

## Running evaluations

We use [Harbor](https://github.com/redhat-et/agent-frameworks-bench) as the benchmark runner and [SkillsBench](https://github.com/redhat-et/skillsbench) for the task structure. You point Harbor at a sweep config file that specifies which tasks to run and how many trials:

```yaml
job_name: skills-vs-no-skills-rh-virt-part1
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
    model_name: claude-sonnet-4-5  # or claude-haiku-3-5

tasks:
  - path: /path/to/skillsbench/tasks/rh-virt_part_1         # with skills
  - path: /path/to/skillsbench/tasks-no-skills/rh-virt_part_1  # without skills
```

Then run:

```bash
harbor run --config sweep-rh-virt-part1.yaml
```

Harbor builds the container, runs the agent, evaluates the output, and writes a score. Repeat across parts and models to build a full comparison.
