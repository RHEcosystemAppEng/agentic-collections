"""
Tests for rh-virt__vm-delete per-skill evaluation.
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

    def test_mentions_vm(self):
        content = read_report().lower()
        assert any(t in content for t in ["vm", "virtual machine", "virtualmachine"]), (
            "report should reference the target VM"
        )

    def test_mentions_deletion(self):
        content = read_report().lower()
        assert "delet" in content, "report should discuss deletion"


class TestSkillDependent:
    def test_stop_before_delete(self):
        """Skill: Must stop VM before deletion; vm_lifecycle stop."""
        c = read_report().lower()
        assert any(t in c for t in ["stop before delet", "stop and delete", "vm_lifecycle", "halt", "must stop", "running"]) and (
            "stop" in c or "halt" in c
        ), (
            "should require stopping VM before deletion"
        )

    def test_orphan_storage(self):
        """Skill: VM-only vs VM+storage; orphan PVCs; delete DataVolume/PVC."""
        c = read_report().lower()
        assert any(t in c for t in ["vm only", "vm+storage", "datavolume", "orphan", "preserve storage", "delete storage", "pvc"]) and (
            "storage" in c or "pvc" in c or "datavolume" in c
        ), (
            "should address storage scope (VM-only vs VM+storage, orphan PVCs)"
        )

    def test_finalizer_handling(self):
        """Skill: Finalizer blocking deletion; stuck Terminating."""
        c = read_report().lower()
        assert any(t in c for t in ["finalizer", "terminating", "stuck", "resources_create_or_update", "remove finalizer"]), (
            "should address finalizer handling for stuck deletion"
        )

    def test_typed_confirmation(self):
        """Skill: Typed VM name confirmation (exact match) before delete."""
        c = read_report().lower()
        assert any(t in c for t in ["type", "typed", "exact name", "confirm", "to confirm"]) and (
            "name" in c or "vm" in c
        ), (
            "should require typed VM name confirmation"
        )

    def test_protected_label(self):
        """Skill: protected: true label blocks deletion."""
        c = read_report().lower()
        assert any(t in c for t in ["protected", "protected label", "metadata.labels", "refuse delet"]), (
            "should address protected label blocking deletion"
        )

    def test_reclaim_policy_retain(self):
        """Docs teach PV reclaim policy Retain blocks PVC deletion; must patch PV
        to Delete first. Without docs, agents don't handle stuck PVC cleanup."""
        c = read_report().lower()
        assert any(t in c for t in [
            "retain", "reclaim", "reclaimpolicy", "reclaim policy",
            "patch pv", "delete policy",
        ]), "should address PV reclaim policy Retain blocking cleanup"
