<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, CLAUDE.md, marketplace/rh-agentic-collection.yml
-->

- **Credentials:** Environment variables only — never hardcoded in any project file or echoed in assistant output. Skills verify that variables are set without printing their values.
- **Container isolation:** The Lightspeed MCP server runs in a Podman container; host credentials are injected at runtime via `--env` flags.
- **No write operations:** All skills are read-only with respect to Red Hat platform data. No remediation playbooks are generated or executed by this pack.
- **Self-removing setup skill:** `red-hat-get-started` deletes itself from the project after completing its one-time task.
