"""
Tests for rh-developer__debug-rhel per-skill evaluation.
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

    def test_mentions_rhel_or_system(self):
        content = read_report().lower()
        assert "rhel" in content or "system" in content or "service" in content, (
            "report should mention RHEL or system"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_ausearch_avc_command(self):
        """Skill teaches ausearch -m AVC -ts recent for recent SELinux denials.
        Without skill, agents use generic SELinux checks without ausearch."""
        c = read_report().lower()
        assert "ausearch" in c, (
            "should use ausearch for SELinux AVC denial investigation"
        )

    def test_semanage_port_labeling(self):
        """Skill teaches semanage port for nonstandard bind port SELinux labeling.
        Without skill, agents skip port-level SELinux context management."""
        c = read_report().lower()
        assert "semanage port" in c or ("semanage" in c and "port" in c), (
            "should use semanage port for nonstandard port SELinux labeling"
        )

    def test_systemd_journal_workflow(self):
        """Skill teaches systemctl status + journalctl -u for service logs."""
        c = read_report().lower()
        assert any(t in c for t in ["systemctl", "journalctl"]) and any(t in c for t in [
            "status", "-u", "service", "log"
        ]), "should use systemd/journal workflow"

    def test_firewall_cmd(self):
        """Skill teaches firewall-cmd for port management."""
        c = read_report().lower()
        assert "firewall-cmd" in c or "firewall" in c, (
            "should check firewall configuration"
        )

    def test_concrete_remediation(self):
        """Skill teaches concrete remediation commands for RHEL issues."""
        c = read_report().lower()
        assert any(t in c for t in ["systemctl restart", "firewall-cmd", "semanage", "restorecon"]) or (
            "```" in read_report() and any(t in c for t in ["sudo", "systemctl"])
        ), "should include concrete RHEL remediation commands"

    def test_permanent_firewall_flag(self):
        """Skill teaches using --permanent flag with firewall-cmd to persist rules
        across reboots. Without skill, agents use firewall-cmd without --permanent,
        creating rules that are lost on reboot."""
        c = read_report()
        assert "--permanent" in c, (
            "should use --permanent flag with firewall-cmd for persistent rules"
        )

    def test_http_port_t_selinux_type(self):
        """Skill teaches the specific SELinux type http_port_t for web service ports.
        Without skill, agents use generic semanage commands without specifying the
        correct SELinux type for HTTP ports."""
        c = read_report()
        assert "http_port_t" in c, (
            "should reference http_port_t SELinux type for port labeling"
        )

    def test_getenforce_check(self):
        """Skill teaches using getenforce to verify SELinux mode (Enforcing/Permissive)
        as a first diagnostic step. Without skill, agents jump to specific SELinux
        fixes without verifying the enforcement mode."""
        c = read_report().lower()
        assert "getenforce" in c, (
            "should use getenforce to check SELinux enforcement mode"
        )
