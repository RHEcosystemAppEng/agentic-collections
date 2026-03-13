# Virtual Machine Provisioning Skill

Create a skill that provisions a new virtual machine in an OpenShift Virtualization cluster. The skill must gather required parameters, check for existing resources, present a configuration summary for user confirmation, create the VM, and diagnose scheduling failures.

## Capabilities

### Parameter gathering with AskUserQuestion

When required parameters are missing, the skill uses an interactive question tool to collect VM name, namespace, operating system, performance class, size, storage, and autostart preference from the user.

- When invoked without parameters, the skill issues an interactive question with all 8 VM configuration fields [@test](./tests/test_parameter_gathering.md)
- OS label "Fedora" maps to the parameter value `"fedora"` and size label "Medium" maps to `"medium"` [@test](./tests/test_label_value_mapping.md)

### Duplicate resource check before creation

Before attempting to create a VM, the skill checks whether a VM with the same name already exists in the target namespace and halts with options if it does.

- A pre-creation check fetches the existing VM resource and presents options (rename/delete existing/cancel) if found [@test](./tests/test_duplicate_check.md)

### Configuration confirmation before creation

The skill displays a formatted configuration table and waits for explicit user confirmation before invoking the VM creation tool.

- The skill presents a configuration table showing all parameters and asks "Confirm: yes/no/modify" before creating [@test](./tests/test_config_confirmation.md)

### Scheduling failure diagnosis

When the VM enters an unschedulable state, the skill consults a reference document, gathers diagnostic events, and presents a root-cause analysis with remediation options.

- When `ErrorUnschedulable` is detected, the step reads the troubleshooting reference file before presenting the diagnosis [@test](./tests/test_scheduling_diagnosis.md)

## Implementation

[@generates](./skills/vm-provision/SKILL.md)

## API

```markdown { #api }
## Workflow

### Step 1: Gather VM Requirements
- Required: VM Name (validated), Namespace
- Optional: OS (default: fedora), Size (default: medium), Storage (default: 30Gi), Performance (default: u1), Autostart (default: false)
- Use AskUserQuestion when parameters missing

### Step 2: Check VM Existence
**MCP Tool**: get resource by apiVersion, kind, namespace, name
- If found: display options (rename/delete/cancel), STOP and wait

### Step 3: Present Configuration for Confirmation
Display table of all parameters, ask "Confirm: yes/no/modify", WAIT

### Step 4: Create Virtual Machine
**MCP Tool**: vm_create(namespace, name, workload, size, storage, performance, autostart)

### Step 5: Verify Status
Check status; on ErrorUnschedulable: run diagnostic workflow (Step 5a)

### Step 5a: Diagnostic Workflow
1. Read scheduling-errors.md
2. Gather events and node taints
3. Present root cause + options, WAIT
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing the rh-virt VM provisioning patterns, OpenShift Virtualization MCP server tool conventions, and VM lifecycle management workflow structure.
