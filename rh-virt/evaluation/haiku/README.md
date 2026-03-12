# Haiku Variants

The Haiku folders only contain `instruction.md` files — everything else (Dockerfiles, mock MCP server, tests, task.toml) is identical to the Sonnet variants.

The only differences from Sonnet:

- **Instructions** use emphatic CAPS reminders and numbered sub-steps to ensure Haiku reads the skill files
- **`task.toml`** sets `LLM_JUDGE_MODEL = "claude-3-5-haiku"` instead of `claude-sonnet-4-5`
