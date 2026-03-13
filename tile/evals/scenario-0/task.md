# Skill Definition File

Create a skill definition file for a read-only operation that checks and reports the health status of a containerized workload. The skill should be suitable for use in an AI agentic collection and follow the standard structure for such files, including proper metadata classification.

## Capabilities

### Valid frontmatter fields

The skill definition file contains all required metadata fields: a kebab-case identifier that matches the file's parent directory name, a concise description (under 500 tokens) that includes specific usage examples and anti-patterns, a model preference field, and a color field that reflects the read-only nature of the operation.

- A skill named `workload-health` with color `cyan` and model `inherit` has all required frontmatter fields populated [@test](./tests/test_frontmatter_complete.md)
- A skill description includes at least one "Use when" example and at least one "NOT for" anti-pattern with an alternative skill [@test](./tests/test_description_format.md)

### Correct risk classification

The color value in the frontmatter correctly reflects the operational risk of the skill.

- A skill performing only read/list/view operations uses the color value reserved for read-only operations (`cyan`) [@test](./tests/test_color_readonly.md)
- A skill that creates or modifies resources uses a color value other than `cyan` [@test](./tests/test_color_nonreadonly.md)

## Implementation

[@generates](./skills/workload-health/SKILL.md)

## API

```yaml { #api }
# YAML frontmatter block at the top of SKILL.md
---
name: <kebab-case-name>          # required, matches directory name
description: |                   # required, <500 tokens
  <overview>
  Use when:
  - "<example query 1>"
  NOT for <anti-pattern> (use /<alternative-skill> instead).
model: inherit | sonnet | haiku  # required
color: cyan | green | blue | yellow | red  # required
metadata:                        # optional custom fields
  author: "<team>"
---
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing conventions, design principles, and skill structure standards for authoring AI-native skills for Red Hat platforms.
