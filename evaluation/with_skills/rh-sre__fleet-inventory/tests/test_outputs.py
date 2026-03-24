"""
Tests for rh-sre__fleet-inventory per-skill evaluation.
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
        assert any(t in content for t in ['system', 'host', 'fleet', 'inventory']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_system_identifier_tracking(self):
        """Skill teaches tracking system identifiers for follow-up actions.
        Without skill, agents list systems without identifiers for remediation."""
        c = read_report().lower()
        assert any(t in c for t in [
            "system id", "system_id", "system_uuid", "uuid", "identifier",
        ]) and any(t in c for t in [
            "remediat", "follow-up", "subsequent", "action", "track",
        ]), (
            "should track system identifiers for follow-up remediation actions"
        )

    def test_remediation_transition_offer(self):
        """Skill: Offer transition to a remediation workflow for CVE remediation."""
        c = read_report().lower()
        assert any(t in c for t in [
            "next step", "remediate", "playbook",
            "remediation workflow", "remediation action",
        ]), "should offer next steps for remediation"

    def test_classification_criteria_reference(self):
        """Skill/docs teach consulting classification criteria or reference
        documentation before interpreting vulnerability data. Without skill,
        agents classify CVEs based on general knowledge alone."""
        c = read_report().lower()
        assert any(t in c for t in [
            "classification criteria", "classification methodology",
            "vulnerability classification", "cve classification",
        ]) or (
            "classification" in c and any(t in c for t in [
                "consult", "reference", "methodology", "criteria",
            ])
        ), "should reference CVE classification criteria or methodology"
