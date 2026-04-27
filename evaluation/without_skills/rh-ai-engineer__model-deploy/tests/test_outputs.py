"""
Tests for rh-ai-engineer__model-deploy per-skill evaluation.
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
        assert any(t in content for t in ["model", "deploy", "inference", "serving"]), (
            "report should mention model deployment"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_vram_budget_analysis(self):
        """Skill teaches GPU VRAM budget: model weights (13.5 GiB) + KV cache (28.5 GiB)
        exceeds A10G capacity (24 GB). Without skill, agents report OOM with approximate
        numbers (~14GB) without KV cache sizing or available VRAM calculation."""
        c = read_report()
        assert any(t in c for t in [
            "28.5", "10.1 GiB", "10.1 GB", "24576",
        ]), (
            "should include specific VRAM budget numbers "
            "(KV cache size ~28.5 GiB, available VRAM ~10.1 GiB, or total GPU VRAM 24576 MiB)"
        )

    def test_default_context_window_32768(self):
        """Skill teaches that vLLM default max_model_len=32768 causes KV cache to exhaust
        GPU VRAM on A10G. Without skill, agents report OOM without identifying the specific
        default value that triggers the oversized KV cache allocation."""
        c = read_report()
        assert "32768" in c or "32,768" in c, (
            "should identify max_model_len=32768 as the specific vLLM default causing GPU OOM"
        )

    def test_kserve_yaml_apiversion(self):
        """Skill teaches creating InferenceService YAML with serving.kserve.io/v1beta1.
        Without skill, agents describe fixes via MCP tool calls or narrative without
        providing a formal KServe YAML manifest with the correct apiVersion."""
        c = read_report()
        assert "serving.kserve.io/v1beta1" in c, (
            "should include InferenceService YAML manifest with serving.kserve.io/v1beta1 apiVersion"
        )

    def test_raw_deployment_mode(self):
        """Skill teaches using serving.kserve.io/deploymentMode: RawDeployment annotation
        for RHOAI model deployments. Without skill, agents omit this RHOAI-specific
        annotation, which controls how KServe deploys the predictor."""
        c = read_report()
        assert "RawDeployment" in c or "deploymentMode" in c, (
            "should include RawDeployment annotation (RHOAI deployment mode)"
        )

    def test_known_model_profile(self):
        """Docs teach known model profiles: e.g., Llama 3.1 8B needs 1 GPU with 16GB VRAM,
        --max-model-len=4096; 70B needs 4xA100 80GB with --tensor-parallel-size=4.
        Without docs, agents can't size GPU allocation per model."""
        c = read_report().lower()
        assert any(t in c for t in [
            "max-model-len", "max_model_len", "tensor-parallel-size",
            "tensor_parallel_size", "16gb", "a100", "a10g",
        ]) or ("gpu" in c and ("vram" in c or "model" in c and "profile" in c)), (
            "should reference known model GPU profiles for deployment sizing"
        )

    def test_nim_account_cr(self):
        """Skill teaches that NIM deployments require a NIMAccount CR to be ready
        before the ServingRuntime can pull images. Without skill, agents diagnose
        ImagePullBackOff generically without identifying the NIMAccount dependency."""
        c = read_report()
        assert any(t in c for t in [
            "NIMAccount", "NimAccount", "nim-account", "NIM Account",
            "NIMAccountNotReady",
        ]), "should identify NIMAccount CR as prerequisite for NIM deployment"
