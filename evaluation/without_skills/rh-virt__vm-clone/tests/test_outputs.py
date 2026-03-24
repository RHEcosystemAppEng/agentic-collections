"""
Tests for rh-virt__vm-clone per-skill evaluation.
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

    def test_mentions_source_and_target(self):
        content = read_report().lower()
        has_source = any(t in content for t in ["source", "original", "production"])
        has_target = any(t in content for t in ["clone", "target", "copy", "destination"])
        assert has_source and has_target, "report should identify both a source VM and a clone target"


class TestSkillDependent:
    def test_storage_class_cloning(self):
        """Skill: StorageClass/CSI for PVC cloning strategy."""
        c = read_report().lower()
        assert any(t in c for t in ["storageclass", "storage class", "csi", "volume cloning", "pvc clone", "clone support"]), (
            "should mention StorageClass or CSI cloning for clone strategy"
        )

    def test_identity_conflict(self):
        """Skill: hostname, cloud-init, SSH key, firmware UUID conflicts between source and clone."""
        c = read_report().lower()
        assert any(t in c for t in ["hostname", "cloud-init", "cloud init", "ssh key", "firmware", "uuid", "mac address", "identity conflict"]), (
            "should address identity conflicts (hostname, cloud-init, UUID) between source and clone"
        )

    def test_cross_namespace_rbac(self):
        """Skill: RBAC/permissions for cross-namespace cloning."""
        c = read_report().lower()
        assert any(t in c for t in ["rbac", "permission", "cross-namespace", "cross namespace", "target namespace", "create virtualmachine"]), (
            "should address RBAC or permissions for cross-namespace cloning"
        )

    def test_data_volume_cloning(self):
        """Skill: DataVolume with source PVC for clone provisioning."""
        c = read_report().lower()
        assert any(t in c for t in ["datavolume", "data volume", "source.pvc", "source pvc", "pvc datasource", "clone storage"]), (
            "should discuss DataVolume or PVC cloning for clone storage"
        )

    def test_datavolume_progress(self):
        """Skill: Monitor DataVolume phase (Pending/Succeeded) during clone."""
        c = read_report().lower()
        assert any(t in c for t in ["datavolume", "phase", "pending", "succeeded", "cloning progress", "status.phase"]), (
            "should mention monitoring DataVolume phase during clone"
        )

    def test_firmware_uuid_regeneration(self):
        """Skill teaches domain.firmware.uuid and domain.firmware.serial must be
        regenerated in clone spec to avoid identity conflicts. Without skill,
        agents clone without regenerating firmware identifiers."""
        c = read_report().lower()
        assert "firmware" in c and ("uuid" in c or "serial" in c), (
            "should address firmware UUID/serial regeneration for clone"
        )

    def test_run_strategy_halted_for_clone(self):
        """Skill teaches runStrategy: Halted ensures cloned VM starts in Stopped state.
        Without skill, agents start clone immediately."""
        c = read_report().lower()
        assert any(t in c for t in ["halted", "runstrategy", "run strategy"]) and (
            "clone" in c or "stop" in c
        ), "should set runStrategy: Halted for cloned VM"

    def test_source_pvc_bound(self):
        """Docs teach CSI clone prerequisite: source PVC must be in Bound state.
        Without docs, agents attempt cloning from unbound PVCs."""
        c = read_report().lower()
        assert any(t in c for t in [
            "bound", "pvc status", "source pvc", "prerequisite",
        ]) and ("pvc" in c or "storage" in c), (
            "should verify source PVC is Bound before cloning"
        )
