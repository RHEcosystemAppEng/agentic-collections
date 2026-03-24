"""
Tests for rh-virt__vm-rebalance per-skill evaluation.
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

    def test_mentions_migration(self):
        content = read_report().lower()
        assert "migrat" in content, "report should discuss migration"

    def test_mentions_node(self):
        content = read_report().lower()
        assert any(t in content for t in ["node", "overload", "imbalance", "utilization"]), (
            "report should reference cluster nodes or load imbalance"
        )


class TestSkillDependent:
    def test_cpu_compatibility(self):
        """Skill: CPU model/feature compatibility between source and target nodes."""
        c = read_report().lower()
        assert any(t in c for t in ["cpu model", "cpu compatible", "cpu feature", "cpu architecture", "migration compatibility"]) or (
            "cpu" in c and ("compatib" in c or "model" in c)
        ), (
            "should address CPU compatibility for migration"
        )

    def test_virtualmachineinstancemigration(self):
        """Skill: VirtualMachineInstanceMigration for live migration."""
        c = read_report().lower()
        assert any(t in c for t in ["virtualmachineinstancemigration", "vmi migration", "migration cr", "migration resource"]), (
            "should reference VirtualMachineInstanceMigration API"
        )

    def test_overcommit_warning(self):
        """Skill: Overcommit detection; warn if node exceeds 100% after rebalance."""
        c = read_report().lower()
        assert any(t in c for t in ["overcommit", "over commit", "exceed 100", "capacity"]) and (
            "overcommit" in c or "100" in c or "exceed" in c
        ), (
            "should address overcommit risk when rebalancing"
        )
