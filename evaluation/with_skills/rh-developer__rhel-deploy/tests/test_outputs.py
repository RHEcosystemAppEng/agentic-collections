"""
Tests for rh-developer__rhel-deploy per-skill evaluation.
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

    def test_mentions_rhel_or_podman(self):
        content = read_report().lower()
        assert "rhel" in content or "podman" in content, "report should mention RHEL or Podman"

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_selinux_volume_labels(self):
        """Skill teaches SELinux volume labels: :z = shared (relabeled for multi-container),
        :Z = private. Without skill, agents skip SELinux mount context."""
        c = read_report()
        assert ":z" in c or ":Z" in c or "selinux" in c.lower(), (
            "should address SELinux volume labels (:z shared, :Z private)"
        )

    def test_rootless_systemd_path(self):
        """Skill teaches rootless systemd service location ~/.config/systemd/user/
        vs /etc/systemd/system/ for rootful. Without skill, agents only know rootful."""
        c = read_report()
        assert ".config/systemd/user" in c or "rootless" in c.lower(), (
            "should address rootless systemd path (~/.config/systemd/user/)"
        )

    def test_enable_linger(self):
        """Skill teaches loginctl enable-linger required for rootless user services
        to survive logout. Without skill, agents miss this requirement."""
        c = read_report().lower()
        assert "enable-linger" in c or "loginctl" in c or "linger" in c, (
            "should mention loginctl enable-linger for rootless services"
        )

    def test_semanage_fcontext(self):
        """Skill teaches semanage fcontext + restorecon for setting SELinux context
        on application files. Without skill, agents skip file context management."""
        c = read_report().lower()
        assert ("semanage fcontext" in c or "semanage" in c) and (
            "restorecon" in c or "fcontext" in c
        ), "should use semanage fcontext + restorecon for file SELinux context"

    def test_firewall_port(self):
        """Skill teaches firewall-cmd for opening application ports."""
        c = read_report().lower()
        assert "firewall-cmd" in c or ("firewall" in c and "port" in c), (
            "should address firewall port configuration"
        )

    def test_systemd_hardening_directives(self):
        """Docs teach systemd hardening directives: NoNewPrivileges=true,
        ProtectSystem=strict, ReadWritePaths. Without docs, agents create basic
        unit files without security hardening."""
        c = read_report()
        assert any(t in c for t in [
            "NoNewPrivileges", "ProtectSystem", "ReadWritePaths",
            "PrivateTmp", "ProtectHome",
        ]) or "hardening" in c.lower(), (
            "should include systemd hardening directives (NoNewPrivileges, ProtectSystem)"
        )

    def test_container_security_practices(self):
        """Skill teaches defence-in-depth for containers: dropping capabilities,
        resource limits, read-only root, security options. Without skill,
        agents deploy containers with default security settings."""
        c = read_report().lower()
        practices = sum(1 for t in [
            "cap-drop", "cap_drop", "capability",
            "--read-only", "read-only root",
            "resource limit", "memory", "cpus",
            "no-new-privileges", "security-opt",
        ] if t in c)
        assert practices >= 2, (
            "should address at least 2 container security practices "
            "(capability dropping, resource limits, read-only root, security options)"
        )
