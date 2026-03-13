# Python Tooling Scripts

Python scripts for validating pack structures, validating skill design principles, generating documentation website data, and running the local documentation server. All scripts use the `uv` package manager. Run from the repository root.

## Installation

```bash
# Requires: uv (https://github.com/astral-sh/uv)
curl -LsSf https://astral.sh/uv/install.sh | sh  # or: brew install uv
uv sync  # install dependencies
```

## Makefile Interface

```bash { .api }
make install                          # Install Python dependencies (one-time)
make validate                         # Validate all pack structures
make validate-skill-design            # Validate all skills against design principles
make validate-skill-design PACK=rh-sre  # Validate a specific pack only
make validate-skill-design-changed    # Validate only changed skills (staged + unstaged)
make generate                         # Generate docs/data.json
make serve                            # Start local server at http://localhost:8000
make test                             # validate + generate + verify checks
make test-full                        # test + browser auto-open
make clean                            # Remove generated files (docs/data.json)
make update                           # validate + generate
```

## scripts/validate_structure.py

Validates agentic collection directory structure: plugin.json, .mcp.json, and skill/agent YAML frontmatter.

```python { .api }
PACK_DIRS: list[str] = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt']

def validate_pack(pack_dir: str) -> List[str]:
    """
    Validate a single pack directory.

    Args:
        pack_dir: Pack directory name (e.g. 'rh-sre')

    Returns:
        List of error message strings (empty if valid)

    Checks: directory exists, plugin.json fields, .mcp.json structure,
            all skills' YAML frontmatter, all agents' YAML frontmatter
    """

def validate_plugin_json(pack_dir: str) -> List[str]:
    """
    Validate .claude-plugin/plugin.json.
    File is optional — returns [] if not present.

    Required fields: 'name', 'version', 'description'
    Returns: List of error strings
    """

def validate_mcp_json(pack_dir: str) -> List[str]:
    """
    Validate .mcp.json structure.
    File is optional — returns [] if not present.

    Checks: 'mcpServers' key exists, value is an object (dict)
    Returns: List of error strings
    """

def validate_yaml_frontmatter(file_path: Path) -> Tuple[bool, str]:
    """
    Validate YAML frontmatter in a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple (is_valid: bool, error_message: str)
        is_valid=True means 'name' and 'description' fields present and YAML valid
    """

def validate_skills(pack_dir: str) -> List[str]:
    """
    Validate all skills/*/SKILL.md frontmatter in a pack.

    Returns: List of error strings
    """

def validate_agents(pack_dir: str) -> List[str]:
    """
    Validate all agents/*.md frontmatter in a pack.

    Returns: List of error strings
    """

def main() -> int:
    """
    Entry point. Validates all packs in PACK_DIRS.
    Prints validation results.
    Returns: 0 (success) or 1 (failure)
    """
```

**Usage:**
```bash
uv run python scripts/validate_structure.py
# Output: "Validating rh-sre... ✓"  (or ❌ with errors)
# Exit: 0 (success) or 1 (failure)
```

---

## scripts/validate_skill_design.py

Validates skills against `SKILL_DESIGN_PRINCIPLES.md` (Tier 2 design principles).

