"""
Tests for rh-sre__mcp-lightspeed-validator per-skill evaluation.
Baseline tests: report structure.
Skill-dependent tests: conceptual checks (no exact tool/field name matching).
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
        assert any(t in content for t in ['lightspeed', 'mcp', 'valid']), (
            "report should mention key topic"
        )

    def test_report_has_structure(self):
        content = read_report()
        assert len(content) > 150, "report should have substantial content"


class TestSkillDependent:
    def test_get_cves_no_params(self):
        """Skill: Call vulnerability__get_cves with NO parameters (limit causes limit_ serialization bug)."""
        c = read_report().lower()
        assert any(t in c for t in ["no param", "without param", "limit_"]), (
            "should call get_cves without parameters (skill: passing limit breaks some clients)"
        )

    def test_lightspeed_credentials(self):
        """Skill: LIGHTSPEED_CLIENT_ID + LIGHTSPEED_CLIENT_SECRET are the env vars."""
        c = read_report().lower()
        assert any(t in c for t in ["lightspeed_client_id", "client_id", "client_secret"]), (
            "should reference Lightspeed credential env vars (skill: LIGHTSPEED_CLIENT_ID/SECRET)"
        )

    def test_never_echo_credentials(self):
        """Skill: Never echo or log credential values."""
        c = read_report().lower()
        has_security = any(t in c for t in ["never echo", "do not echo", "redact", "sensitive", "protect"])
        assert has_security or "credential" in c, (
            "should address credential handling (skill: never echo values)"
        )

    def test_table_format(self):
        """Skill: Output table with Server | Outcome."""
        c = read_report().lower()
        has_table = "|" in read_report()
        has_outcome = any(t in c for t in ["passed", "failed", "get_cves", "lightspeed"])
        assert has_table or has_outcome, (
            "should use table format (skill: Report Format)"
        )
