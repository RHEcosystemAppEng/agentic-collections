"""
Test suite for OpenShift Virtualization (deterministic checks).

Part 1 – Clone 'vm-db-prod-01' (virt-prod-dc2) → 'vm-db-test-01' (virt-staging)
Part 2 – Evacuate maintenance node hv-prod-dc1-03 (migrate VMs)
Part 3 – Provision 'perf-bench-01' in virt-staging for CPU-bound benchmarks
Part 4 – Decommission 'vm-db-stg-02' from virt-staging

Deterministic tests verify file existence, JSON structure, and exact values.
Skill-knowledge evaluation of report content is handled by llm_judge.py.
"""

import os
import re
import json
import pytest

# ── Part 1 files ──────────────────────────────────────────────────────────
REQUIRED_REPORTS = [
    "/root/pre_cloning_verification.md",
    "/root/execution_and_telemetry_log.md",
    "/root/hardware_identity_audit.md",
]
CLONED_VM_SPEC = "/root/cloned_vm_spec.json"

# ── Part 2 files ──────────────────────────────────────────────────────────
MIGRATION_REPORT = "/root/migration_assessment.md"
MIGRATION_PLAN_JSON = "/root/migration_plan.json"

# ── Part 3 files ──────────────────────────────────────────────────────────
PROVISION_REPORT = "/root/vm_provisioning_report.md"
VM_CREATE_PARAMS = "/root/perf_bench_vm_create.json"

# ── Part 4 files ──────────────────────────────────────────────────────────
DELETION_REPORT = "/root/deletion_operations_report.md"
DELETION_SCOPE_JSON = "/root/deletion_scope.json"

MAINTENANCE_NODE = "hv-prod-dc1-03"
MAINTENANCE_VMS = {"vm-legacy-auth-01", "vm-backup-prod-01"}
VALID_DC1_TARGETS = {"hv-prod-dc1-01", "hv-prod-dc1-02"}


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def _load_create_params(path: str) -> dict:
    """Load vm_create JSON and extract the actual tool parameters.

    Agents may produce flat params: {"name": "x", "namespace": "y", ...}
    or nested wrappers:  {"parameters": {"name": "x", ...}, "tool": "vm_create"}
    This normalises both into a flat dict.
    """
    with open(path) as f:
        data = json.load(f)
    if "parameters" in data and isinstance(data["parameters"], dict):
        return data["parameters"]
    if "args" in data and isinstance(data["args"], dict):
        return data["args"]
    if "input" in data and isinstance(data["input"], dict):
        return data["input"]
    return data


# ═══════════════════════════════════════════════════════════════════════════
#  PART 1 — BASELINE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPart1RequirementFulfillment:
    """All Part 1 deliverables must exist with professional structure."""

    def test_deliverables_exist(self):
        for path in REQUIRED_REPORTS + [CLONED_VM_SPEC]:
            assert os.path.exists(path), f"Missing required file: {path}"

    def test_markdown_structure(self):
        for path in REQUIRED_REPORTS:
            content = read_file(path)
            assert len(re.findall(r"^#+\s+", content, re.MULTILINE)) >= 2, (
                f"{path} lacks section headings"
            )


