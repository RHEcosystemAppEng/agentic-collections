"""
Tests for ocp-admin__cluster-report per-skill evaluation.
Baseline tests: any competent agent should pass.
Skill-dependent tests: based on empirical gaps between skilled and unskilled agent outputs.
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

    def test_mentions_cluster(self):
        content = read_report().lower()
        assert any(t in content for t in ["cluster", "openshift", "node"]), (
            "report should mention cluster"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_clusterversion_resource(self):
        """Skill teaches to probe the ClusterVersion resource to verify OpenShift.
        Without skill, agents say 'vanilla Kubernetes' without mentioning the mechanism."""
        c = read_report().lower()
        assert "clusterversion" in c or "cluster version resource" in c, (
            "should mention ClusterVersion resource as the OpenShift verification method"
        )

    def test_aggregated_cross_cluster_totals(self):
        """Skill teaches a comparison table with aggregated totals across clusters.
        Without skill, agents report each cluster separately without totals."""
        c = read_report().lower()
        has_total_label = "total" in c or "aggregate" in c or "combined" in c
        has_aggregate_context = any(t in c for t in [
            "total node", "total cpu", "total memory", "total gpu",
            "across cluster", "combined resource", "aggregate",
        ]) or (has_total_label and any(t in c for t in ["node", "cpu", "core", "memory", "gi"]))
        assert has_total_label and has_aggregate_context, (
            "should include aggregated cross-cluster totals (total nodes, CPU, memory)"
        )

    def test_non_openshift_exclusion(self):
        """Skill teaches to EXCLUDE non-OpenShift clusters from detailed reporting.
        Without skill, agents include dev-k8s as a full section with nodes/pods/namespaces."""
        c = read_report().lower()
        has_exclusion = any(t in c for t in [
            "excluded", "exclude", "excluded by default", "not included",
            "omitted", "non-openshift",
        ])
        assert has_exclusion and "dev-k8s" in c, (
            "should explicitly exclude non-OpenShift clusters from detailed data"
        )

    def test_unreachable_reporting(self):
        """Both agents should mention unreachable clusters, but skill teaches categorization."""
        c = read_report().lower()
        assert "legacy-dc" in c and any(t in c for t in [
            "unreachable", "connection refused", "offline",
        ]), "should report legacy-dc as unreachable"

    def test_gpu_inventory(self):
        """Skill template includes GPU column — moderate discriminator."""
        c = read_report().lower()
        assert "gpu" in c, "should include GPU information"

    def test_version_numbers(self):
        """Both agents get versions from MCP, but skill ensures all clusters are covered."""
        c = read_report()
        versions = sum(1 for v in ["4.16.3", "4.15.12", "4.16.1"] if v in c)
        assert versions >= 2, "should report exact version numbers for multiple clusters"

    def test_multi_cluster_tooling(self):
        """Docs teach multi-cluster tooling/automation for consistent reporting.
        Without docs, agents rely on manual kubectl context switching."""
        c = read_report().lower()
        assert any(t in c for t in [
            "build-kubeconfig", "kubeconfig.py", "cluster-reporter",
            "multi-cluster", "multiple context", "all contexts",
            "setup script", "automation",
        ]), "should reference multi-cluster tooling or automation approach"

    def test_rbac_for_reporting(self):
        """Docs teach read-only RBAC (ClusterRole/ServiceAccount) for cluster reporting
        instead of admin credentials."""
        c = read_report().lower()
        assert any(t in c for t in [
            "cluster-reporter-readonly", "cluster-reporter-system",
            "readonly", "read-only", "clusterrole",
            "service account", "serviceaccount", "rbac",
            "least privilege", "non-admin",
        ]), "should reference read-only RBAC for cluster reporting"
