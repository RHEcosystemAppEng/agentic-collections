"""
Tests for rh-ai-engineer__serving-runtime-config per-skill evaluation.
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

    def test_mentions_topic(self):
        content = read_report().lower()
        assert any(t in content for t in ["servingruntime", "serving runtime", "runtime"]), (
            "report should mention ServingRuntime"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_kserve_container_name(self):
        """Skill teaches the main container MUST be named kserve-container for KServe
        compatibility. Without skill, agents use framework-specific names like 'triton'."""
        c = read_report()
        assert "kserve-container" in c, (
            "should name the main container 'kserve-container' (required by KServe)"
        )

    def test_serving_runtime_api_version(self):
        """Skill teaches ServingRuntime uses serving.kserve.io/v1alpha1 API (alpha,
        not beta like InferenceService). Without skill, agents use v1beta1 or omit
        the apiVersion distinction between ServingRuntime and InferenceService."""
        c = read_report()
        assert "v1alpha1" in c or (
            "alpha" in c.lower() and "serving" in c.lower()
        ), "should use v1alpha1 API version for ServingRuntime"

    def test_autoselect_false_for_secondary(self):
        """Skill teaches using autoSelect: true only for primary format and false for
        secondary formats to avoid conflicts. Without skill, agents set true for all."""
        c = read_report().lower()
        assert "autoselect: false" in c or "autoselect\":false" in c or "autoselect\": false" in c, (
            "should use autoSelect: false for non-primary model formats"
        )

    def test_gpu_at_inferenceservice_level(self):
        """Skill teaches not hardcoding GPU in ServingRuntime; GPU allocation belongs
        at the InferenceService level for flexibility. Without skill, agents hardcode
        nvidia.com/gpu in the runtime spec."""
        c = read_report().lower()
        assert any(t in c for t in [
            "inferenceservice level", "inferenceservice deployment",
            "per inferenceservice", "not specified in the servingruntime",
            "gpu allocation happens at",
        ]), "should explain GPU allocation belongs at InferenceService level, not in the runtime"

    def test_model_format_matching(self):
        """Skill teaches that supportedModelFormats must match InferenceService model
        format for runtime selection."""
        c = read_report().lower()
        assert any(t in c for t in [
            "model format", "supportedmodelformat", "supported model format",
            "inferenceservice", "match",
        ]), "should address model format matching for runtime selection"

    def test_dashboard_label(self):
        """Skill teaches opendatahub.io/dashboard label for dashboard visibility."""
        c = read_report().lower()
        assert any(t in c for t in [
            "opendatahub", "dashboard", "label", "visible",
            "platform", "display",
        ]), "should address dashboard/platform visibility via labels"

    def test_caikit_tgis_grpc(self):
        """Docs teach Caikit+TGIS is gRPC-only (no REST API) and NIM uses
        TensorRT-LLM with pre-compiled engines. Without docs, agents assume REST
        for all runtimes."""
        c = read_report().lower()
        assert any(t in c for t in [
            "grpc", "caikit", "tgis", "tensorrt",
        ]) and ("runtime" in c or "serving" in c), (
            "should note Caikit+TGIS gRPC-only or NIM TensorRT-LLM characteristics"
        )
