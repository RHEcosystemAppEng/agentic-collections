"""
Tests for rh-sre__remediation-verifier per-skill evaluation.
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
        assert any(t in content for t in ['verif', 'remediation', 'confirm']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_three_checks(self):
        """Skill: Verify CVE status + package version + service health (defense in depth)."""
        c = read_report().lower()
        has_cve = any(t in c for t in ["cve", "vulnerab", "patched", "affected"])
        has_pkg = any(t in c for t in ["package", "version", "installed", "fixed"])
        has_svc = any(t in c for t in ["service", "running", "health", "enabled"])
        assert (has_cve and has_pkg) or (has_cve and has_svc) or (has_pkg and has_svc), (
            "should perform at least 2 of 3 checks (skill: CVE status, package, service)"
        )

    def test_package_version_comparison(self):
        """Skill: Compare installed package version to expected fixed version (RPM-style)."""
        c = read_report().lower()
        has_compare = any(t in c for t in ["compare", "version", "expected", "installed"])
        has_fixed = any(t in c for t in ["fixed", "updated", "el8", "el9"])
        assert has_compare or has_fixed, (
            "should compare package versions (skill: verify_package_version)"
        )

    def test_inventory_24h_lag(self):
        """Skill: Lightspeed inventory can take up to 24 hours to reflect updated package versions."""
        c = read_report().lower()
        has_24 = "24" in c
        has_timing = any(t in c for t in ["hour", "propagat", "delay"])
        assert has_24 and has_timing, (
            "should note inventory 24h lag (skill: Best Practices)"
        )

    def test_include_system_profile(self):
        """Skill: get_host_details with include_system_profile: true returns installed_packages, enabled_services."""
        c = read_report().lower()
        assert any(t in c for t in ["include_system_profile", "system_profile", "installed_packages"]), (
            "should reference include_system_profile for packages/services (skill)"
        )

    def test_insights_client_resync(self):
        """Skill: insights-client --check-results triggers inventory re-sync."""
        c = read_report().lower()
        assert any(t in c for t in ["insights-client", "check-results"]), (
            "should mention insights-client for inventory resync (skill)"
        )
