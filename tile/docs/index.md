# agentic-collections

Persona-specific agentic skill collections automating interactions with Red Hat platforms and products. The package bundles five collections of AI skills (invokable via slash commands), MCP server configurations, and Python tooling scripts. Each collection targets a specific user role and integrates with Claude Code and Cursor AI marketplaces.

## Package Information

- **Package Name**: agentic-collections
- **Package Type**: pypi
- **Language**: Python (tooling) + Markdown (skill definitions)
- **Installation**: `pip install agentic-collections` or `uv add agentic-collections`
- **Python**: >= 3.11
- **Dependencies**: PyYAML >= 6.0, jsonschema >= 4.0

## Core Imports

The package is not an importable Python library. The Python scripts are invoked directly via `uv run` or the Makefile:

```bash
# Install dependencies
uv sync

# Validate pack structure
uv run python scripts/validate_structure.py

# Validate skill design principles
uv run python scripts/validate_skill_design.py [pack-dir] [--warnings-as-errors]

# Generate documentation website data
uv run python scripts/build_website.py

# Start documentation server
cd docs && uv run python -m http.server 8000
```

For programmatic use in Python:

```python
from scripts.generate_pack_data import generate_pack_data, parse_skills, parse_yaml_frontmatter
from scripts.generate_mcp_data import generate_mcp_data, parse_mcp_file
from scripts.validate_skill_design import validate_skill, ValidationResult
from scripts.validate_structure import validate_pack
```

## Basic Usage

```bash
# Full workflow: validate + generate docs
make install     # install dependencies (one-time)
make validate    # validate all pack structures
make validate-skill-design          # validate all skills
make validate-skill-design PACK=rh-sre  # validate one pack
make generate    # generate docs/data.json
make serve       # start docs server at localhost:8000
make test        # validate + generate + verify

# Validate only changed skills (local dev)
make validate-skill-design-changed
```

Skills are invoked in AI marketplaces using the slash format:
```
/cve-impact          # SRE: CVE analysis
/remediation         # SRE: Full CVE remediation workflow
/vm-create           # Virt: Create virtual machine
/deploy              # Developer: Deploy to OpenShift
/cluster-report      # Admin: Multi-cluster health report
```

## Capabilities

### Red Hat SRE Collection (rh-sre)

13 skills for Site Reliability Engineering workflows: CVE analysis, remediation orchestration, Ansible playbook generation/execution, fleet inventory, and system context gathering. Integrates with Red Hat Lightspeed MCP and Ansible Automation Platform (AAP) MCP servers.

```python { .api }
# Key skills (invoked as slash commands):
/remediation           # Full end-to-end CVE remediation orchestration
/cve-impact            # CVE discovery, listing, risk assessment
/cve-validation        # Validate CVE IDs and remediation availability
/playbook-generator    # Generate Ansible remediation playbooks via Lightspeed
/playbook-executor     # Execute playbooks via AAP
/fleet-inventory       # Query managed system inventory
/system-context        # Gather system deployment context
/mcp-lightspeed-validator  # Validate Lightspeed MCP connectivity
/mcp-aap-validator     # Validate AAP MCP connectivity
/job-template-creator  # Create AAP job templates
/job-template-remediation-validator  # Verify AAP job template requirements
/remediation-verifier  # Verify CVE remediation success
/execution-summary     # Summarize agents/skills/tools used
```

[Red Hat SRE Collection](./packs/rh-sre.md)

### Red Hat Developer Collection (rh-developer)

14 skills for containerizing and deploying applications to OpenShift or RHEL systems. Covers project detection, S2I builds, Helm deployments, RHEL deployments, and debugging. Integrates with OpenShift MCP, Podman MCP, GitHub MCP, and optionally Lightspeed MCP.

```python { .api }
# Key skills (invoked as slash commands):
/containerize-deploy   # End-to-end: source code → running application
/detect-project        # Detect language, framework, version from source
/recommend-image       # Recommend optimal S2I/container base image
/s2i-build             # S2I build on OpenShift (BuildConfig + ImageStream)
/deploy                # Deploy image to OpenShift (Deployment + Service + Route)
/helm-deploy           # Deploy via Helm charts to OpenShift
/rhel-deploy           # Deploy to standalone RHEL/Fedora/CentOS via Podman
/validate-environment  # Check tools (oc, helm, podman, git) and cluster
/debug-pod             # Diagnose pod failures (CrashLoopBackOff, OOMKilled)
/debug-build           # Diagnose OpenShift build failures
/debug-container       # Diagnose local container issues
/debug-network         # Diagnose OpenShift service connectivity
/debug-pipeline        # Diagnose Tekton pipeline failures
/debug-rhel            # Diagnose RHEL system issues (systemd, SELinux, firewall)
```

