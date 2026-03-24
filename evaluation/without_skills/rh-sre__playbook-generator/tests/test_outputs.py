"""
Tests for rh-sre__playbook-generator per-skill evaluation.
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
        assert any(t in content for t in ['playbook', 'generat', 'cve']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_mcp_tool_for_generation(self):
        """Skill: Use create_vulnerability_playbook MCP tool, not manual playbook writing."""
        c = read_report().lower()
        assert any(t in c for t in [
            "create_vulnerability_playbook", "create_vuln_playbook",
            "remediations", "lightspeed",
        ]) and any(t in c for t in ["tool", "mcp", "generat"]), (
            "should reference MCP tool usage for playbook generation (not manual writing)"
        )

    def test_no_modifications_to_playbook(self):
        """Skill: Return playbook AS IS, no modifications—never add pre-flight, backup, restart."""
        c = read_report().lower()
        assert any(t in c for t in [
            "as is", "as-is", "unmodified", "do not modify", "no modification",
            "unchanged", "without modification", "returned unchanged",
            "original output", "generated output",
        ]), "should return playbook unmodified (skill: no enhancements without user approval)"

    def test_no_auto_generate_on_failure(self):
        """Skill: Never auto-generate playbooks from general knowledge without approval."""
        c = read_report().lower()
        has_constraint = any(t in c for t in [
            "do not auto", "never auto", "not auto-generat",
            "without approval", "explicit approval", "user approval",
            "do not generat", "never generat",
        ])
        has_options = any(t in c for t in ["retry", "option", "escalat"])
        assert has_constraint or has_options, (
            "should state not to auto-generate playbooks without user approval"
        )

    def test_delegation_to_executor(self):
        """Skill: This skill ONLY generates; execution delegated to playbook-executor."""
        c = read_report().lower()
        assert any(t in c for t in [
            'delegat', 'executor', 'playbook-executor', 'hand off',
            'not execute', 'do not run', 'do not execute',
            'not run ansible-playbook', 'not ansible-playbook',
        ]), "should delegate execution (not run ansible-playbook directly)"
