# Remediation Availability Indicators (get_cve Response)

Read this reference when interpreting `vulnerability__get_cve` or `get_cve` response to determine if automated remediation is available.

## CRITICAL: Correct vs Incorrect Indicators

### ✅ USE These Fields for Remediation Availability

| Field | Meaning | Remediation Available When |
|-------|---------|-----------------------------|
| `advisory_available` | Red Hat Security Advisory exists | `true` |
| `remediation` | Remediation status code | `2` = automated remediation available |
| `advisories_list` | List of RHSA/errata IDs | Non-empty (e.g. `["RHSA-2026:2719"]`) |

**Decision rule**: Remediation IS available when `advisory_available === true` OR `remediation === 2` OR `advisories_list` is non-empty.

### ❌ DO NOT Use These Fields for Remediation

| Field | Meaning | Why NOT to Use |
|-------|---------|----------------|
| `rules` | Red Hat Insights **Advisor** rules | Advisor rules are separate from vulnerability remediation. Empty `rules: []` does NOT mean no remediation. Remediation comes from Security Advisories (RHSA), not Advisor rules. |

**Common mistake**: Agent sees `rules: []` (empty) and incorrectly concludes "no remediation available." This is WRONG. Always check `advisory_available` and `remediation` first.

## Interpretation Checklist

When evaluating `get_cve` response:

1. **Check `advisory_available`**: If `true` → remediation available ✓
2. **Check `remediation`**: If `2` → automated remediation available ✓
3. **Check `advisories_list`**: If non-empty (e.g. RHSA-*) → remediation available ✓
4. **Ignore `rules`**: Do NOT use for remediation decision. Empty rules ≠ no remediation.

## Example: Remediation Available (rules empty)

```json
{
  "advisory_available": true,
  "advisories_list": ["RHSA-2026:2719"],
  "remediation": 2,
  "rules": []
}
```

**Correct interpretation**: Remediation IS available. `rules: []` only means no Advisor rule—remediation comes from RHSA-2026:2719.

## Example: No Remediation

```json
{
  "advisory_available": false,
  "advisories_list": [],
  "remediation": 0,
  "rules": []
}
```

**Correct interpretation**: No automated remediation. Manual steps required.

## get_cve_systems Response (per-system)

When using `get_cve_systems` for system-level check, each system entry may include:
- `attributes.advisory_available` — same meaning as get_cve
- `attributes.remediation` — same meaning as get_cve

Use the same interpretation rules. Do NOT use `rules` for remediation decision.
