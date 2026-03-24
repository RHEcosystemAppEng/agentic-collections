"""
Tests for rh-developer__debug-pipeline per-skill evaluation.
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

    def test_mentions_pipeline(self):
        content = read_report().lower()
        assert "pipeline" in content, "report should mention pipeline"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_pipelinerun_taskrun_hierarchy(self):
        """Skill teaches PipelineRun → TaskRun → Step hierarchy to find failure."""
        c = read_report().lower()
        assert any(t in c for t in ["pipelinerun", "pipeline run"]) and any(t in c for t in [
            "taskrun", "task run", "task"
        ]), "should drill PipelineRun→TaskRun hierarchy"

    def test_concrete_remediation(self):
        """Skill teaches distinguishing transient vs config fix needed."""
        c = read_report().lower()
        assert any(t in c for t in ["retry", "rerun", "fix", "remediat", "resolv"]), (
            "should provide remediation guidance"
        )

    def test_taskrun_label_filter(self):
        """Docs teach filtering TaskRuns by parent pipeline using
        tekton.dev/pipelineRun=<name> label. Without docs, agents list all TaskRuns."""
        c = read_report().lower()
        assert "tekton.dev/pipelinerun" in c or ("label" in c and "pipelinerun" in c) or (
            "filter" in c and "taskrun" in c
        ), "should filter TaskRuns by pipelineRun label"
