# CVE Pagination Skill with HITL-First Pattern

Create a skill that retrieves all security vulnerabilities affecting a specific system. Because large systems may have thousands of CVEs requiring many API calls, the skill must present a pagination strategy prompt to the user and wait for their choice BEFORE making any tool calls or resolving any identifiers.

## Capabilities

### HITL-first pagination prompt

When a system-level CVE query is requested, the skill's very first action is to display a pagination options prompt and wait for the user to choose a strategy. No MCP tool calls or hostname resolution occur before this prompt.

- The pagination prompt is the first user-visible response; no `find_host_by_name` or `get_system_cves` calls appear before it [@test](./tests/test_hitl_before_tool_calls.md)
- The pagination prompt offers at least three options: first page only, all pages, and N pages [@test](./tests/test_three_pagination_options.md)

### Warning about first-page limitations

The pagination prompt informs the user that retrieving only the first page may return zero remediatable CVEs, because remediatable vulnerabilities may appear on any page.

- The prompt includes a warning that first-page-only results may show 0 remediatable CVEs [@test](./tests/test_first_page_warning.md)

### Correct pagination loop implementation

After the user selects a strategy, the skill pages through results using limit and offset parameters, accumulating results across pages until the chosen stopping condition is met.

- The pagination loop passes `limit=100` per request and increments the offset on each iteration [@test](./tests/test_pagination_loop.md)
- The loop stops when: the page returns fewer results than the limit (last page), the user-specified page count is reached, or "all pages" mode and no more results [@test](./tests/test_stop_conditions.md)

### System UUID resolution after strategy selection

Hostname-to-UUID resolution occurs only after the user has confirmed the pagination strategy, not before.

- The hostname lookup tool call appears in the workflow after the pagination prompt response is processed, not before [@test](./tests/test_uuid_resolution_order.md)

## Implementation

[@generates](./skills/system-cve-fetcher/SKILL.md)

## API

```markdown { #api }
## Workflow

### Step -1: Pagination HITL Gate (MANDATORY — FIRST RESPONSE)
Display to user:
"""
To fetch CVEs on this system, I will paginate through vulnerability data (limit=100/page).
Systems may have 1,700+ CVEs (~18 API calls).

⚠️ First page only may return 0 remediatable CVEs—they may be on any page.

Options:
- **First page only**: Fetch 100 CVEs (quick overview, may miss remediatable)
- **All pages**: Fetch until no more results (recommended for remediatable)
- **N pages**: Fetch up to N×100 CVEs

How would you like to proceed? (first page / all pages / N pages)
"""
WAIT for user response. Do NOT proceed until response received.

### Step 0: Resolve Hostname to UUID
After user selects strategy: invoke inventory find_host_by_name
Parameters: name: "<hostname>"

### Step 1: Paginate CVE Results
Loop: get_system_cves(system_uuid=<uuid>, limit=100, offset=<page*100>)
Stop when: last page reached OR page count limit reached

### Step 2: Filter and Report
Filter for advisory_available=true if remediatable requested
Present summary table
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing the rh-sre pagination handling patterns, HITL-first workflow conventions, and system CVE retrieval best practices for large-dataset agentic skills.
