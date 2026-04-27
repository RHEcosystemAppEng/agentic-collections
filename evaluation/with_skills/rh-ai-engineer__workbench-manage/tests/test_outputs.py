"""
Tests for rh-ai-engineer__workbench-manage per-skill evaluation.
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
        assert any(t in content for t in ["workbench", "notebook"]), (
            "report should mention workbench or notebook"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 200, "report should have substantial content"


class TestSkillDependent:
    def test_stop_preserves_data(self):
        """Skill teaches: stopping a workbench preserves PVC data; only delete removes it."""
        c = read_report().lower()
        assert any(t in c for t in [
            "stop", "preserve", "data", "pvc", "storage",
            "stopped", "restart", "start again",
        ]), "should explain that stop preserves data vs delete"

    def test_delete_pvc_warning(self):
        """Skill teaches: deleting workbench requires separate confirmation for PVC; warn about permanent data loss."""
        c = read_report().lower()
        assert any(t in c for t in [
            "pvc", "delete", "data loss", "permanent", "warning",
            "volume", "storage", "backup", "cannot be undone",
        ]), "should warn about PVC/data loss on deletion"

    def test_lifecycle_operations(self):
        """Skill teaches: create, start, stop, delete with distinct implications."""
        c = read_report().lower()
        ops = sum(1 for t in ["start", "stop", "delet", "creat"] if t in c)
        assert ops >= 2, "should describe lifecycle operations (create, start, stop, delete)"

    def test_list_notebook_images_tool(self):
        """Skill teaches: list_notebook_images MCP tool to discover available notebook images."""
        c = read_report().lower()
        assert any(t in c for t in ["list_notebook_images", "notebook images", "available images"]), (
            "should reference list_notebook_images tool (skill)"
        )

    def test_gpu_tuning_awareness(self):
        """Docs teach GPU scheduling triage and OOM mitigation using
        model/context-size controls for workbenches with GPU resources.
        Without docs, agents don't address GPU resource tuning."""
        c = read_report().lower()
        assert any(t in c for t in [
            "gpu", "oom", "context size", "max-model-len", "memory",
        ]) and any(t in c for t in ["workbench", "notebook", "resource", "gpu"]), (
            "should address GPU/OOM tuning for workbench resources"
        )
