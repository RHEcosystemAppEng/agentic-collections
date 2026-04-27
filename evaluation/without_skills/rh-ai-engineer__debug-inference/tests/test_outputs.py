"""
Tests for rh-ai-engineer__debug-inference per-skill evaluation.
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
        assert any(t in content for t in ["inference", "model", "serving", "deploy"]), (
            "report should mention inference"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_kserve_status_conditions(self):
        """Skill teaches presenting PredictorReady and IngressReady as distinct KServe conditions.
        Without skill, agents report generic pod status (CrashLoopBackOff) without naming these conditions."""
        c = read_report().lower()
        assert any(t in c for t in [
            "predictorready", "predictor ready", "predictor_ready",
            "ingressready", "ingress ready", "ingress_ready",
        ]), "should name KServe status conditions (PredictorReady, IngressReady)"

    def test_kserve_container_name(self):
        """Skill teaches 'kserve-container' as the specific container for log inspection.
        Without skill, agents check logs generically without naming this container."""
        c = read_report().lower()
        assert "kserve-container" in c or "kserve container" in c, (
            "should mention kserve-container by name as the container to inspect"
        )

    def test_label_selector_methodology(self):
        """Skill teaches using serving.kserve.io/inferenceservice label to find predictor pods.
        Without skill, agents discover pods through generic namespace listing."""
        c = read_report().lower()
        assert any(t in c for t in [
            "serving.kserve.io", "kserve.io/inferenceservice",
        ]), "should reference the KServe label selector for predictor pod discovery"

    def test_account_cr_awareness(self):
        """Skill teaches NIM Account CR as the credential management mechanism.
        Without skill, agents manually create docker-registry secrets and
        patch service accounts instead of using the Account custom resource."""
        c = read_report()
        assert any(t in c for t in [
            "Account CR", "kind: Account", "Account resource",
            "Account custom resource",
        ]) or "account cr" in c.lower(), (
            "should reference NIM Account CR as credential management mechanism"
        )

    def test_nim_api_version(self):
        """Skill teaches the nvidia.com API group for NIM Account and ngcSecret
        field for NGC credential binding. Without skill, agents create
        generic secrets without the Account CR pattern."""
        c = read_report().lower()
        assert any(t in c for t in [
            "nvidia.com/v1alpha1", "ngcsecret", "ngc_api_key",
        ]) or ("account" in c and "api" in c and "nvidia" in c), (
            "should reference NIM Account API version or NGC secret binding"
        )

    def test_root_cause_with_remediation(self):
        """Both agents should link diagnosis to fix — easy test."""
        c = read_report().lower()
        has_diagnosis = any(t in c for t in ["oom", "memory", "crash", "fail"])
        has_fix = any(t in c for t in ["fix", "recommend", "solution", "increase", "reduce"])
        assert has_diagnosis and has_fix, "should link diagnosis to recommended fix"

    def test_ngc_pull_secret_expiry(self):
        """Docs teach NGC pull-secret expiry as a common issue, and
        'Insufficient nvidia.com/gpu' as GPU scheduling error signature.
        Without docs, agents miss these specific failure patterns."""
        c = read_report().lower()
        assert any(t in c for t in [
            "ngc", "pull-secret", "pull secret", "expir",
            "insufficient nvidia.com/gpu", "nvidia.com/gpu",
        ]), "should address NGC pull-secret expiry or GPU scheduling errors"
