"""
Tests for rh-virt__vm-lifecycle-manager per-skill evaluation.
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

    def test_mentions_operations(self):
        c = read_report().lower()
        assert ("stop" in c or "halt" in c) and ("restart" in c or "start" in c), (
            "report should discuss stop and restart operations"
        )

    def test_mentions_vms(self):
        c = read_report().lower()
        assert any(t in c for t in ["vm", "virtual machine", "virtualmachine"]), (
            "report should reference the target VMs"
        )


class TestSkillDependent:
    def test_two_step_restart(self):
        """Skill: Restart = stop then start (not single atomic); resourceVersion conflict."""
        c = read_report().lower()
        assert ("stop" in c and "start" in c) and any(t in c for t in ["two", "separate", "sequence", "then", "first", "resourceversion", "conflict"]), (
            "should explain restart as stop-then-start, not single operation"
        )

    def test_run_strategy_control(self):
        """Skill: RunStrategy Always/Halted for start/stop; not generic power state."""
        c = read_report().lower()
        assert any(t in c for t in ["runstrategy", "run strategy", "always", "halted"]) and (
            "start" in c or "stop" in c
        ), (
            "should map start/stop to RunStrategy (Always/Halted)"
        )

    def test_ready_verification(self):
        """Skill: Verify status.printableStatus Stopped/Running after each step."""
        c = read_report().lower()
        assert any(t in c for t in ["printablestatus", "printable status", "status", "stopped", "running"]) and (
            any(t in c for t in ["verify", "check", "poll", "wait", "before start"])
        ), (
            "should verify VM reached expected state before proceeding"
        )

    def test_vm_lifecycle_tool(self):
        """Skill: vm_lifecycle MCP tool for start/stop/restart."""
        c = read_report().lower()
        assert any(t in c for t in ["vm_lifecycle", "vm lifecycle", "lifecycle tool", "mcp"]), (
            "should reference vm_lifecycle or MCP lifecycle tool"
        )

    def test_restart_composite(self):
        """Skill: Restart implemented as stop → verify stopped → wait → start."""
        c = read_report().lower()
        has_stop_start = "stop" in c and "start" in c
        has_wait = any(t in c for t in ["wait", "5 second", "poll", "verify stopped"])
        assert has_stop_start and has_wait, (
            "should include wait/verify between stop and start for restart"
        )
