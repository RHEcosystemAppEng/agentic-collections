"""
Tests for rh-developer__debug-network per-skill evaluation.
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

    def test_mentions_network_issue(self):
        content = read_report().lower()
        assert "503" in content or "network" in content or "route" in content, (
            "report should mention the network issue"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_route_admitted_condition(self):
        """Skill teaches Route Admitted condition (from the router) is distinct from
        Route just existing. Without skill, agents only check if Route exists."""
        c = read_report().lower()
        assert "admitted" in c or "route admitted" in c or ("condition" in c and "route" in c), (
            "should check Route Admitted condition (not just Route existence)"
        )

    def test_empty_endpoints_diagnosis(self):
        """Skill teaches checking Endpoints object for empty subsets as the root
        cause of 503 errors. Without skill, agents check pod status but not the
        Endpoints object directly."""
        c = read_report().lower()
        assert ("endpoint" in c and any(t in c for t in [
            "empty", "no endpoint", "none", "no backend", "no subsets",
            "0 endpoint", "missing",
        ])) or "oc get endpoints" in c or "get ep " in c, (
            "should diagnose empty Endpoints as root cause of 503"
        )

    def test_curl_pod_in_cluster_debug(self):
        """Skill teaches using a disposable in-cluster curl pod for debugging
        internal connectivity. Without skill, agents test externally only."""
        c = read_report().lower()
        assert ("curl" in c and "pod" in c) or "debug pod" in c or "run.*curl" in c or (
            "cluster" in c and "curl" in c
        ), "should use in-cluster curl pod for connectivity debugging"

    def test_connectivity_path_tracing(self):
        """Skill teaches tracing Route → Service → Endpoints → Pod path."""
        c = read_report().lower()
        path_terms = ["route", "service", "endpoint", "pod"]
        mentioned = sum(1 for t in path_terms if t in c)
        assert mentioned >= 3, "should trace connectivity path (Route→Service→Endpoints→Pod)"

    def test_selector_label_mismatch(self):
        """Skill teaches 503 often means selector doesn't match pod labels."""
        c = read_report().lower()
        assert any(t in c for t in ["selector", "label", "match", "mismatch"]) and any(t in c for t in [
            "endpoint", "503"
        ]), "should identify selector/label mismatch causing no endpoints"

    def test_oc_patch_fix_command(self):
        """Skill teaches using oc patch or oc edit for Service selector fixes.
        Without skill, agents describe the fix narratively without the actual
        command to apply it."""
        c = read_report().lower()
        assert any(t in c for t in [
            "oc patch", "oc edit", "kubectl patch", "oc label",
        ]) or ("patch" in c and "service" in c), (
            "should include oc patch/edit command for Service selector fix"
        )

    def test_network_policy_awareness(self):
        """Skill teaches checking NetworkPolicy as a potential cause of network
        issues. Without skill, agents focus only on Service/Route without
        considering NetworkPolicy restrictions."""
        c = read_report()
        assert "NetworkPolicy" in c or "network policy" in c.lower() or (
            "networkpolic" in c.lower()
        ), "should check NetworkPolicy as potential network restriction"
