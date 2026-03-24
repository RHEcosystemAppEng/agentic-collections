"""
Tests for rh-developer__deploy per-skill evaluation.
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

    def test_mentions_deploy(self):
        content = read_report().lower()
        assert "deploy" in content, "report should mention deployment"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_insecure_redirect_policy(self):
        """Skill teaches insecureEdgeTerminationPolicy: Redirect on Route to force
        HTTP→HTTPS. Without skill, agents create Routes without redirect policy,
        leaving HTTP access open."""
        c = read_report()
        assert "insecureEdgeTerminationPolicy" in c or (
            "Redirect" in c and ("http" in c.lower() and "https" in c.lower())
        ), "should configure insecureEdgeTerminationPolicy: Redirect on Route"

    def test_framework_port_detection(self):
        """Skill teaches port inference by framework defaults (Node 3000/8080,
        Python 5000/8000, Java 8080). Without skill, agents hardcode 8080."""
        c = read_report().lower()
        assert any(t in c for t in ["port", "8080", "3000", "5000"]) and any(t in c for t in [
            "detect", "expose", "listen", "framework", "default", "infer"
        ]), "should address port detection from framework defaults"

    def test_deployment_service_route_triad(self):
        """Skill teaches creating Deployment, Service, Route in sequence."""
        c = read_report().lower()
        assert any(t in c for t in ["deployment"]) and "service" in c and any(t in c for t in [
            "route", "external", "https"
        ]), "should define Deployment + Service + Route"

    def test_selector_alignment(self):
        """Skill teaches Service selector must match Deployment pod labels."""
        c = read_report().lower()
        assert any(t in c for t in ["selector", "label", "targetport", "target port"]) or (
            "service" in c and "port" in c and "match" in c
        ), "should address selector/port alignment"

    def test_tls_route_config(self):
        """Skill teaches Route with TLS termination (edge/passthrough)."""
        c = read_report().lower()
        assert any(t in c for t in ["tls", "https", "edge", "termination"]), (
            "should address Route TLS for external access"
        )

    def test_hpa_autoscaling(self):
        """Skill teaches including HorizontalPodAutoscaler configuration for
        production deployments. Without skill, agents set static replica count
        without autoscaling."""
        c = read_report()
        assert "HorizontalPodAutoscaler" in c or "autoscaling/v2" in c or (
            "hpa" in c.lower() and "autoscal" in c.lower()
        ), "should include HorizontalPodAutoscaler for production scaling"

    def test_hsts_security_headers(self):
        """Skill teaches HSTS headers or Strict-Transport-Security configuration
        on OpenShift Routes. Without skill, agents skip transport security headers."""
        c = read_report()
        assert any(t in c for t in [
            "HSTS", "Strict-Transport-Security", "hsts",
            "haproxy.router.openshift.io",
        ]), "should configure HSTS or transport security headers on Route"