[Red Hat Developer Collection](./packs/rh-developer.md)

### OpenShift Administration Collection (ocp-admin)

1 skill for multi-cluster OpenShift administration. Read-only operations using OpenShift MCP server.

```python { .api }
# Skills (invoked as slash commands):
/cluster-report        # Multi-cluster health report (CPU, memory, namespaces, pods)
```

[OpenShift Administration Collection](./packs/ocp-admin.md)

### Red Hat Virtualization Collection (rh-virt)

10 skills for OpenShift Virtualization management: VM lifecycle, snapshots, cloning, and rebalancing. Integrates with OpenShift Virtualization MCP server (KubeVirt toolset).

```python { .api }
# Skills (invoked as slash commands):
/vm-create             # Create VMs (OS, size, storage, performance class)
/vm-inventory          # List/view VMs with status and resources
/vm-lifecycle-manager  # Start, stop, restart VMs
/vm-delete             # Permanently delete VMs (with typed confirmation)
/vm-clone              # Clone VMs for testing or scaling
/vm-rebalance          # Migrate VMs across nodes for load balancing
/vm-snapshot-create    # Create VM snapshots
/vm-snapshot-list      # List snapshots (read-only)
/vm-snapshot-delete    # Delete snapshots
/vm-snapshot-restore   # Restore VM from snapshot
```

[Red Hat Virtualization Collection](./packs/rh-virt.md)

### Red Hat Support Engineer Collection (rh-support-engineer)

Placeholder pack for technical support and troubleshooting tools for Red Hat products and platforms. No skills are currently defined. Targets the Support Engineer persona; available in Claude Code, Cursor, and ChatGPT marketplaces.

[Red Hat Support Engineer Collection](./packs/rh-support-engineer.md)

### Python Tooling Scripts

Python scripts for validating packs, generating documentation website data, and running the documentation server. Used via Makefile targets or directly with `uv run`.

```python { .api }
# validate_structure.py
def validate_pack(pack_dir: str) -> List[str]: ...
def validate_plugin_json(pack_dir: str) -> List[str]: ...
def validate_mcp_json(pack_dir: str) -> List[str]: ...
def validate_skills(pack_dir: str) -> List[str]: ...
def validate_agents(pack_dir: str) -> List[str]: ...
def validate_yaml_frontmatter(file_path: Path) -> Tuple[bool, str]: ...

# validate_skill_design.py
def validate_skill(skill_path: Path) -> ValidationResult: ...
def find_skill_files(pack_dirs: list[str]) -> Iterator[Path]: ...
def extract_frontmatter(content: str) -> tuple[dict | None, str]: ...

# generate_pack_data.py
def generate_pack_data() -> List[Dict[str, Any]]: ...
def parse_skills(pack_dir: str) -> List[Dict[str, Any]]: ...
def parse_agents(pack_dir: str) -> List[Dict[str, Any]]: ...
def parse_docs(pack_dir: str) -> List[Dict[str, Any]]: ...
def parse_plugin_json(pack_dir: str, plugin_titles: Dict[str, str]) -> Dict[str, Any]: ...
def parse_yaml_frontmatter(file_path: Path) -> Dict[str, Any]: ...

# generate_mcp_data.py
def generate_mcp_data() -> List[Dict[str, Any]]: ...
def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]: ...
def extract_env_vars(env_dict: Dict[str, str]) -> List[str]: ...
def extract_header_env_vars(headers: Dict[str, str]) -> List[str]: ...
def load_custom_mcp_data() -> Dict[str, Any]: ...

# build_website.py
def build_website() -> None: ...
def load_icons() -> Dict[str, Dict[str, str]]: ...
```

[Python Tooling Scripts](./tooling.md)

### Pack & Skill Structure

Conventions for creating new agentic packs and skills: directory layout, YAML frontmatter schemas, MCP server configuration, design principles, and naming conventions.

[Pack & Skill Structure](./pack-structure.md)

## Types

```python { .api }
@dataclass
class ValidationResult:
    """Result of validating a single skill."""
    path: Path
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool: ...
```