class TestPart1SourceDataAccuracy:
    """Agent must reflect actual mock data for vm-db-prod-01."""

    def test_source_vm_cpu_and_memory(self):
        """Source VM has 8 vCPUs and 16Gi memory — both must appear near
        resource-related terms, not just as bare numbers."""
        content = read_file("/root/pre_cloning_verification.md").lower()
        has_cpu = bool(re.search(
            r"\b8\b.{0,20}(?:cpu|core|vcpu|socket)|(?:cpu|core|vcpu|socket).{0,20}\b8\b",
            content,
        ))
        has_mem = bool(re.search(
            r"16\s*gi\b|16\s*gb\b|\b16\b.{0,20}(?:mem|ram)|(?:mem|ram|memory).{0,20}\b16\b",
            content,
        ))
        assert has_cpu and has_mem, (
            "Source VM resources (8 CPU / 16Gi) not correctly identified in context"
        )

    def test_source_vm_os(self):
        content = read_file("/root/pre_cloning_verification.md").lower()
        assert "rhel-9.3" in content or "rhel 9.3" in content, (
            "Source OS (RHEL 9.3) not correctly identified"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  PART 1 — SKILL-DEPENDENT TESTS  (vm-clone)
# ═══════════════════════════════════════════════════════════════════════════

class TestCloningProtocols:
    """Verify adherence to vm-clone SKILL.md protocols."""

    def test_unique_hardware_identifiers(self):
        """Clone must have its own firmware UUID and Serial.

        KubeVirt firmware identity (spec.template.spec.domain.firmware.uuid
        and .serial) is domain-specific knowledge from the skill's Step 4.1.
        Without the skill, agents don't know these fields exist.
        """
        with open(CLONED_VM_SPEC) as f:
            spec = json.load(f)
        firmware = (
            spec.get("spec", {})
            .get("template", {})
            .get("spec", {})
            .get("domain", {})
            .get("firmware", {})
        )
        uuid_val = firmware.get("uuid", "")
        serial_val = firmware.get("serial", "")
        assert uuid_val, (
            "Clone spec missing 'spec.template.spec.domain.firmware.uuid'"
        )
        assert serial_val, (
            "Clone spec missing 'spec.template.spec.domain.firmware.serial'"
        )
        assert "vm-db-prod-01" not in uuid_val and "vm-db-prod-01" not in serial_val, (
            "Clone firmware identifiers must not reference the source VM name"
        )

    def test_initial_run_state_halted(self):
        """Clone must start in stopped / Halted state.

        The instruction hints at this ('avoid resource contention'), so this
        is partially guessable. The skill makes it explicit: runStrategy=Halted.
        """
        with open(CLONED_VM_SPEC) as f:
            spec = json.load(f)
        running = spec.get("spec", {}).get("running", True)
        run_strategy = spec.get("spec", {}).get("runStrategy", "")
        assert running is False or run_strategy == "Halted", (
            "Clone must be initialized in a stopped/Halted state"
        )

    def test_datavolume_naming_convention(self):
        """Clone's DataVolume should follow the skill's naming convention:
        <target-vm-name>-rootdisk.

        Source: vm-clone SKILL.md — DataVolume naming pattern.
        Without the skill, agents may use arbitrary DV names.
        """
        with open(CLONED_VM_SPEC) as f:
            spec = json.load(f)
        dv_templates = spec.get("spec", {}).get("dataVolumeTemplates", [])
        volumes = (
            spec.get("spec", {})
            .get("template", {})
            .get("spec", {})
            .get("volumes", [])
        )
        all_names = [dv.get("metadata", {}).get("name", "") for dv in dv_templates]
        all_names += [v.get("dataVolume", {}).get("name", "") for v in volumes if "dataVolume" in v]
        all_names += [v.get("persistentVolumeClaim", {}).get("claimName", "") for v in volumes if "persistentVolumeClaim" in v]
        assert any("vm-db-test-01" in n and "rootdisk" in n for n in all_names), (
            "Clone spec should use the naming convention '<vm-name>-rootdisk' "
            "for its DataVolume (skill-defined pattern)"
        )

    # Skill-knowledge tests for report content (clone storage doc reference)
    # are evaluated by llm_judge.py


# ═══════════════════════════════════════════════════════════════════════════
#  PART 2 — BASELINE TESTS  (migration)
# ═══════════════════════════════════════════════════════════════════════════

class TestPart2RequirementFulfillment:
    """Part 2 migration deliverables must exist."""

    def test_migration_deliverables_exist(self):
        for path in (MIGRATION_REPORT, MIGRATION_PLAN_JSON):
            assert os.path.exists(path), f"Missing required file: {path}"

    def test_migration_report_structure(self):
        content = read_file(MIGRATION_REPORT)
        assert len(re.findall(r"^#+\s+", content, re.MULTILINE)) >= 2, (
            "migration_assessment.md lacks section headings"
        )

    def test_migration_plan_is_array(self):
        """migration_plan.json must be a JSON array of VM migration entries."""
        with open(MIGRATION_PLAN_JSON) as f:
            plan = json.load(f)
        if isinstance(plan, dict):
            plan = plan.get("migrations", plan.get("plan", plan.get("vms", [])))
        assert isinstance(plan, list), (
            "migration_plan.json must contain a JSON array of migration entries"
        )
        assert len(plan) >= 2, (
            "migration_plan.json must contain entries for at least 2 VMs"
        )


class TestMigrationAccuracy:
    """Migration plan must correctly identify VMs, source, and targets."""

    def _load_plan(self):
        with open(MIGRATION_PLAN_JSON) as f:
            plan = json.load(f)
        if isinstance(plan, dict):
            plan = plan.get("migrations", plan.get("plan", plan.get("vms", [])))
        return plan

    def test_identifies_maintenance_node_vms(self):
        """Plan must reference both VMs on hv-prod-dc1-03."""
        plan = self._load_plan()
        plan_str = json.dumps(plan).lower()
        for vm in MAINTENANCE_VMS:
            assert vm in plan_str, (
                f"Migration plan missing VM '{vm}' from maintenance node"
            )

    def test_target_nodes_in_same_datacenter(self):
        """Target nodes must be other dc1 nodes (hv-prod-dc1-01 or -02)."""
        plan = self._load_plan()
        plan_str = json.dumps(plan).lower()
        has_valid_target = any(t in plan_str for t in VALID_DC1_TARGETS)
        assert has_valid_target, (
            f"Migration targets must be in the same datacenter: {VALID_DC1_TARGETS}"
        )

    # Skill-knowledge tests for migration report content (node schedulability,
    # timeout estimation, concurrency limits) are evaluated by llm_judge.py


# ═══════════════════════════════════════════════════════════════════════════
#  PART 3 — BASELINE TESTS  (provisioning)
# ═══════════════════════════════════════════════════════════════════════════

class TestPart3RequirementFulfillment:
    """Part 3 deliverables must exist."""

    def test_provisioning_deliverables_exist(self):
        for path in (PROVISION_REPORT, VM_CREATE_PARAMS):
            assert os.path.exists(path), f"Missing required file: {path}"

    def test_provisioning_report_structure(self):
        content = read_file(PROVISION_REPORT)
        assert len(re.findall(r"^#+\s+", content, re.MULTILINE)) >= 2, (
            "vm_provisioning_report.md lacks section headings"
        )

    def test_create_json_has_basic_params(self):
        """vm_create JSON must include name, namespace, and workload."""
        params = _load_create_params(VM_CREATE_PARAMS)
        assert params.get("name") == "perf-bench-01", (
            "vm_create JSON must set name to 'perf-bench-01'"
        )
        assert params.get("namespace") == "virt-staging", (
            "vm_create JSON must target namespace 'virt-staging'"
        )
        assert "fedora" in str(params.get("workload", "")).lower(), (
            "vm_create JSON must use Fedora as workload"
        )

    def test_autostart_disabled(self):
        """VM must not auto-start per instruction."""
        params = _load_create_params(VM_CREATE_PARAMS)
        assert params.get("autostart") is False or params.get("autostart") == "false", (
            "perf-bench-01 must have autostart disabled"
        )


# Skill-knowledge tests for provisioning (compute profile, scheduling doc
# reference) are evaluated by llm_judge.py


# ═══════════════════════════════════════════════════════════════════════════
#  PART 4 — BASELINE TESTS  (decommissioning)
# ═══════════════════════════════════════════════════════════════════════════

class TestPart4RequirementFulfillment:
    """Part 4 deliverables must exist."""

    def test_deletion_deliverables_exist(self):
        for path in (DELETION_REPORT, DELETION_SCOPE_JSON):
            assert os.path.exists(path), f"Missing required file: {path}"

    def test_deletion_scope_identifies_target_vm(self):
        """Scope JSON must reference vm-db-stg-02 and virt-staging."""
        with open(DELETION_SCOPE_JSON) as f:
            scope = json.load(f)
        scope_str = json.dumps(scope).lower()
        assert "vm-db-stg-02" in scope_str, (
            "Deletion scope must reference target VM 'vm-db-stg-02'"
        )
        assert "virt-staging" in scope_str, (
            "Deletion scope must reference namespace 'virt-staging'"
        )


# Skill-knowledge tests for deletion (label-selector discovery, protection
# label, typed confirmation, paused state, deletion profiles, troubleshooting
# doc references) are evaluated by llm_judge.py