```python { .api }
MAX_DESCRIPTION_TOKENS: int = 500
CHARS_PER_TOKEN: int = 4
MAX_DESCRIPTION_CHARS: int = 2000  # derived

CRITICAL_SKILL_KEYWORDS: list[str] = [
    "executor", "playbook-executor", "job-template-creator", "remediation"
]
# Skills with these keywords in name require Human-in-the-Loop section

REQUIRED_SECTIONS: list[str] = ["When to Use This Skill", "Workflow"]
ORDERED_SECTIONS: list[str] = ["Prerequisites", "When to Use This Skill", "Workflow"]

DEPENDENCY_SUBSECTIONS: list[str] = [
    "Required MCP Servers", "Required MCP Tools",
    "Related Skills", "Reference Documentation"
]

@dataclass
class ValidationResult:
    path: Path
    errors: list[str]    # blocking errors
    warnings: list[str]  # non-blocking warnings

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

def validate_skill(skill_path: Path) -> ValidationResult:
    """
    Run all design principle checks on a single SKILL.md file.

    Checks:
      DP1: Document Consultation has both Action:Read and Output declaration
      DP2: Document Consultation appears BEFORE MCP Tool/Parameters in workflow steps
      DP3: Description under 500 tokens; includes "Use when" examples
      DP4: ## Dependencies section with required subsections
      DP5: Critical skills have ## Human-in-the-Loop Requirements section
      DP6: ## When to Use This Skill and ## Workflow sections present in order
      DP7: No echo $VAR credential exposure (unless in documented anti-pattern)
      Frontmatter: 'name' and 'description' fields present

    Returns:
        ValidationResult with errors (blocking) and warnings (non-blocking)
    """

def find_skill_files(pack_dirs: list[str]) -> Iterator[Path]:
    """
    Yield paths to all SKILL.md files in pack directories.

    Args:
        pack_dirs: List of pack directory names
    Yields:
        Path objects to skills/*/SKILL.md files
    """

def extract_frontmatter(content: str) -> tuple[dict | None, str]:
    """
    Extract YAML frontmatter and body from markdown string.

    Returns:
        Tuple (frontmatter_dict or None, body_str)
        frontmatter_dict is None if missing or invalid YAML
    """

def main() -> int:
    """
    CLI entry point. Accepts pack directories or specific SKILL.md paths.

    Args (via sys.argv):
        paths: Pack dirs or SKILL.md paths (default: all packs)
        --warnings-as-errors: Treat warnings as errors

    Returns: 0 (pass) or 1 (fail)
    """
```

**Design Principles checked:**

| ID | Name | Error/Warning |
|----|------|---------------|
| DP1 | Document Consultation Transparency | warning |
| DP2 | Parameter Order (consultation before MCP tool) | error |
| DP3 | Conciseness (description length + Use when) | warning |
| DP4 | Dependencies Declaration | error (missing section) / warning (missing subsections) |
| DP5 | Human-in-the-Loop for critical skills | warning |
| DP6 | Mandatory Sections (When to Use + Workflow) | error |
| DP7 | Credential Security (no echo $VAR) | error |

**Usage:**
```bash
# Validate all packs
uv run python scripts/validate_skill_design.py

# Validate specific pack
uv run python scripts/validate_skill_design.py rh-sre

# Validate specific skill file
uv run python scripts/validate_skill_design.py rh-sre/skills/cve-impact/SKILL.md

# Treat warnings as errors
uv run python scripts/validate_skill_design.py --warnings-as-errors

# Validate only changed skills (for CI/local dev)
VALIDATE_INCLUDE_UNCOMMITTED=1 ./scripts/ci-validate-changed-skills.sh
```

**Output format:**
```
  rh-sre/skills/cve-impact/SKILL.md: ✓
  rh-sre/skills/remediation/SKILL.md: ⚠️
    • DP3: Description may exceed 500 tokens...
  rh-virt/skills/vm-delete/SKILL.md: ❌
    • DP6: Missing required section '## Workflow'
```

---

## scripts/generate_pack_data.py

Parses agentic packs and extracts metadata for documentation generation.

```python { .api }
PACK_DIRS: list[str] = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-virt']
# Note: rh-support-engineer excluded (no skills/agents)

def generate_pack_data() -> List[Dict[str, Any]]:
    """
    Parse all packs and return structured data.

    Returns:
        List of pack dicts:
        {
            'name': str,           # pack directory name
            'path': str,           # relative path e.g. './rh-sre'
            'plugin': dict,        # plugin.json data (with defaults if missing)
            'skills': list[dict],  # sorted by name
            'agents': list[dict],  # sorted by name
            'docs': list[dict],    # sorted by category, title
            'has_readme': bool
        }
    """

def parse_skills(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse skills from skills/*/SKILL.md.

    Returns:
        List of skill dicts (sorted by name):
        {
            'name': str,        # from frontmatter 'name' field
            'description': str, # from frontmatter 'description', whitespace-collapsed
            'file_path': str    # path relative to pack_dir
        }
    """

def parse_agents(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse agents from agents/*.md.

    Returns:
        List of agent dicts (sorted by name):
        {
            'name': str,
            'description': str,  # whitespace-collapsed
            'model': str,        # default: 'inherit'
            'tools': list,       # from frontmatter
            'file_path': str
        }
    """

def parse_docs(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse documentation from docs/**/*.md.
    Excludes: README.md, INDEX.md, SOURCES.md, .ai-index/ directory.

    Returns:
        List of doc dicts (sorted by category, title):
        {
            'title': str,      # from frontmatter or derived from filename
            'category': str,   # from frontmatter or parent directory name
            'sources': list,   # list of {title, url, date_accessed} dicts
            'file_path': str
        }
    """

def parse_plugin_json(pack_dir: str, plugin_titles: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse .claude-plugin/plugin.json with defaults if missing.

    Args:
        pack_dir: Pack directory name
        plugin_titles: Title overrides from docs/plugins.json

    Returns:
        Dict with fields: name, version, description, author, license, keywords,
        title (from plugins.json or name field)
        Defaults: version='0.0.0', author={'name': 'Red Hat'}, license='Apache-2.0'
    """

def parse_yaml_frontmatter(file_path: Path) -> Dict[str, Any]:
    """
    Extract YAML frontmatter from a markdown file.

    Returns:
        Dict of frontmatter fields, or {} on error/missing frontmatter
    """

def load_plugin_titles() -> Dict[str, str]:
    """
    Load title overrides from docs/plugins.json.

    Returns:
        Dict mapping pack names to display titles
        e.g. {'rh-sre': 'Red Hat SRE Agentic Skills Collection'}
    """

def sanitize_for_json(obj: Any) -> Any:
    """
    Convert non-JSON-serializable types for JSON output.
    Handles: date/datetime → ISO string, nested dicts/lists recursively.
    """
```

