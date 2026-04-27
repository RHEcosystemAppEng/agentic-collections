"""
Tests for rh-developer__debug-pod per-skill evaluation.
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

    def test_mentions_pod_or_container(self):
        content = read_report().lower()
        assert "pod" in content or "container" in content, "report should mention pod or container"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_previous_logs_flag(self):
        """Skill teaches using --previous to get logs from crashed container
        when restarts > 0. Without skill, agents only check current logs."""
        c = read_report()
        assert "--previous" in c or "previous" in c.lower(), (
            "should use --previous flag to get logs from crashed container"
        )

    def test_readiness_removes_endpoints(self):
        """Skill teaches that readiness probe failures remove pod from Service
        endpoints, causing traffic loss. Without skill, agents miss this link."""
        c = read_report().lower()
        assert ("readiness" in c and "endpoint" in c) or ("readiness" in c and "service" in c) or (
            "readiness" in c and "traffic" in c
        ), "should explain readiness failures remove Service endpoints"

    def test_exit_137_oomkilled_mapping(self):
        """Skill teaches exit code 137 = OOMKilled, map to memory limit."""
        c = read_report().lower()
        assert ("137" in c or "oom" in c or "oomkill" in c) and any(t in c for t in [
            "memory", "limit", "increase"
        ]), "should map exit 137 to OOMKilled and memory limit"

    def test_concrete_remediation_command(self):
        """Skill teaches oc set resources deployment/... --limits=memory=."""
        c = read_report().lower()
        assert any(t in c for t in ["oc set resources", "oc patch", "memory=", "limits"]) or (
            "```" in read_report() and "oc" in c
        ), "should include concrete oc remediation command"

    def test_resource_analysis(self):
        """Skill teaches analyzing memory request/limit for OOM remediation."""
        c = read_report().lower()
        assert any(t in c for t in ["limit", "request"]) and any(t in c for t in [
            "memory", "resource", "increase"
        ]), "should analyze resource limits for OOM"

    def test_events_correlation(self):
        """Skill teaches checking events for scheduling, OOM, and image pull failures."""
        c = read_report().lower()
        assert "event" in c and any(t in c for t in [
            "oom", "schedule", "pull", "fail", "kill", "backoff"
        ]), "should correlate pod events with failure cause"
