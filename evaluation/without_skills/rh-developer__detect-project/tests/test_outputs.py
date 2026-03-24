"""
Tests for rh-developer__detect-project per-skill evaluation.
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

    def test_mentions_project_or_language(self):
        content = read_report().lower()
        assert any(t in content for t in ["project", "language", "framework", "detect"]), (
            "report should mention project detection"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 100, "report should have substantial content"


class TestSkillDependent:
    def test_s2i_deployment_recommendation(self):
        """Skill teaches S2I as preferred deployment for OpenShift."""
        c = read_report().lower()
        assert "s2i" in c or "source-to-image" in c or "source to image" in c, (
            "should recommend S2I as deployment strategy for OpenShift"
        )

    def test_app_module_format(self):
        """Skill teaches APP_MODULE format 'module:callable' (e.g., app:app) for
        S2I Python. Without skill, agents don't know this configuration."""
        c = read_report().lower()
        assert "app_module" in c and any(t in c for t in [
            "app:app", "module:", ":app", "module:callable", "wsgi",
        ]), "should specify APP_MODULE format (e.g., app:app) for S2I Python"

    def test_gunicorn_s2i_link(self):
        """Skill teaches gunicorn is required IN requirements.txt for the S2I
        Python builder to use APP_MODULE. Without skill, agents mention gunicorn
        generically without connecting it to S2I builder requirements."""
        c = read_report().lower()
        assert "gunicorn" in c and ("s2i" in c or "app_module" in c or "builder" in c), (
            "should connect gunicorn to S2I/APP_MODULE (not just as a generic server)"
        )

    def test_ubi_base_image_recommendation(self):
        """Skill teaches UBI as the base image for OpenShift."""
        c = read_report().lower()
        assert "ubi" in c or "universal base image" in c, (
            "should recommend UBI base image for OpenShift deployment"
        )

    def test_s2i_entry_point_detection(self):
        """Skill teaches the S2I Python entry point detection order
        (app.sh → application.py → app.py). Without skill, agents don't
        describe the builder's startup sequence."""
        c = read_report().lower()
        has_sequence = "app.sh" in c
        has_default_entry = ("default" in c or "entry point" in c) and "app.py" in c
        has_startup = any(t in c for t in [
            "startup logic", "startup sequence", "s2i startup",
            "entry point detection", "entry point order",
        ])
        assert has_sequence or has_default_entry or has_startup, (
            "should describe S2I Python entry point detection (app.sh/app.py sequence)"
        )