---

## scripts/generate_mcp_data.py

Parses `.mcp.json` files and generates MCP server data, merging with custom metadata.

```python { .api }
PACK_DIRS: list[str] = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt']

def generate_mcp_data() -> List[Dict[str, Any]]:
    """
    Parse MCP configs from all packs and merge with docs/mcp.json custom data.

    Returns:
        List of server dicts:
        {
            'name': str,         # server name from mcpServers key
            'pack': str,         # source pack directory
            'type': str,         # 'command' (default) or 'http'
            'description': str,  # from .mcp.json
            'security': dict,    # isolation, network, credentials
            # Command-based servers:
            'command': str,      # e.g. 'podman'
            'args': list[str],
            'env': list[str],    # extracted env var names
            # HTTP servers:
            'url': str,
            'headers': dict,
            # From docs/mcp.json:
            'repository': str,   # GitHub URL
            'tools': list[dict], # [{name, description}]
            'title': str,        # display title
            'tier': str,         # 'Official'
            'owner': str         # 'Red Hat'
        }
    """

def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse .mcp.json from a pack directory.
    Returns [] if .mcp.json does not exist.

    Supports: command-based and HTTP-based (type='http') servers
    """

def extract_env_vars(env_dict: Dict[str, str]) -> List[str]:
    """
    Extract env variable names from ${VAR} format values.

    Args:
        env_dict: e.g. {'LIGHTSPEED_CLIENT_ID': '${LIGHTSPEED_CLIENT_ID}'}

    Returns:
        Sorted list of variable names e.g. ['LIGHTSPEED_CLIENT_ID']
        Literal values (not ${VAR} format) return the key name instead.
    """

def extract_header_env_vars(headers: Dict[str, str]) -> List[str]:
    """
    Extract env variable names from ${VAR} patterns in HTTP header values.

    Args:
        headers: e.g. {'Authorization': 'Bearer ${AAP_API_TOKEN}'}

    Returns:
        List of variable names e.g. ['AAP_API_TOKEN']
    """

def load_custom_mcp_data() -> Dict[str, Any]:
    """
    Load custom MCP server metadata from docs/mcp.json.

    Returns:
        Dict mapping server names to custom data:
        {
            'openshift': {
                'title': 'OpenShift MCP Server',
                'owner': 'Official',
                'repository': 'https://github.com/...',
                'tools': [{'name': 'events_list', 'description': '...'}]
            }
        }
        Returns {} if docs/mcp.json does not exist.
    """
```

---

## scripts/build_website.py

Builds the documentation website data file by combining pack and MCP data.

