"""
Tests for rh-sre__job-template-remediation-validator per-skill evaluation.
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
        assert any(t in content for t in ['valid', 'job template', 'check']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_ask_job_type_on_launch(self):
        """Skill teaches ask_job_type_on_launch: true is required for check vs run modes."""
        c = read_report().lower()
        assert any(t in c for t in ["ask_job_type", "ask_job_type_on_launch"]), (
            "should require ask_job_type_on_launch (skill: for check vs run)"
        )

    def test_credentials_check_both_fields(self):
        """Skill teaches credentials may be in summary_fields.credentials OR credentials array."""
        c = read_report().lower()
        assert any(t in c for t in ["summary_fields", "credentials array", "both"]), (
            "should check credentials in summary_fields or credentials array (skill-specific)"
        )

    def test_become_enabled_required(self):
        """Skill: become_enabled required for package updates."""
        c = read_report().lower()
        assert any(t in c for t in ["become", "privilege", "escalat", "sudo"]), (
            "should require privilege escalation (skill: required for remediation)"
        )

    def test_required_vs_recommended(self):
        """Skill: Distinguish required (inventory, project, playbook, credentials, become, ask_job_type) vs recommended (ask_variables, ask_limit)."""
        c = read_report().lower()
        has_required = any(t in c for t in ["required", "must", "inventory", "project", "playbook"])
        has_recommended = any(t in c for t in ["recommended", "warn", "variable", "limit"])
        assert has_required or has_recommended, (
            "should distinguish required vs recommended checks (skill: Phase 2 vs 3)"
        )
