"""
Tests for rh-developer__containerize-deploy per-skill evaluation.
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

    def test_mentions_containerization(self):
        content = read_report().lower()
        assert any(t in content for t in ["container", "deploy", "image"]), (
            "report should mention containerization or deployment"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_startup_probe(self):
        """Skill docs teach startup probe in addition to liveness/readiness.
        Without skill, agents typically only include liveness and readiness probes."""
        c = read_report()
        assert "startupProbe" in c or "startup probe" in c.lower() or "startupprobe" in c.lower(), (
            "should include startup probe configuration (startupProbe YAML key)"
        )

    def test_multistage_dockerfile_example(self):
        """Skill docs teach multi-stage Dockerfile with COPY --from=builder pattern.
        Without skill, agents mention multi-stage conceptually but don't provide the example."""
        c = read_report()
        assert "COPY --from=" in c or "AS builder" in c or "copy --from=" in c.lower(), (
            "should include a multi-stage Dockerfile example with COPY --from= or AS builder syntax"
        )

    def test_hpa_autoscaling_config(self):
        """Skill docs teach complete HPA configuration with autoscaling API.
        Without skill, agents mention autoscaling conceptually but skip the manifest."""
        c = read_report()
        assert "HorizontalPodAutoscaler" in c or "autoscaling/v2" in c, (
            "should include HorizontalPodAutoscaler manifest or autoscaling/v2 API reference"
        )

    def test_connection_pool_config(self):
        """Skill docs teach application-specific database connection pooling with
        SQLAlchemy settings. Without skill, agents skip pool configuration details."""
        c = read_report()
        assert any(t in c for t in [
            "SQLALCHEMY_POOL", "pool_size", "POOL_SIZE",
            "pool_recycle", "POOL_RECYCLE",
        ]), "should include SQLAlchemy connection pool settings (pool_size, pool_recycle)"

    def test_strategy_comparison(self):
        """Skill teaches comparing at least 2 containerization strategies with trade-offs."""
        c = read_report().lower()
        strategies = ["s2i", "dockerfile", "helm", "podman", "source-to-image"]
        mentioned = sum(1 for s in strategies if s in c)
        assert mentioned >= 2, "should compare at least 2 containerization strategies"

    def test_session_affinity_config(self):
        """Skill docs teach explicit sessionAffinity configuration in Service spec.
        Without skill, agents skip this detail in the Service definition."""
        c = read_report().lower()
        assert "sessionaffinity" in c or "session affinity" in c, (
            "should specify sessionAffinity in Service configuration"
        )

    def test_app_module_s2i_entrypoint(self):
        """Skill teaches APP_MODULE environment variable for S2I Python startup
        (e.g., app:app). Without skill, agents don't know this S2I-specific
        configuration for WSGI entry point discovery."""
        c = read_report()
        assert "APP_MODULE" in c or "app:app" in c or "APP_SCRIPT" in c, (
            "should reference APP_MODULE or app:app S2I entrypoint configuration"
        )

    def test_gunicorn_worker_formula(self):
        """Skill teaches Gunicorn worker count formula: (2 × CPU cores) + 1.
        Without skill, agents hardcode worker count without the sizing formula."""
        c = read_report()
        assert any(t in c for t in [
            "2 * cores", "2 × CPU", "(2 * cores) + 1", "2 × cores",
            "2*cores", "2 * cpu", "2x CPU", "2 x cores",
        ]) or ("worker" in c.lower() and ("formula" in c.lower() or "cores" in c.lower())), (
            "should include Gunicorn worker count formula based on CPU cores"
        )

    def test_sqlalchemy_engine_options(self):
        """Skill teaches SQLALCHEMY_ENGINE_OPTIONS configuration for advanced
        pool tuning. Without skill, agents configure individual pool parameters
        but miss the unified engine options dict."""
        c = read_report()
        assert "SQLALCHEMY_ENGINE_OPTIONS" in c or "engine_options" in c, (
            "should include SQLALCHEMY_ENGINE_OPTIONS for advanced pool configuration"
        )
