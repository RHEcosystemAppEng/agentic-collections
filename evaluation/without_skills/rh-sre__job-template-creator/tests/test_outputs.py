"""
Tests for rh-sre__job-template-creator per-skill evaluation.
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
        assert any(t in content for t in ['job template', 'template', 'ansible']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_git_before_template(self):
        """Skill: Playbook must be in Git repo before template creation; AAP syncs from project."""
        c = read_report().lower()
        has_git = any(t in c for t in ["git", "commit", "push", "repository", "sync"])
        has_project = any(t in c for t in ["project", "scm", "sync"])
        assert has_git or has_project, (
            "should add playbook to Git before template (skill: Phase 1)"
        )

    def test_manual_creation_required(self):
        """Skill teaches template creation requires manual steps (e.g., Web UI)
        because the automation API is read-only for templates."""
        c = read_report().lower()
        assert any(t in c for t in [
            "web ui", "manual", "read-only", "cannot create",
            "no create", "gui", "interface",
        ]), "should acknowledge template creation requires manual steps"

    def test_playbook_path_convention(self):
        """Skill teaches following a consistent directory structure or location
        convention for remediation playbooks."""
        c = read_report().lower()
        assert any(t in c for t in [
            "playbook path", "remediation playbook", "playbook location",
            "playbook directory", "playbook structure",
        ]), "should follow a playbook path convention for remediation"

    def test_privilege_escalation_required(self):
        """Skill: become_enabled required for remediation (package updates)."""
        c = read_report().lower()
        assert any(t in c for t in ["privilege", "become", "sudo", "escalat", "root"]), (
            "should require privilege escalation (skill: required for package updates)"
        )

    def test_launch_prompts(self):
        """Skill: Prompt on Launch for Job Type, Variables, Limit."""
        c = read_report().lower()
        assert any(t in c for t in ["launch", "prompt", "variable", "limit", "job type"]), (
            "should configure prompt on launch (skill: Phase 4)"
        )

    def test_configurable_variables(self):
        """Docs teach configuring variables for CVE targeting, remediation mode,
        and post-remediation verification. Without docs, agents skip variable design."""
        c = read_report().lower()
        concepts = sum(1 for t in [
            "target_cve", "cve", "remediation_mode", "mode",
            "verify_after", "verification", "extra_var", "extra var",
            "variable", "parameter",
        ] if t in c)
        assert concepts >= 3, (
            "should define configurable variables for CVE targeting, "
            "remediation mode, and verification"
        )

    def test_version_control_sync(self):
        """Skill teaches AAP projects sync playbooks from version control.
        Without skill, agents describe playbook management without
        version-control-backed project sync."""
        c = read_report().lower()
        assert any(t in c for t in [
            "scm", "source control", "version control",
            "repository sync", "git-backed", "git sync",
        ]), "should reference version control sync for AAP project playbooks"
