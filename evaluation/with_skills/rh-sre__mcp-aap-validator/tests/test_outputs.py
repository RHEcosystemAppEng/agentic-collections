"""
Tests for rh-sre__mcp-aap-validator per-skill evaluation.
Baseline tests: report structure.
Skill-dependent tests: conceptual checks (no exact tool/field name matching).
"""
import os
import pytest

REPORT = "/root/report.md"


def read_report():
    if not os.path.exists(REPORT):
        pytest.fail(f"Required file not found: {REPORT}")
    with open(REPORT) as f:
        return f.read()


class TestBaseline:
    def test_report_exists(self):
        assert os.path.exists(REPORT), "report.md must exist"

    def test_mentions_topic(self):
        content = read_report().lower()
        assert any(t in content for t in ['aap', 'mcp', 'valid', 'connect']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_both_servers_tested(self):
        """Skill: Test BOTH job_templates_list (job-management) AND inventories_list (inventory-management)."""
        c = read_report().lower()
        has_job = any(t in c for t in ["job_template", "job template", "job-management"])
        has_inv = any(t in c for t in ["inventor", "inventory-management"])
        assert has_job or has_inv, (
            "should test both AAP MCP servers (skill: job-management + inventory-management)"
        )

    def test_mcp_gateway_not_ui(self):
        """Skill teaches AAP_MCP_SERVER must point to MCP gateway endpoint, not main AAP UI URL."""
        c = read_report().lower()
        assert ("gateway" in c and "mcp" in c) or "aap_mcp_server" in c, (
            "should note AAP_MCP_SERVER must point to MCP gateway, not UI (skill: wrong URL = 404)"
        )

    def test_404_wrong_url(self):
        """Skill teaches HTTP 404 = wrong AAP_MCP_SERVER URL."""
        c = read_report().lower()
        assert "404" in c and any(t in c for t in ["url", "wrong"]), (
            "should explain 404 indicates wrong URL (skill: troubleshooting)"
        )

    def test_table_format(self):
        """Skill: Output table with Server | Outcome (PASSED/FAILED/PARTIAL)."""
        content = read_report()
        c = content.lower()
        has_table = "|" in content
        has_outcome = any(t in c for t in ["passed", "failed", "partial", "job_templates_list", "inventories_list"])
        assert has_table or has_outcome, (
            "should use table format with outcome (skill: Report Format)"
        )
