"""
Tests for rh-developer__validate-environment per-skill evaluation.
Baseline tests: report structure.
Skill-dependent tests: methodology checks that require skill knowledge.
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

    def test_mentions_environment(self):
        content = read_report().lower()
        assert any(t in content for t in ["environment", "cluster", "ready", "validation"]), (
            "report should mention environment validation"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 100, "report should have substantial content"


class TestSkillDependent:
    def test_skopeo_as_required_tool(self):
        """Skill teaches skopeo is a required dependency for image recommendation flows.
        Without skill, agents skip skopeo in environment validation."""
        c = read_report().lower()
        assert "skopeo" in c, (
            "should validate skopeo as a required tool"
        )

    def test_oc_auth_can_i_checks(self):
        """Skill teaches oc auth can-i create deployments/buildconfigs/imagestreams
        for permission checks. Without skill, agents only check oc whoami."""
        c = read_report().lower()
        has_permission_method = ("auth can-i" in c or "can-i" in c or "permission" in c)
        has_resource_type = any(t in c for t in [
            "deployment", "buildconfig", "imagestream", "create"
        ])
        assert has_permission_method and has_resource_type, (
            "should verify create permissions for deployments/buildconfigs/imagestreams"
        )

    def test_tool_version_checks(self):
        """Skill teaches checking version/availability of oc, helm, podman, git."""
        c = read_report().lower()
        tools = ["oc", "helm", "podman", "git", "skopeo"]
        mentioned = sum(1 for t in tools if t in c)
        assert mentioned >= 3, "should validate multiple CLI tools"

    def test_structured_pass_fail(self):
        """Skill teaches presenting results as pass/fail per check."""
        c = read_report().lower()
        assert any(t in c for t in ["pass", "fail", "missing", "go", "no-go", "available"]) and any(t in c for t in [
            "tool", "check", "oc", "helm", "result"
        ]), "should provide structured pass/fail validation report"
