# Haiku Variants

The Haiku folders only contain files that differ from Sonnet — specifically the `instruction.md` files. Everything else (Dockerfiles, mock MCP server, tests, `task.toml`) is identical to the Sonnet variants.

The instruction difference: Haiku instructions use emphatic CAPS reminders and numbered sub-steps to help Haiku discover and follow the available skill files.

**Note:** When running evaluations with Harbor and SkillsBench, each task must be a self-contained folder with the full required structure (`instruction.md`, `task.toml`, `environment/`, `tests/`). Copy the shared files from the Sonnet variant and replace only `instruction.md` with the Haiku version.
