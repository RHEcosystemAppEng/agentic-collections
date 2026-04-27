"""
Tests for rh-sre__execution-summary per-skill evaluation.
Baseline tests: report structure.
Skill-dependent tests: skill-specific patterns (not generic report quality).
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
        assert any(t in content for t in ['summary', 'execution', 'remediation']), (
            "report should mention execution summary or remediation"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 300, "execution summary should be substantial"


class TestSkillDependent:
    def test_methodology_phases(self):
        """Structuring execution into methodology phases
        (data collection, evidence gathering, etc.)."""
        c = read_report().lower()
        phase_terms = [
            "data collection", "evidence gathering", "discovery",
            "triage", "assessment", "verification",
            "phase 1", "phase 2", "step 1", "step 2",
        ]
        found = sum(1 for t in phase_terms if t in c)
        assert found >= 2, (
            f"should organize execution into methodology phases (found {found})"
        )

    def test_docs_from_consulted(self):
        """Extract docs from 'I consulted' statements; path from docs/ or skills/ onwards."""
        c = read_report().lower()
        has_docs = any(t in c for t in ["docs/", "skills/", "consult", "documentation"])
        assert has_docs, (
            "should list documentation consulted"
        )
