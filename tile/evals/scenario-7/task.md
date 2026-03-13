# AI-Optimized Documentation Index

Create the semantic indexing system for an agentic pack's knowledge base. The system must enable AI agents to discover relevant documents efficiently without reading the entire corpus, and must include three interconnected index files that together support progressive document loading.

## Capabilities

### Semantic index structure

The semantic index contains metadata for each document including title, category, file path, semantic keywords for AI discovery, use-case identifiers, and related document cross-references.

- Each entry in the semantic index includes `semantic_keywords`, `use_cases`, and `related_docs` fields [@test](./tests/test_semantic_entry_fields.md)
- The semantic index file is small enough (~200 tokens per entry) to allow agents to read the full index without loading individual documents [@test](./tests/test_index_token_efficiency.md)

### Task-to-docs mapping

The task-to-docs mapping pre-computes which documents are needed for common task types, allowing agents to load exactly the right documents without scanning the full index.

- Each task type key maps to an array of document paths that should be loaded for that workflow [@test](./tests/test_task_mapping_format.md)
- Common workflow task types (e.g., "cve_remediation", "vm_creation") have pre-computed doc sets [@test](./tests/test_common_workflows_mapped.md)

### Cross-reference graph

The cross-reference graph captures relationships between documents so agents can follow related-content chains.

- Each document node in the graph includes an array of related document paths [@test](./tests/test_cross_reference_structure.md)

### Document YAML frontmatter

Each documentation file includes mandatory frontmatter fields for indexing: title, category, sources with attribution, tags, semantic_keywords, use_cases, related_docs, and last_updated.

- A documentation file with all mandatory frontmatter fields passes index validation [@test](./tests/test_doc_frontmatter_complete.md)
- A documentation file without `semantic_keywords` or `use_cases` cannot be discovered via the index [@test](./tests/test_missing_keywords.md)

## Implementation

[@generates](./docs/.ai-index/)

## API

```json { #api }
// semantic-index.json
{
  "documents": [
    {
      "id": "<doc-id>",
      "title": "<Document Title>",
      "path": "docs/<category>/<file>.md",
      "category": "<rhel|ansible|openshift|insights|references>",
      "semantic_keywords": ["<keyword1>", "<keyword2>"],
      "use_cases": ["<task-id-1>", "<task-id-2>"],
      "related_docs": ["<other-doc-id>"]
    }
  ]
}

// task-to-docs-mapping.json
{
  "<task-type>": ["<doc-path-1>", "<doc-path-2>"]
}

// cross-reference-graph.json
{
  "<doc-id>": {
    "related": ["<other-doc-id-1>", "<other-doc-id-2>"]
  }
}
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing the rh-sre AI-optimized documentation system conventions, semantic indexing patterns, and documentation YAML frontmatter standards for token-efficient agentic knowledge bases.
