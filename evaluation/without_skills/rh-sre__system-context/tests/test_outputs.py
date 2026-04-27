"""
Tests for rh-sre__system-context per-skill evaluation.
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
        assert any(t in content for t in ['system', 'context', 'environment']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_remediation_strategy_by_context(self):
        """Skill: Determine strategy from context: batch vs rolling, maintenance window, pod eviction for K8s."""
        c = read_report().lower()
        has_strategy = any(t in c for t in ["strategy", "approach", "rolling", "batch"])
        has_context = any(t in c for t in ["maintenance", "pod eviction", "kubernetes", "staging first"])
        assert has_strategy and has_context, (
            "should derive strategy from context (skill: Decision Matrix)"
        )

    def test_rhel_version_distribution(self):
        """Skill: Report RHEL version distribution (playbook must support multiple versions)."""
        c = read_report().lower()
        assert any(t in c for t in ['rhel', 'version', 'distribution', 'el7', 'el8', 'el9']), (
            "Should report RHEL version distribution (skill: conditional dnf/yum)"
        )

    def test_environment_and_criticality(self):
        """Skill: Classify by environment (prod/staging/dev) and criticality for rollout order."""
        c = read_report().lower()
        has_env = any(t in c for t in ["staging", "development", "rollout_order", "rollout order"])
        has_crit = any(t in c for t in ["critical", "criticality", "priority", "high", "rollout"])
        assert has_env and has_crit, (
            "should classify by environment and criticality (skill: rollout_order)"
        )

    def test_infrastructure_classification(self):
        """Skill: infrastructure_type (bare_metal/virtualized/container) and infrastructure_vendor (kvm) fields."""
        c = read_report().lower()
        has_type = any(t in c for t in ["infrastructure_type", "infrastructure_vendor", "virtualized"])
        has_bare = "bare_metal" in c or "bare metal" in c
        assert has_type or has_bare, (
            "should reference infrastructure classification (skill: bare_metal/virtualized/container)"
        )

    def test_kubernetes_context_fields(self):
        """Skill: hasPdbs and daemonsets_present for safety planning in K8s context."""
        c = read_report().lower()
        has_k8s = any(t in c for t in ["pdb", "daemonset"])
        has_safety = any(t in c for t in ["safety", "eviction"])
        assert has_k8s and has_safety, (
            "should reference PDB/daemonset for K8s safety (skill)"
        )

    def test_needs_restarting_check(self):
        """Docs teach needs-restarting -r (exit code 0=no reboot, 1=reboot needed)
        and -s for services needing restart. Without docs, agents skip this check."""
        c = read_report().lower()
        assert any(t in c for t in [
            "needs-restarting", "needs_restarting", "reboot", "restart service",
        ]), "should use needs-restarting for reboot/service restart assessment"
