"""
Tests for rh-developer__s2i-build per-skill evaluation.
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

    def test_mentions_s2i(self):
        content = read_report().lower()
        assert "s2i" in content or "source-to-image" in content, (
            "report should mention S2I"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_app_module_format(self):
        """Skill teaches APP_MODULE env var format module:app (e.g. main:app) for
        non-default Python entry points. Without skill, agents don't know this format."""
        c = read_report()
        assert "APP_MODULE" in c or "app_module" in c.lower(), (
            "should reference APP_MODULE env var for Python S2I entry point"
        )

    def test_module_colon_app_syntax(self):
        """Skill teaches the module:app syntax (e.g., main:app, wsgi:application).
        Without skill, agents don't know the colon-separated format."""
        c = read_report()
        assert any(t in c for t in ["main:app", "wsgi:app", "module:app", ":app", ":application"]) or (
            "APP_MODULE" in c and ":" in c
        ), "should show module:app format for APP_MODULE"

    def test_s2i_build_phases(self):
        """Skill teaches S2I build phases: assemble (install deps, compile) and
        run (start app). Without skill, agents treat S2I as a black box."""
        c = read_report().lower()
        assert ("assemble" in c and ("run" in c or "start" in c)) or (
            "build phase" in c or "build step" in c or "build process" in c
        ), "should explain S2I build phases (assemble and run)"

    def test_buildconfig_imagestream(self):
        """Skill teaches creating ImageStream + BuildConfig with source/builder/output."""
        c = read_report().lower()
        assert any(t in c for t in ["buildconfig", "imagestream", "build config"]) and any(t in c for t in [
            "source", "builder", "output"
        ]), "should define BuildConfig/ImageStream"

    def test_gunicorn_requirement(self):
        """Skill teaches gunicorn must be in requirements.txt for APP_MODULE."""
        c = read_report().lower()
        assert "gunicorn" in c and any(t in c for t in [
            "requirements", "pip", "install", "wsgi", "app_module"
        ]), "should address gunicorn requirement for S2I Python"

    def test_standalone_imagestream_yaml(self):
        """Skill teaches creating ImageStream as a separate resource with
        image.openshift.io/v1 API group and lookupPolicy. Without skill,
        agents reference ImageStreamTag in BuildConfig but don't define
        the ImageStream resource itself."""
        c = read_report()
        has_is_api = "image.openshift.io" in c
        has_lookup = "lookupPolicy" in c
        assert has_is_api or has_lookup, (
            "should define ImageStream resource with image.openshift.io API"
        )

