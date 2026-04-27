"""
Tests for rh-virt__vm-inventory per-skill evaluation.
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

    def test_has_structured_data(self):
        content = read_report()
        has_table = "|" in content and content.count("|") >= 4
        has_list = content.count("- ") >= 5
        assert has_table or has_list, "report should present VM inventory in a structured format (table or list)"

    def test_mentions_namespace(self):
        content = read_report().lower()
        assert "namespace" in content, "report should organize by namespace"


class TestSkillDependent:
    def test_vmi_runtime_data(self):
        """Skill: Query VirtualMachineInstance (VMI) for running VM runtime data."""
        c = read_report().lower()
        assert any(t in c for t in ["virtualmachineinstance", "vmi", "virtual machine instance"]), (
            "should reference VMI for runtime data, not just VirtualMachine"
        )

    def test_resource_format(self):
        """Skill: Resources as 'X vCPU, YGi' format, not instance type names like u1.medium."""
        c = read_report().lower()
        assert any(t in c for t in ["vcpu", "vcpus"]) and any(t in c for t in ["gi", "gib"]), (
            "should use vCPU/Gi resource format, not instance type names"
        )

    def test_status_based_grouping(self):
        """Skill: Sort by namespace, then status (Running > Pending > Stopped > Failed), then name."""
        c = read_report().lower()
        status_terms = sum(1 for t in ["running", "stopped", "pending", "failed"] if t in c)
        has_organization = any(t in c for t in [
            "group", "sort", "order", "organiz", "by namespace",
            "by status", "running first", "namespace",
        ])
        assert status_terms >= 2 and has_organization, (
            "should organize VMs with status awareness (Running/Stopped/etc) by namespace"
        )

    def test_conditions_awareness(self):
        """Skill: KubeVirt-specific conditions — AgentConnected, LiveMigratable."""
        c = read_report().lower()
        assert any(t in c for t in [
            "agentconnected", "agent connected", "agent_connected",
            "livemigratable", "live migratable", "live_migratable",
            "guest agent",
        ]), "should mention KubeVirt-specific conditions (AgentConnected, LiveMigratable)"
