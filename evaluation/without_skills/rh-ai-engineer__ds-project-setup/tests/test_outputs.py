"""
Tests for rh-ai-engineer__ds-project-setup per-skill evaluation.
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
        assert any(t in content for t in ["project", "data science", "namespace"]), (
            "report should mention the project"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_data_connection_secret_keys(self):
        """Skill teaches RHOAI data connections are stored as K8s Secrets with specific
        key names: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET,
        AWS_S3_ENDPOINT. Without skill, agents describe connections abstractly."""
        c = read_report()
        aws_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET",
                     "AWS_S3_ENDPOINT", "AWS_DEFAULT_REGION"]
        mentioned = sum(1 for k in aws_keys if k in c)
        assert mentioned >= 2, (
            "should reference specific RHOAI data connection secret key names (AWS_*)"
        )

    def test_credential_partial_redaction(self):
        """Skill teaches showing first 4 chars + **** for credentials (e.g., AKIA****).
        Without skill, agents use PLACEHOLDER values or full redaction."""
        c = read_report()
        has_partial = any(t in c for t in [
            "AKIA****", "AKIA*", "wJal****", "wJal*",
            "1234****", "1234*",
        ])
        has_stars_with_prefix = "****" in c and any(t in c for t in ["AKIA", "akia"])
        assert has_partial or has_stars_with_prefix, (
            "should use partial credential redaction (first chars visible + ****)"
        )

    def test_k8s_secret_yaml_manifest(self):
        """Skill teaches showing the K8s Secret manifest structure for data connections.
        Without skill, agents describe connections narratively without YAML."""
        c = read_report()
        has_secret_kind = "kind: Secret" in c or "kind:Secret" in c
        has_secret_ref = "Secret" in c and ("apiVersion" in c or "metadata" in c)
        assert has_secret_kind or has_secret_ref, (
            "should include K8s Secret manifest structure for data connection"
        )

    def test_pipeline_server_with_data_connection(self):
        """Skill teaches pipeline server requires a data connection (prerequisite chain).
        Without skill, agents skip pipeline server or configure it generically."""
        c = read_report().lower()
        has_pipeline = any(t in c for t in ["pipeline server", "pipeline"])
        has_linkage = any(t in c for t in [
            "data connection", "model-store", "artifact storage",
            "s3 bucket", "data_connection",
        ])
        pipeline_configured = "pipeline" in c and "configured" in c and "not configured" not in c
        assert has_pipeline and (has_linkage or pipeline_configured), (
            "should configure pipeline server linked to a data connection"
        )

    def test_base64_secret_values(self):
        """Skill teaches showing actual base64-encoded secret values in K8s
        Secret YAML manifests. Without skill, agents show credentials in
        plain text or fully redacted format."""
        c = read_report()
        import re
        has_base64 = bool(re.search(r'[A-Za-z0-9+/]{12,}={0,2}', c))
        has_opaque = "Opaque" in c
        assert has_base64 or has_opaque, (
            "should include base64-encoded values or Opaque secret type in K8s manifest"
        )

    def test_model_serving_mode(self):
        """Both agents should configure model serving — easy test."""
        c = read_report().lower()
        assert any(t in c for t in [
            "single", "multi", "model serving", "serving mode",
        ]), "should configure model serving mode"

    def test_runtime_selection_context(self):
        """Docs teach decision context across runtimes: vLLM (PagedAttention),
        NIM (TensorRT-LLM, no compilation), Caikit+TGIS (gRPC-only).
        Without docs, agents don't provide runtime comparison context."""
        c = read_report().lower()
        assert any(t in c for t in [
            "pagedattention", "paged attention", "tensorrt", "grpc",
            "caikit", "vllm", "nim",
        ]) and any(t in c for t in ["runtime", "serving", "comparison", "select"]), (
            "should compare runtimes with technical characteristics"
        )
