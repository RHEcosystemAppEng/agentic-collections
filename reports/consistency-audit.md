# Consistency Audit Report

- Generated: `2026-04-21T12:52:58.657554+00:00`
- Branch: `001-collection-consistency-audit`
- Total packs: `7`
- Total findings: `6`

## Severity Summary

- blocking: `0`
- high: `5`
- medium: `0`
- informational: `1`

## Matrix

| Pack | Registration | Version | Model | Claims | Style | Overall |
|---|---|---|---|---|---|---|
| rh-sre | registered | warn | pass | warn | warn | none |
| rh-developer | registered | warn | pass | warn | warn | none |
| ocp-admin | registered | warn | pass | warn | warn | none |
| rh-support-engineer | excluded-by-policy | warn | pass | warn | warn | high |
| rh-virt | registered | warn | pass | warn | warn | none |
| rh-ai-engineer | registered | warn | pass | warn | warn | none |
| rh-automation | registered | warn | pass | warn | warn | none |

## Findings

- [informational] `VER-001` Pack 'rh-support-engineer' is not listed in marketplace modules (marketplace/rh-agentic-collection.yml)
- [high] `VER-002` Pack README missing for 'rh-support-engineer' (rh-support-engineer/README.md)
- [high] `CLM-001` Root README total skill count is out of sync with repository reality (README.md)
- [high] `VIS-002` Missing icon mapping for pack 'rh-support-engineer' (docs/icons.json)
- [high] `VIS-002` Missing plugin display metadata for pack 'rh-support-engineer' (docs/plugins.json)
- [high] `VIS-003` Documentation site data file is missing or has not yet been generated (docs/data.json)
