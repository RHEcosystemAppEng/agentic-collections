"""
Tests for rh-ai-engineer__ai-observability per-skill evaluation.
Baseline tests: any competent agent should pass.
Skill-dependent tests: based on empirical gaps between skilled and unskilled agent outputs.
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
        assert any(t in content for t in ["monitor", "metric", "observ", "inference"]), (
            "report should mention monitoring or observability"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_tempo_distributed_tracing(self):
        """Skill teaches Tempo for distributed tracing of inference requests.
        Without skill, agents don't mention Tempo at all."""
        c = read_report().lower()
        assert any(t in c for t in ["tempo", "distributed trac"]), (
            "should recommend Tempo for distributed tracing"
        )

    def test_korrel8r_correlation(self):
        """Skill teaches Korrel8r for cross-domain signal correlation.
        Without skill, agents don't know about Korrel8r."""
        c = read_report().lower()
        assert any(t in c for t in ["korrel8r", "cross-domain correlation"]), (
            "should mention Korrel8r for cross-domain correlation"
        )

    def test_dcgm_gpu_metric_names(self):
        """Skill teaches DCGM-specific GPU metric names (DCGM_FI_DEV_*).
        Without skill, agents use generic nvidia_gpu_memory_* names."""
        c = read_report()
        assert any(t in c for t in ["DCGM_FI_DEV", "dcgm_fi_dev", "DCGM"]), (
            "should reference DCGM GPU metric names (not generic nvidia_gpu_*)"
        )

    def test_opentelemetry_instrumentation(self):
        """Skill teaches OpenTelemetry for trace instrumentation on inference endpoints.
        Without skill, agents don't mention OpenTelemetry."""
        c = read_report().lower()
        assert any(t in c for t in ["opentelemetry", "otel"]), (
            "should recommend OpenTelemetry instrumentation"
        )

    def test_vllm_tuning_args(self):
        """Skill teaches vLLM CLI args for memory management.
        Without skill, agents recommend generic resource increases but not vLLM-specific tuning."""
        c = read_report().lower()
        assert any(t in c for t in [
            "max-model-len", "max_model_len", "gpu-memory-utilization",
            "gpu_memory_utilization", "tensor parallel", "tensor_parallel",
        ]), "should mention vLLM-specific configuration args for resource tuning"

    def test_latency_percentiles(self):
        """Both agents should report latency percentiles (easy test)."""
        c = read_report().lower()
        assert any(t in c for t in ["p50", "p95", "p99"]), (
            "should report latency with percentiles"
        )

    def test_tensor_parallel_size_tuning(self):
        """Docs teach reducing --tensor-parallel-size as GPU scheduling triage step,
        and OOM mitigation via --max-model-len and quantized models (AWQ/GPTQ/FP8).
        Without docs, agents don't know these vLLM tuning parameters."""
        c = read_report().lower()
        assert any(t in c for t in [
            "tensor-parallel-size", "tensor_parallel_size", "tensor parallel",
            "awq", "gptq", "fp8", "quantiz",
        ]), "should address tensor-parallel-size and quantization for GPU tuning"
