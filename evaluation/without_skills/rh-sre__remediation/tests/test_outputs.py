"""
Tests for rh-sre__remediation per-skill evaluation.
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
        assert any(t in content for t in ['remediation', 'orchestrat', 'workflow']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_seven_step_sequence(self):
        """Skill: Orchestrate in order: validate MCP → impact → validate CVE → context → playbook → execute → verify."""
        c = read_report().lower()
        has_sequence = any(t in c for t in ["validate", "impact", "context", "playbook", "execute", "verify"])
        has_order = any(t in c for t in ["step", "phase", "before", "workflow order", "sequence"])
        assert has_sequence and has_order, (
            "should define 7-step orchestration sequence (skill: workflow order)"
        )

    def test_remediatable_gate(self):
        """Skill: Gate on cve-validation: if not remediatable, stop or warn before playbook generation."""
        c = read_report().lower()
        has_gate = any(t in c for t in ["remediat", "gate", "remediation_available", "advisory"])
        has_stop = any(t in c for t in ["stop", "cannot proceed", "no automated", "manual"])
        assert has_gate or has_stop, (
            "should gate on remediation availability (skill: Remediatable Gate)"
        )

    def test_plan_validation_before_execute(self):
        """Skill: Present Remediation Plan (summary, table, checklist); wait for user yes/proceed before Step 5."""
        c = read_report().lower()
        has_plan = any(t in c for t in ["plan", "checklist", "summary", "table"])
        has_confirm = any(t in c for t in ["confirm", "proceed", "approval", "yes", "abort"])
        assert has_plan and has_confirm, (
            "should require plan validation before execution (skill: Remediation Plan)"
        )

    def test_dry_run_recommendation(self):
        """Skill: Recommend dry-run first; wait for explicit approval before actual execution."""
        c = read_report().lower()
        assert any(t in c for t in ["dry-run", "dry run", "check mode", "preview"]), (
            "should recommend dry-run first (skill: before Step 5)"
        )

    def test_two_part_confirmation(self):
        """Docs teach Part A (pre-Step-0) and Part B (post-Step-4) confirmations
        with ordered step completion marking. Without docs, agents use single confirmation."""
        c = read_report().lower()
        assert any(t in c for t in [
            "part a", "part b", "pre-step", "post-step", "two-part",
            "before step 0", "after step 4",
        ]) or ("confirm" in c and "step" in c), (
            "should use two-part confirmation (Part A pre-Step-0, Part B post-Step-4)"
        )
