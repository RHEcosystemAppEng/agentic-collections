"""
Tests for rh-virt__vm-create per-skill evaluation.
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

    def test_mentions_namespace(self):
        content = read_report().lower()
        assert "namespace" in content, "report should mention the target namespace"


class TestSkillDependent:
    def test_data_volume_provisioning(self):
        """Skill: DataVolume for disk provisioning with image/blank source."""
        c = read_report().lower()
        assert any(t in c for t in ["datavolume", "data volume", "cdi.kubevirt.io", "source.registry", "source.blank"]), (
            "should discuss DataVolume for disk provisioning"
        )

    def test_storage_class_provisioning(self):
        """Skill: StorageClass for DataVolume/PVC provisioning."""
        c = read_report().lower()
        assert any(t in c for t in ["storageclass", "storage class", "volumeBindingMode", "provisioner"]) and (
            "storage" in c or "pvc" in c or "datavolume" in c
        ), (
            "should mention StorageClass for disk provisioning"
        )

    def test_instance_type_or_workload(self):
        """Skill: Instance type (u1.medium) or workload (fedora, rhel) resolution."""
        c = read_report().lower()
        assert any(t in c for t in ["instancetype", "instance type", "u1.", "u1.medium", "workload", "fedora", "rhel", "ubuntu", "centos"]), (
            "should reference instance types or workload/OS selection"
        )

    def test_unschedulable_toleration(self):
        """Skill: ErrorUnschedulable and toleration workaround."""
        c = read_report().lower()
        assert any(t in c for t in ["errorunschedulable", "unschedulable", "taint", "toleration", "scheduling"]) and (
            "taint" in c or "toleration" in c or "unschedulable" in c
        ), (
            "should address ErrorUnschedulable and taint/toleration handling"
        )

    def test_yaml_or_manifest(self):
        """Should include a YAML manifest or structured spec."""
        content = read_report()
        assert "apiVersion" in content or "kind:" in content or "spec:" in content or "```yaml" in content or "```yml" in content, (
            "should include a YAML manifest or structured specification"
        )
