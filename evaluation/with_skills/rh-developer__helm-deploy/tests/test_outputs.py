"""
Tests for rh-developer__helm-deploy per-skill evaluation.
Baseline tests: report structure.
Skill-dependent tests: OpenShift-Helm integration (not generic Helm knowledge).
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

    def test_mentions_helm(self):
        content = read_report().lower()
        assert "helm" in content, "report should mention Helm"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 100, "report should have substantial content"


class TestSkillDependent:
    def test_values_customization(self):
        """Customizing values before deployment."""
        c = read_report().lower()
        assert any(t in c for t in ["values", "override", "set", "customize"]) and any(t in c for t in [
            "install", "upgrade", "deploy"
        ]), "should address values customization"

    def test_openshift_considerations(self):
        """OpenShift-specific Helm considerations (Route, SCC)."""
        c = read_report().lower()
        assert any(t in c for t in ["openshift", "route", "scc", "security"]), (
            "should address OpenShift-specific Helm concerns"
        )

    def test_buildconfig_integration(self):
        """OpenShift BuildConfig integration in Helm charts for S2I builds.
        Without skill, agents use static image references."""
        c = read_report()
        assert "BuildConfig" in c or "buildconfig" in c.lower() or "build.openshift.io" in c, (
            "should address OpenShift BuildConfig integration in Helm deployment"
        )

    def test_s2i_in_helm_chart(self):
        """OpenShift S2I build integration as part of the Helm chart,
        so the chart manages both the build and deploy lifecycle."""
        c = read_report().lower()
        assert ("s2i" in c or "source-to-image" in c or "source to image" in c) and (
            "helm" in c or "chart" in c or "template" in c
        ), "should integrate S2I builds within the Helm chart structure"
