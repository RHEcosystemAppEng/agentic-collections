"""
Tests for rh-virt__vm-snapshot-restore per-skill evaluation.
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

    def test_mentions_restore(self):
        content = read_report().lower()
        assert "restor" in content, "report should discuss restore operation"

    def test_mentions_snapshot(self):
        content = read_report().lower()
        assert "snapshot" in content or "backup" in content, "report should mention the snapshot"


class TestSkillDependent:
    def test_vm_stopped_prerequisite(self):
        """Skill: VM must be stopped before restore; stop-and-restore option."""
        c = read_report().lower()
        assert any(t in c for t in ["stop before restor", "must be stopped", "stop-and-restore", "vm must be stopped", "halt"]) and (
            "stop" in c and "restor" in c
        ), (
            "should require VM stopped before restore"
        )

    def test_destructive_warning(self):
        """Skill: Data loss warning; changes since snapshot will be lost."""
        c = read_report().lower()
        assert any(t in c for t in ["data loss", "changes since", "will be lost", "overwrite", "destructive", "replace current", "cannot recover"]), (
            "should warn about data loss from restore"
        )

    def test_restore_cr(self):
        """Skill: VirtualMachineRestore CR with target and snapshot reference."""
        c = read_report().lower()
        assert "virtualmachinerestore" in c and any(t in c for t in ["target", "virtualmachinesnapshotname", "spec"]), (
            "should define VirtualMachineRestore resource"
        )

    def test_post_restore_verification(self):
        """Skill: Verify restore complete; status.complete; start VM after."""
        c = read_report().lower()
        assert any(t in c for t in ["status.complete", "restore complete", "post-restore", "after restore", "start vm", "start the vm"]) and (
            "restor" in c or "complete" in c or "start" in c
        ), (
            "should include post-restore verification or start step"
        )

    def test_typed_confirmation(self):
        """Skill: Typed snapshot name confirmation before restore."""
        c = read_report().lower()
        assert any(t in c for t in ["type", "typed", "exact name", "to confirm", "snapshot name"]) and (
            "confirm" in c or "type" in c
        ), (
            "should require typed snapshot name confirmation"
        )
