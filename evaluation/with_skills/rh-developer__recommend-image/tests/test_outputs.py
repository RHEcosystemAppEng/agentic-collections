"""
Tests for rh-developer__recommend-image per-skill evaluation.
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

    def test_mentions_image(self):
        content = read_report().lower()
        assert "image" in content, "report should mention container images"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 100, "report should have substantial content"


class TestSkillDependent:
    def test_remote_image_inspection_approach(self):
        """Skill teaches skopeo inspect docker:// for remote image inspection.
        Without skill, agents only consider local podman/docker pull."""
        c = read_report().lower()
        assert any(t in c for t in [
            "skopeo", "remote inspect", "registry inspect",
            "docker://", "image metadata", "without pulling"
        ]), "should discuss remote image inspection approach (e.g., skopeo, registry API)"

    def test_image_variant_categories(self):
        """Skill teaches three variant categories: Full (build tools), Minimal
        (smaller/secure), Runtime (smallest, no build tools). Without skill,
        agents don't distinguish these categories."""
        c = read_report().lower()
        variants = ["full", "minimal", "runtime"]
        mentioned = sum(1 for v in variants if v in c)
        assert mentioned >= 2, (
            "should compare image variant categories (Full, Minimal, Runtime)"
        )

    def test_security_data_awareness(self):
        """Skill teaches Red Hat Security Data API for CVE/security status per image.
        Without skill, agents skip security posture evaluation."""
        c = read_report().lower()
        assert any(t in c for t in ["security data", "cve", "vulnerability", "security api"]) and any(t in c for t in [
            "image", "scan", "check", "posture", "red hat"
        ]), "should address security/CVE posture for image selection"

    def test_ubi_registry_awareness(self):
        """Skill teaches UBI images from registry.access.redhat.com."""
        c = read_report().lower()
        assert any(t in c for t in ["ubi", "red hat", "registry"]) and any(t in c for t in [
            "python", "node", "java", "image"
        ]), "should recommend UBI images from Red Hat registry"
