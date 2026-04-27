"""
Tests for rh-ai-engineer__nim-setup per-skill evaluation.
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
        assert "nim" in content, "report should mention NIM"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_opendatahub_nim_api(self):
        """Skill teaches nim.opendatahub.io as the RHOAI API group for NIM Account CR.
        Without skill, agents use upstream nim.nvidia.com API group."""
        c = read_report()
        assert "nim.opendatahub.io" in c, (
            "should use nim.opendatahub.io as the NIM Account CR API group (not nim.nvidia.com)"
        )

    def test_ngc_image_pull_secret_name(self):
        """Skill teaches ngc-image-pull-secret as the specific secret name for nvcr.io.
        Without skill, agents use generic names like nvcr-credentials."""
        c = read_report()
        assert "ngc-image-pull-secret" in c, (
            "should use ngc-image-pull-secret as the image pull secret name"
        )

    def test_dockerconfigjson_secret_type(self):
        """Skill teaches kubernetes.io/dockerconfigjson as the secret type for image pull.
        Without skill, agents use kubectl docker-registry shorthand without explicit type."""
        c = read_report().lower()
        assert "dockerconfigjson" in c, (
            "should specify dockerconfigjson as the image pull secret type"
        )

    def test_gpu_operator_certified_csv(self):
        """Skill teaches checking gpu-operator-certified CSV by name.
        Without skill, agents check generically for gpu-operator."""
        c = read_report().lower()
        assert "gpu-operator-certified" in c, (
            "should verify gpu-operator-certified ClusterServiceVersion by name"
        )

    def test_nfd_operator_reference(self):
        """Skill teaches verifying NFD (Node Feature Discovery) Operator as a prerequisite.
        Without skill, agents skip NFD verification entirely."""
        c = read_report().lower()
        assert "nfd" in c, (
            "should verify NFD (Node Feature Discovery) Operator as a prerequisite"
        )

    def test_stringdata_secret_field(self):
        """Skill teaches using stringData in Secret YAML for NGC API key (no base64 needed).
        Without skill, agents use kubectl --from-literal or data with base64."""
        c = read_report()
        assert "stringData" in c or "stringdata" in c.lower(), (
            "should use stringData field in Secret YAML manifest for API key"
        )

    def test_nvidia_gpu_only(self):
        """Docs emphasize NIM requires NVIDIA GPUs only; fallback to vLLM when
        NVIDIA GPUs unavailable. Without docs, agents don't mention this constraint."""
        c = read_report().lower()
        assert any(t in c for t in [
            "nvidia gpu", "nvidia only", "fallback", "vllm",
        ]) and ("nim" in c or "gpu" in c), (
            "should note NIM requires NVIDIA GPUs with vLLM fallback"
        )
