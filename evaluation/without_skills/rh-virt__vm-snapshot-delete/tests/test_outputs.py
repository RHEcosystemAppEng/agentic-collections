"""
Tests for rh-virt__vm-snapshot-delete per-skill evaluation.
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

    def test_mentions_snapshot(self):
        content = read_report().lower()
        assert "snapshot" in content, "report should mention snapshots"

    def test_mentions_deletion(self):
        content = read_report().lower()
        assert "delet" in content, "report should discuss deletion"


class TestSkillDependent:
    def test_restore_conflict_check(self):
        """Skill: Active VirtualMachineRestore blocks snapshot deletion."""
        c = read_report().lower()
        assert any(t in c for t in ["virtualmachinerestore", "restore", "in use", "active restore", "block delet"]) and (
            "restore" in c or "conflict" in c
        ), (
            "should check for active restore blocking deletion"
        )

    def test_last_snapshot_warning(self):
        """Skill: Warn when deleting the only snapshot for a VM."""
        c = read_report().lower()
        assert any(t in c for t in ["last snapshot", "only snapshot", "no recovery", "only remaining", "no other snapshot"]) or (
            "last" in c and "snapshot" in c and ("warn" in c or "only" in c)
        ), (
            "should warn when deleting the last snapshot for a VM"
        )

    def test_storage_reclaim(self):
        """Skill: Storage freed by deletion; recovery point lost."""
        c = read_report().lower()
        assert any(t in c for t in ["storage freed", "storage reclaim", "freed", "recovery point"]), (
            "should mention storage reclamation or recovery point loss"
        )

    def test_virtualmachinesnapshot_delete(self):
        """Skill: Delete VirtualMachineSnapshot resource."""
        c = read_report().lower()
        assert any(t in c for t in ["virtualmachinesnapshot", "resources_delete", "delete snapshot"]) and (
            "snapshot" in c
        ), (
            "should reference VirtualMachineSnapshot deletion"
        )

    def test_list_other_snapshots(self):
        """Skill: List other snapshots for same VM before delete."""
        c = read_report().lower()
        assert any(t in c for t in ["spec.source.name", "label selector", "vm.kubevirt.io/name", "other snapshot", "list snapshot", "same vm"]), (
            "should list other snapshots for the VM"
        )
