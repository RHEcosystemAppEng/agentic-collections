"""
Tests for rh-developer__debug-container per-skill evaluation.
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

    def test_mentions_container(self):
        content = read_report().lower()
        assert "container" in content, "report should mention container"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_nonroot_user(self):
        """Skill teaches running containers as non-root user (--user 1001).
        Without skill, agents omit the --user flag in fix commands."""
        c = read_report()
        assert "--user" in c or "user 1001" in c.lower(), (
            "should include --user flag for non-root container execution"
        )

    def test_image_variant_strategy(self):
        """Skill teaches separate image tags/variants (--build-arg VARIANT=) for
        different container roles. Without skill, agents use same image for all roles."""
        c = read_report()
        assert "--build-arg" in c or "VARIANT=" in c or "separate image" in c.lower(), (
            "should recommend separate image variants for different roles (web vs worker)"
        )

    def test_oomkilled_state_inspection(self):
        """Skill teaches verifying OOMKilled state via container inspect.
        Without skill, agents infer OOM from exit code only without inspecting state."""
        c = read_report()
        assert any(t in c for t in [
            ".State.OOMKilled", "OOMKilled", "oomkilled",
            "State.OOMKilled", "OOMKilled=true", "oomkilled=true",
        ]) and any(t in c for t in [
            "inspect", "Inspect", "state", "State",
        ]), "should inspect container state to verify OOMKilled"

    def test_cleanup_before_rerun(self):
        """Skill teaches proper cleanup (stop + rm with error suppression) before
        rerunning a failed container. Without skill, agents skip cleanup."""
        c = read_report()
        assert "2>/dev/null" in c or ("podman stop" in c and "podman rm" in c) or (
            "podman rm" in c.lower() and "podman run" in c.lower()
        ), "should include container cleanup before rerunning (stop/rm pattern)"

    def test_exit_code_137_oom_mapping(self):
        """Skill teaches exit code 137 = OOMKilled, recommend memory increase."""
        c = read_report().lower()
        assert ("137" in c or "oom" in c) and "memory" in c, (
            "should map exit 137 to OOM and address memory"
        )

    def test_memory_swap_configuration(self):
        """Skill teaches --memory-swap flag for Podman to control total memory
        (RAM + swap). Without skill, agents only adjust --memory without swap."""
        c = read_report().lower()
        assert "memory-swap" in c or "swap" in c or "memory+swap" in c, (
            "should address memory-swap configuration for container memory limits"
        )

    def test_separate_worker_image(self):
        """Skill teaches creating separate container images for different roles
        (web vs worker) rather than running all roles from a single image.
        Without skill, agents patch the existing single image."""
        c = read_report().lower()
        assert any(t in c for t in [
            "separate image", "worker image", "dockerfile.worker",
            "dedicated image", "purpose-built", "role-specific",
        ]) or ("web" in c and "worker" in c and "image" in c), (
            "should recommend separate images for different container roles"
        )
