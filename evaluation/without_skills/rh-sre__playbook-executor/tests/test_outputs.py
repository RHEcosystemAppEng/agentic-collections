"""
Tests for rh-sre__playbook-executor per-skill evaluation.
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
        assert any(t in content for t in ['playbook', 'execut', 'job']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_git_flow_mandatory(self):
        """Skill: When template playbook path differs from generated playbook, Git Flow (commit, push, sync) is MANDATORY before launch."""
        c = read_report().lower()
        has_git = any(t in c for t in ["git", "commit", "push", "sync"])
        has_block = any(t in c for t in ["before launch", "mandatory", "must", "block", "sync complete"])
        assert has_git or has_block, (
            "should require Git Flow when path differs (skill: no override at launch)"
        )

    def test_launch_configuration(self):
        """Skill teaches configuring launch-time prompts for execution flexibility
        (job type, variables, host limiting). Without skill, agents run playbooks
        with hardcoded settings."""
        c = read_report().lower()
        has_launch = any(t in c for t in ["launch", "prompt", "on launch"])
        has_config = any(t in c for t in [
            "variable", "limit", "job type", "configur",
        ])
        assert has_launch and has_config, (
            "should configure launch-time prompts for execution flexibility"
        )

    def test_relaunch_failed_hosts(self):
        """Skill: jobs_relaunch_retrieve with hosts: 'failed' to retry only failed hosts."""
        c = read_report().lower()
        assert any(t in c for t in ["relaunch", "failed hosts", "retry failed"]), (
            "should mention relaunch for failed hosts (skill: jobs_relaunch_retrieve)"
        )

    def test_dry_run_first(self):
        """Skill: Recommend dry-run (check mode) before production execution."""
        c = read_report().lower()
        assert any(t in c for t in ["dry", "check mode", "check_mode", "preview", "before launch"]), (
            "should recommend dry-run first (skill: Phase 3)"
        )

    def test_per_host_results(self):
        """Skill: Report per-host results (succeeded, failed, error details)."""
        c = read_report().lower()
        has_per_host = any(t in c for t in ["per host", "each host", "host result", "stdout", "host summary"])
        has_ansible_outcome = any(t in c for t in ["succeeded", "failed", "unreachable", "skipped", "changed"])
        assert has_per_host or has_ansible_outcome, (
            "should report per-host execution results (skill: host summaries)"
        )

    def test_error_taxonomy(self):
        """Docs teach error taxonomy: connection/permissions/package/service/disk
        failure categories with specific recovery paths.
        Without docs, agents treat all errors generically."""
        c = read_report().lower()
        categories = ["connection", "permission", "package", "service", "disk"]
        mentioned = sum(1 for cat in categories if cat in c)
        assert mentioned >= 2, (
            "should categorize errors by type (connection/permissions/package/service/disk)"
        )
