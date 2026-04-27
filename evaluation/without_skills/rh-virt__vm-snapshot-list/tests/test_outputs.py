"""
Tests for rh-virt__vm-snapshot-list per-skill evaluation.
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

    def test_mentions_snapshots(self):
        content = read_report().lower()
        assert "snapshot" in content, "report should mention snapshots"

    def test_has_structured_output(self):
        content = read_report()
        assert "|" in content or "- " in content, "report should have structured output (table or list)"


class TestSkillDependent:
    def test_ready_to_use_status(self):
        """Skill: readyToUse status for restore readiness."""
        c = read_report().lower()
        assert any(t in c for t in ["readytouse", "ready to use", "ready for restore"]), (
            "should reference readyToUse status for snapshot readiness"
        )

    def test_creation_timestamp(self):
        """Skill: metadata.creationTimestamp or creation time."""
        c = read_report().lower()
        assert any(t in c for t in ["creationtimestamp", "creation timestamp", "created", "when"]), (
            "should show creation timestamp for each snapshot"
        )

    def test_phase_status(self):
        """Skill: status.phase (Succeeded, Failed, InProgress)."""
        c = read_report().lower()
        assert any(t in c for t in ["succeeded", "failed", "inprogress", "status.phase", "phase"]) and (
            "succeeded" in c or "failed" in c or "phase" in c
        ), (
            "should show phase (Succeeded/Failed/InProgress)"
        )

    def test_label_selector_for_vm_filtering(self):
        """Skill teaches using vm.kubevirt.io/name label selector to
        filter snapshots by source VM. Without skill, agents list all
        snapshots without label-based filtering."""
        c = read_report()
        assert "vm.kubevirt.io" in c or "labelSelector" in c or "label selector" in c.lower(), (
            "should reference vm.kubevirt.io/name label for snapshot filtering"
        )