```python { .api }
def build_website() -> None:
    """
    Generate docs/data.json from all pack and MCP data.

    Reads: all pack .mcp.json files, all SKILL.md/agent .md files,
           docs/plugins.json, docs/mcp.json, docs/icons.json
    Writes: docs/data.json

    Output structure:
    {
        'repository': {
            'name': 'agentic-collections',
            'owner': 'Red Hat Ecosystem Engineering',
            'description': str,
            'url': 'https://github.com/RHEcosystemAppEng/agentic-collections'
        },
        'packs': [pack_dict, ...],       # from generate_pack_data(), with 'icon' added
        'mcp_servers': [server_dict, ...], # from generate_mcp_data(), with 'icon' added
        'generated_at': 'ISO timestamp'
    }
    """

def load_icons() -> Dict[str, Dict[str, str]]:
    """
    Load icon mappings from docs/icons.json.

    Returns:
        Dict with structure:
        {
            'packs': {'rh-sre': 'icon-url', ...},
            'mcp_servers': {'lightspeed-mcp': 'icon-url', ...}
        }
        Returns {'packs': {}, 'mcp_servers': {}} if docs/icons.json missing.
    """
```

**Usage:**
```bash
uv run python scripts/build_website.py
# Writes: docs/data.json
# Start server: cd docs && uv run python -m http.server 8000
```

---

## scripts/validate_mcp_types.py

Validates MCP server type detection and parsing correctness.

```python { .api }
def validate_mcp_types() -> bool:
    """
    Validate that both command-based and HTTP servers parse correctly.

    Asserts:
      - Command servers: have non-empty command, empty URL and headers
      - HTTP servers: have non-empty URL, empty command and args

    Returns:
        True on success
    Raises:
        AssertionError on validation failure
    """
```

**Usage:**
```bash
uv run python scripts/validate_mcp_types.py
# Output: lists command-based and HTTP servers found
# Raises: AssertionError if server type mismatch detected
```

---

## scripts/check_site.py

Interactive site verification after running `make serve`. Loads `docs/data.json` and prints a summary and manual testing checklist.

```python { .api }
def load_data() -> dict:
    """
    Load docs/data.json.
    Exits with error if file not found (run 'make generate' first).

    Returns:
        Full data.json contents as dict
    """

def print_summary(data: dict) -> None:
    """
    Print summary of repository, packs, and MCP servers to stdout.
    Shows: repository info, each pack's name/version/skill counts,
           each MCP server's name, command, env vars, security isolation.
    """

def print_checklist() -> None:
    """
    Print manual testing checklist for browser verification at http://localhost:8000.
    Covers: header, collections section, MCP servers section, search, responsive design.
    """

def main() -> None:
    """
    Entry point. Loads data.json, prints summary and testing checklist.
    """
```

**Usage:**
```bash
# First start the server
make serve &
# Then run the checker
uv run python scripts/check_site.py
```

---

## Shell Scripts

```bash { .api }
# Run agentskills.io linter (Tier 1) on a skill directory
./scripts/run-skill-linter.sh skills/<skill-name>/
./scripts/run-skill-linter.sh rh-sre/skills/cve-impact/

# Detect changed skill files (git-aware)
./scripts/detect-changed-skills.sh
# Output: list of changed SKILL.md paths

# CI validation of changed skills
./scripts/ci-validate-changed-skills.sh
# With VALIDATE_INCLUDE_UNCOMMITTED=1: includes staged + unstaged changes

# Validate all skills across all packs
./scripts/validate-skills.sh

# Install gitleaks pre-commit hook
./scripts/install-hooks.sh

# Run local test verification
./scripts/test_local.sh
```

## docs/ Data Files Reference

```python { .api }
# docs/plugins.json — pack display title mappings
{
    "rh-sre": {"title": "Red Hat SRE Agentic Skills Collection"},
    "rh-virt": {"title": "Red Hat OpenShift Virtualization Agentic Collection"},
    "rh-developer": {"title": "Red Hat Developer Agentic Skills Collection"},
    "ocp-admin": {"title": "Red Hat OpenShift Administration Agentic Skills Collection"},
    "rh-support-engineer": {"title": "Red Hat Support Engineer Agentic Skills Collection"}
}

# docs/mcp.json — custom MCP server metadata schema
{
    "<server-name>": {
        "title": "Display Title",             # optional
        "owner": "Official|Community",        # optional
        "repository": "https://github.com/...", # optional — shows README badge
        "tier": "Official",                   # optional
        "tools": [                            # optional — shown in server details
            {"name": "tool_name", "description": "What this tool does"}
        ]
    }
}

# docs/icons.json — icon URL mappings
{
    "packs": {"rh-sre": "icon-url"},
    "mcp_servers": {"lightspeed-mcp": "icon-url"}
}
```
