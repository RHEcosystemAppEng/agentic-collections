"""
Tests for rh-virt__vm-snapshot-create per-skill evaluation.
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

    def test_mentions_vm(self):
        content = read_report().lower()
        assert any(t in content for t in ["vm", "virtual machine", "virtualmachine"]), (
            "report should reference the target VM"
        )


class TestSkillDependent:
    def test_volume_snapshot_class(self):
        """Skill: VolumeSnapshotClass prerequisite for CSI snapshot support."""
        c = read_report().lower()
        assert any(t in c for t in ["volumesnapshotclass", "volume snapshot class", "snapshot class", "csi driver"]), (
            "should mention VolumeSnapshotClass for snapshot prerequisites"
        )

    def test_quiesce_consistency(self):
        """Skill: Quiesce/freeze for application-consistent snapshots; guest agent."""
        c = read_report().lower()
        assert any(t in c for t in ["quiesce", "freeze", "thaw", "guest agent", "application-consistent", "qemu-guest-agent"]), (
            "should discuss quiesce/freeze for consistency"
        )

    def test_snapshot_cr_structure(self):
        """Skill: VirtualMachineSnapshot CR with spec.source."""
        c = read_report().lower()
        assert "virtualmachinesnapshot" in c and any(t in c for t in ["spec", "source", "snapshot.kubevirt", "apiversion"]), (
            "should define VirtualMachineSnapshot resource structure"
        )

    def test_hot_plugged_blocker(self):
        """Skill: Hot-plugged volumes block snapshot creation."""
        c = read_report().lower()
        assert any(t in c for t in ["hot-plug", "hotplug", "hot plug", "block snapshot", "cannot snapshot"]), (
            "should address hot-plugged volumes blocking snapshots"
        )

    def test_status_indications(self):
        """Skill: status.indications (GuestAgent, Online) for consistency level."""
        c = read_report().lower()
        assert any(t in c for t in ["indications", "guestagent", "online", "status.phase", "inprogress", "succeeded"]), (
            "should reference snapshot status/indications"
        )

    def test_guest_agent_connected_check(self):
        """Docs teach checking AgentConnected condition to determine if
        application-consistent (vs crash-consistent) snapshots are possible.
        Without docs, agents don't check guest agent status before snapshot."""
        c = read_report().lower()
        assert any(t in c for t in [
            "agentconnected", "agent connected", "guest agent",
            "application-consistent", "crash-consistent",
        ]), "should check AgentConnected for snapshot consistency level"
