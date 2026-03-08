# Fleet Inventory Parameter Reference

Read when calling `get_host_details` or `get_cve_systems` to ensure correct parameters.

## get_host_details

**Parameters** (based on user query):

```python
# No filters
get_host_details()

# Specific system
get_host_details(system_id="abc-123")

# Hostname pattern
get_host_details(hostname_pattern="web-*")

# Tag filter
get_host_details(tags=["production"])

# RHEL version filter
get_host_details(operating_system__version__startswith="8")

# Combined
get_host_details(tags=["production", "web-tier"], operating_system__version__startswith="8")
```

**Response fields**: id, display_name, fqdn, rhel_version, last_seen, tags, stale, satellite_managed

## get_cve_systems

**Parameters**: `cve_id` (string, format CVE-YYYY-NNNNN, uppercase)

```python
get_cve_systems(cve_id="CVE-2024-1234")
```

**Response fields**: cve_id, affected_systems (system_id, display_name, status, remediation_available), total_affected, total_remediated, total_vulnerable

**Status values**: Vulnerable (patch needed), Patched (no action), Not Affected (exclude)

## Filtering and Sorting

**By RHEL**: `[s for s in systems if s['rhel_version'].startswith("8")]`
**By tag**: `[s for s in systems if "production" in s.get('tags', [])]`
**By stale**: `[s for s in systems if not s.get('stale', False)]`
**Sort by last_seen**: `sorted(systems, key=lambda s: s['last_seen'], reverse=True)`
**Sort by display_name**: `sorted(systems, key=lambda s: s['display_name'])`
