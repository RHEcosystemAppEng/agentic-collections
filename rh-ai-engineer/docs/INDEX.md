---
title: Documentation Index
category: index
tags: [index, navigation, documentation-map]
semantic_keywords: [documentation index, doc navigation, reference lookup]
last_updated: 2026-02-26
---

# rh-ai-engineer Documentation Index

Documentation map for the Red Hat AI Engineer agentic collection. Use this index to find the right document for your task.

## Reference Documentation

| Document | Path | When to Consult |
|----------|------|-----------------|
| [Supported Runtimes](references/supported-runtimes.md) | `docs/references/supported-runtimes.md` | Selecting a serving runtime (vLLM, NIM, Caikit+TGIS), comparing runtime capabilities, understanding runtime prerequisites |
| [Known Model Profiles](references/known-model-profiles.md) | `docs/references/known-model-profiles.md` | Determining GPU requirements for a model, configuring vLLM args, checking hardware compatibility before deployment |
| [Live Doc Lookup Protocol](references/live-doc-lookup.md) | `docs/references/live-doc-lookup.md` | When a model is not in known-model-profiles.md, when encountering unfamiliar errors, when runtime documentation may be stale |

## Skills Quick Reference

| Skill | Command | Purpose |
|-------|---------|---------|
| [NIM Setup](../skills/nim-setup/SKILL.md) | `/nim-setup` | One-time NVIDIA NIM platform configuration (NGC secrets, Account CR) |
| [Model Deploy](../skills/model-deploy/SKILL.md) | `/model-deploy` | Deploy models using KServe with vLLM, NIM, or Caikit+TGIS runtimes |

## Document Consultation Guide

Skills in this collection follow the Document Consultation Transparency principle (CLAUDE.md Design Principle #1). The consultation order is:

1. **Before runtime selection**: Read [supported-runtimes.md](references/supported-runtimes.md)
2. **Before deployment**: Read [known-model-profiles.md](references/known-model-profiles.md)
3. **When model not found**: Read [live-doc-lookup.md](references/live-doc-lookup.md), then use WebFetch
