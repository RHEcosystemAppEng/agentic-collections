"""
Tests for rh-developer__debug-build per-skill evaluation.
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

    def test_mentions_build(self):
        content = read_report().lower()
        assert "build" in content, "report should mention builds"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_s2i_custom_assemble_script(self):
        """Skill teaches creating .s2i/bin/assemble to extend the S2I build process.
        Without skill, agents recommend Dockerfile or custom builder image instead."""
        c = read_report()
        assert ".s2i/bin/assemble" in c or ".s2i/bin" in c, (
            "should mention .s2i/bin/assemble as a way to customize the S2I build"
        )

    def test_default_assemble_path(self):
        """Skill teaches invoking the default S2I assemble script at /usr/libexec/s2i/assemble.
        Without skill, agents don't know the default script path."""
        c = read_report()
        assert "/usr/libexec/s2i/" in c or "libexec/s2i" in c, (
            "should reference the default S2I assemble script at /usr/libexec/s2i/"
        )

    def test_package_manager_awareness(self):
        """Report should mention package installation approach for the builder image."""
        c = read_report().lower()
        assert any(t in c for t in ["microdnf", "dnf", "yum", "package manager", "install package"]), (
            "should mention package installation approach for the builder image"
        )

    def test_s2i_phase_breakdown(self):
        """Skill teaches S2I phases (fetch, pull, assemble, commit, push)."""
        c = read_report().lower()
        phases = ["assemble", "fetch", "pull", "push", "commit"]
        mentioned = sum(1 for p in phases if p in c)
        assert mentioned >= 2, (
            "should identify S2I build phases (skill teaches phase-by-phase diagnosis)"
        )

    def test_concrete_remediation_command(self):
        """Skill teaches providing concrete oc/command remediation."""
        c = read_report().lower()
        assert any(t in c for t in ["oc ", "oc start-build", "oc create", "oc import", "retry"]) or (
            "```" in read_report() and ("oc" in c or "bash" in c)
        ), "should include concrete remediation commands"

    def test_dependency_fix_suggestion(self):
        """Report should suggest concrete dependency fixes for the failing build."""
        c = read_report().lower()
        assert any(t in c for t in [
            "psycopg", "pip install", "requirements", "dependency", "package"
        ]), "should suggest concrete dependency fixes for the failing build"
