# Per-Skill Evaluation Review Report

Review of each task under `tasks/per_skill_eval/` covering instructions, tests, skills, docs, and mock MCP. Criteria: instructions clear/realistic/fair/not overfitting; tests fair/not overfitting; mock MCP proper and realistic.

---

## ocp-admin__cluster-report

**Instructions:** Clear and realistic. Asks for cluster health and inventory report with version, nodes, projects, pods. Explicitly asks to document methodology. Does not mention skills. Fair scope.

**Tests:** Conceptual checks (cluster version, node status, resource utilization, projects, workload stats, context awareness). No exact tool or field names. Fair and not overfitting.

**Mock MCP:** mock-ocp-mcp provides multiple contexts (prod-us-east, prod-eu-west, staging-central, dev-k8s, legacy-dc), ClusterVersion, nodes, projects, pods. Realistic. Supports both OpenShift and non-OpenShift contexts. Good.

**Remarks:** None.

---

## rh-ai-engineer__ai-observability

**Instructions:** Clear. Set up monitoring for AI/ML models: metrics, GPU utilization, right-sizing. Does not mention skills. Realistic.

**Tests:** Conceptual (GPU monitoring, model metrics, right-sizing, Prometheus/Grafana, alerting). No tool-name matching. Fair.

**Mock MCP:** Uses rhoai and openshift mocks; not ai-observability MCP. Skill expects get_gpu_info, analyze_vllm, etc. Agent can still describe methodology from the skill. Rhoai mock has inference services, projects; openshift has resources. Adequate for methodology documentation.

**Remarks:** Mock does not implement ai-observability MCP tools. Agent relies on skill/docs and available rhoai/openshift tools. Acceptable for report-based evaluation.

---

## rh-ai-engineer__debug-inference

**Instructions:** Clear. Debug failing InferenceService: readiness, pod scheduling, resources, recommend fix. Does not mention skills. Realistic.

**Tests:** Conceptual (readiness, scheduling, logs, resources, events, fix recommendation). Fair.

**Mock MCP:** Rhoai mock has broken deployments (text-gen-legacy OOMKilled, nim-llama-prod failing). Openshift mock has pods, events, logs. Good for debugging.

**Remarks:** None.

---

## rh-ai-engineer__ds-project-setup

**Instructions:** Clear. Set up data science project with storage, model serving, data connections. Does not mention skills. Realistic.

**Tests:** Conceptual (project creation, data connections, model serving, credentials, dashboard). Fair.

**Mock MCP:** Rhoai mock has projects, data connections, serving runtimes, inference services. Good coverage.

**Remarks:** None.

---

## rh-ai-engineer__model-deploy

**Instructions:** Clear. Deploy ML model: serving runtime, InferenceService, GPU, common issues. Does not mention skills. Realistic.

**Tests:** Conceptual (serving runtime, InferenceService, storage, GPU/resource, verification). Fair.

**Mock MCP:** Rhoai mock has serving runtimes, inference services, deploy_model. Good.

**Remarks:** None.

---

## rh-ai-engineer__nim-setup

**Instructions:** Clear. Set up NVIDIA NIM: prerequisites (GPU Operator, NFD), NGC auth, NIM Account. Does not mention skills. Realistic.

**Tests:** Conceptual (GPU Operator, NFD, NGC auth, image pull secret, NIM Account). Fair.

**Mock MCP:** Rhoai and openshift. NIM Account is a CR; agent can describe setup. Adequate.

**Remarks:** None.

---

## rh-ai-engineer__serving-runtime-config

**Instructions:** Clear. Configure ServingRuntime: model format, container, platform integration. Does not mention skills. Realistic.

**Tests:** Conceptual (API group, model format, multi-model, container config, platform integration). Fair.

**Mock MCP:** Rhoai mock has list_serving_runtimes, serving runtime templates. Good.

**Remarks:** None.

---

## rh-ai-engineer__workbench-manage

**Instructions:** Clear. Manage workbench: notebook image, resources, storage, lifecycle. Does not mention skills. Realistic.

**Tests:** Conceptual (notebook image, resources, storage, lifecycle, data loss warning). Fair.

**Mock MCP:** Rhoai mock may not expose workbench-specific tools (list_workbenches, create_workbench, etc.). Agent documents methodology from skill. Adequate for report-based eval.

**Remarks:** Verify mock has workbench tools if agent is expected to call them. Otherwise methodology-only is acceptable.

---

## rh-developer__containerize-deploy

**Instructions:** Clear. Plan containerization (S2I, Dockerfile, Helm) and deployment. Does not mention skills. Realistic.

**Tests:** Conceptual (strategy evaluation, deployment config). Fair.

**Mock MCP:** Openshift mock with deployments, builds, projects. Good.

**Remarks:** None.

---

## rh-developer__debug-build

**Instructions:** Clear. S2I build failing; examine config/logs, identify phase, recommend fix. Does not mention skills. Realistic.

**Tests:** Conceptual (build config, phase, fix). Fair.

**Mock MCP:** Openshift mock has builds with status Complete; api-service pod crashes at runtime (entry point), not during build. No failing S2I build in mock. Agent documents methodology from skill. Adequate for report-based eval.

**Remarks:** Mock has no failing build; agent relies on skill/docs for build-debug methodology. Consider adding a failing build (e.g., failed pip install) for richer execution-based eval.

---

## rh-developer__debug-container

**Instructions:** Clear. Container failing at startup; inspect image/config, find cause, recommend fix. Does not mention skills. Realistic.

**Tests:** Conceptual (image inspection, root cause, fix). Fair.

**Mock MCP:** Openshift mock has containers. Adequate.

**Remarks:** None.

---

## rh-developer__debug-network

**Instructions:** Clear. HTTP 503 via Route; trace Route→Service→Pod, find misconfiguration. Does not mention skills. Realistic.

**Tests:** Conceptual (request path, misconfiguration, fix). Fair.

**Mock MCP:** Openshift mock has order-system with 503 (selector mismatch). Good.

**Remarks:** None.

---

## rh-developer__debug-pipeline

**Instructions:** Clear. Tekton PipelineRun failed; examine status, find failing task, recommend fix. Does not mention skills. Realistic.

**Tests:** Conceptual (PipelineRun, task, fix/retry). Fair.

**Mock MCP:** Openshift mock has pipeline data. Good.

**Remarks:** None.

---

## rh-developer__debug-pod

**Instructions:** Clear. Pod in web-frontend namespace crashing; investigate, find cause, recommend fix. Does not mention skills. Aligned with mock (web-frontend has OOMKilled). Realistic.

**Tests:** Conceptual (OOM/memory, exit code, previous logs, resource limits, events, remediation). Fair.

**Mock MCP:** Openshift mock has web-frontend with OOMKilled (exit 137, 64Mi limit). Good alignment.

**Remarks:** None.

---

## rh-developer__debug-rhel

**Instructions:** Clear. RHEL service failing; check service, SELinux, firewall, recommend fix. Does not mention skills. Realistic.

**Tests:** Conceptual (service, SELinux, firewall, fix). Fair.

**Mock MCP:** Uses available tools; RHEL debugging may be more doc/skill-driven. Adequate.

**Remarks:** None.

---

## rh-developer__deploy

**Instructions:** Clear. Plan deployment: strategy, Service, Route, image, ports. Does not mention skills. Realistic.

**Tests:** Conceptual (Deployment, Service, Route, image, ports). Fair.

**Mock MCP:** Openshift mock has deployments, services, routes. Good.

**Remarks:** None.

---

## rh-developer__detect-project

**Instructions:** Clear. Detect project type, language, framework from source. Does not mention skills. Realistic.

**Tests:** Conceptual (language, framework, deployment strategy). Fair.

**Mock MCP:** May use Read tool for source; MCP for cluster context. Adequate.

**Remarks:** None.

---

## rh-developer__helm-deploy

**Instructions:** Clear. Plan Helm deployment: chart, values, OpenShift specifics. Does not mention skills. Realistic.

**Tests:** Conceptual (Helm chart, values, OpenShift). Fair.

**Mock MCP:** Openshift mock. Adequate.

**Remarks:** None.

---

## rh-developer__recommend-image

**Instructions:** Clear. Recommend base image for project type (UBI, security, size). Does not mention skills. Realistic.

**Tests:** Conceptual (base image, UBI, selection criteria). Fair.

**Mock MCP:** May use project metadata from mock. Adequate.

**Remarks:** None.

---

## rh-developer__rhel-deploy

**Instructions:** Clear. Plan RHEL deployment: systemd, SELinux, volumes, networking. Does not mention skills. Realistic.

**Tests:** Conceptual (systemd, SELinux, volumes, networking). Fair.

**Mock MCP:** Adequate for methodology documentation.

**Remarks:** None.

---

## rh-developer__s2i-build

**Instructions:** Clear. Configure S2I for Python app: builder, build process, entry point. Does not mention skills. Realistic.

**Tests:** Conceptual (builder image, entry point, BuildConfig, dependencies). Fair.

**Mock MCP:** Openshift mock has builds, api-platform. Good.

**Remarks:** None.

---

## rh-developer__validate-environment

**Instructions:** Clear. Validate OpenShift: connectivity, permissions, resources, readiness. Does not mention skills. Realistic.

**Tests:** Conceptual (connectivity, permissions, resources, readiness). Fair.

**Mock MCP:** Openshift mock. Adequate.

**Remarks:** None.

---

## rh-sre__cve-impact

**Instructions:** Clear. Analyze CVE impact: affected systems, scope, pagination. Does not mention skills. Realistic.

**Tests:** Conceptual (affected systems count, pagination, environment breakdown, remediation readiness, severity). Fair.

**Mock MCP:** mock-lightspeed-mcp has 63 systems, 5 CVEs, get_cves, get_cve, get_cve_systems, get_system_cves. Realistic fleet and CVE data. Good.

**Remarks:** None.

---

## rh-sre__cve-validation

**Instructions:** Clear. Validate CVEs: identifiers, severity, fixes, remediation status. Does not mention skills. Realistic.

**Tests:** Conceptual (CVE validation, advisories, classification). Fair.

**Mock MCP:** Lightspeed mock. Good.

**Remarks:** None.

---

## rh-sre__execution-summary

**Instructions:** Minimal. "Complete the execution summary analysis." Vague but does not overfit. Agent discovers scope from skill.

**Tests:** Conceptual (execution summary concepts). Fair.

**Mock MCP:** AAP and Lightspeed mocks. Adequate.

**Remarks:** Instruction could be slightly more specific (e.g., "document tools and steps used in a remediation workflow") without overfitting.

---

## rh-sre__fleet-inventory

**Instructions:** Minimal. "Complete the fleet inventory analysis." Vague but fair. Agent discovers scope from skill.

**Tests:** Conceptual (fleet inventory concepts). Fair.

**Mock MCP:** Lightspeed mock with 63 systems. Good.

**Remarks:** Same as execution-summary: optional minor clarification.

---

## rh-sre__job-template-creator

**Instructions:** Minimal. "Create an AAP job template for CVE remediation." Fair. Agent discovers details from skill.

**Tests:** Conceptual (job template creation). Fair.

**Mock MCP:** AAP mock with job templates, projects. Good.

**Remarks:** None.

---

## rh-sre__job-template-remediation-validator

**Instructions:** Minimal. "Validate an AAP job template for CVE remediation." Fair.

**Tests:** Conceptual (template validation). Fair.

**Mock MCP:** AAP mock. Good.

**Remarks:** None.

---

## rh-sre__mcp-aap-validator

**Instructions:** Clear. Validate AAP MCP connectivity and functionality. Does not mention skills. Realistic.

**Tests:** Conceptual (connectivity, auth, tool availability, error diagnostics, structured output). Fair.

**Mock MCP:** AAP mock. Agent validates by calling tools. Good.

**Remarks:** None.

---

## rh-sre__mcp-lightspeed-validator

**Instructions:** Clear. Validate Lightspeed MCP connectivity and functionality. Does not mention skills. Realistic.

**Tests:** Conceptual (connectivity, auth, tools, diagnostics). Fair.

**Mock MCP:** Lightspeed mock. Good.

**Remarks:** None.

---

## rh-sre__playbook-executor

**Instructions:** Clear. Execute remediation playbook via AAP, pre-flight, monitoring. Does not mention skills. Realistic.

**Tests:** Conceptual (pre-flight, dry run, monitoring, validation, git/source). Fair.

**Mock MCP:** AAP mock with job templates, projects, jobs, launch. Good.

**Remarks:** None.

---

## rh-sre__playbook-generator

**Instructions:** Minimal. "Generate a CVE remediation playbook using Red Hat Insights/Lightspeed." Fair.

**Tests:** Conceptual (playbook generation). Fair.

**Mock MCP:** Lightspeed mock with create_vulnerability_playbook. Good.

**Remarks:** None.

---

## rh-sre__remediation

**Instructions:** Minimal. "Orchestrate CVE remediation from validation through execution and verification." Fair.

**Tests:** Conceptual (remediation orchestration). Fair.

**Mock MCP:** AAP and Lightspeed. Good.

**Remarks:** None.

---

## rh-sre__remediation-verifier

**Instructions:** Minimal. "Verify CVE remediation was applied." Fair.

**Tests:** Conceptual (verification). Fair.

**Mock MCP:** Lightspeed mock. Good.

**Remarks:** None.

---

## rh-sre__system-context

**Instructions:** Minimal. "Gather system context for remediation decisions." Fair.

**Tests:** Conceptual (system context). Fair.

**Mock MCP:** Lightspeed mock with system data. Good.

**Remarks:** None.

---

## rh-virt__vm-clone

**Instructions:** Clear. Clone production-db (prod-vms) to test-db-clone (test-env). Does not mention skills. Realistic.

**Tests:** Conceptual (cloning strategy, storage, independence). Fair.

**Mock MCP:** mock-virt-mcp has VMs but not production-db in prod-vms. Uses virt-prod-dc1, virt-prod-dc2, etc. Agent documents methodology for the given scenario. Adequate.

**Remarks:** Instruction VM/namespace (production-db, prod-vms) not in mock. Acceptable for methodology documentation.

---

## rh-virt__vm-create

**Instructions:** Clear. Plan VM test-vm in vm-testing. Does not mention skills. Realistic.

**Tests:** Conceptual (VM spec, storage, error handling). Fair.

**Mock MCP:** Virt mock. Agent can describe creation plan. Good.

**Remarks:** test-vm and vm-testing not in mock; acceptable for planning task.

---

## rh-virt__vm-delete

**Instructions:** Clear. Plan deletion of legacy-app in decommission. Does not mention skills. Realistic.

**Tests:** Conceptual (safety checks, scope, safeguards). Fair.

**Mock MCP:** Virt mock. Adequate.

**Remarks:** legacy-app and decommission not in mock; acceptable for planning.

---

## rh-virt__vm-inventory

**Instructions:** Clear. Produce VM inventory: all namespaces, status, resources, OS, IPs, organization. Does not mention skills. Realistic.

**Tests:** Conceptual (VM status, CPU/memory, OS, network, storage, node, sort). No tool/field names. Fair.

**Mock MCP:** mock-virt-mcp has 32 VMs across namespaces, VM/VMI, nodes, PVCs. Good. VMI may lack volumeStatus; agent can still produce inventory from VM and VMI data.

**Remarks:** None.

---

## rh-virt__vm-lifecycle-manager

**Instructions:** Clear. Stop web-frontend, restart production-db in prod-vms. Does not mention skills. Realistic.

**Tests:** Conceptual (lifecycle procedures, sequencing, verification). Fair.

**Mock MCP:** Virt mock. Adequate.

**Remarks:** web-frontend, production-db, prod-vms not in mock; acceptable for methodology.

---

## rh-virt__vm-rebalance

**Instructions:** Clear. Migrate production-db from overloaded node. Does not mention skills. Realistic.

**Tests:** Conceptual (migration feasibility, target node, safety). Fair.

**Mock MCP:** Virt mock has nodes and utilization. Good.

**Remarks:** production-db not in mock; acceptable.

---

## rh-virt__vm-snapshot-create

**Instructions:** Clear. Snapshot production-db in prod-vms; prerequisites, spec, consistency. Does not mention skills. Realistic.

**Tests:** Conceptual (prerequisites, consistency, spec, monitoring, volume check). Baseline requires "production-db" (from instruction). Fair.

**Mock MCP:** Virt mock does not implement VirtualMachineSnapshot in resources_list. Agent documents plan from skill. Adequate for methodology documentation.

**Remarks:** production-db and prod-vms not in mock; test expects "production-db" from instruction. Consistent. Snapshot CRs not in mock; agent works from skill.

---

## rh-virt__vm-snapshot-delete

**Instructions:** Clear. Delete snapshot production-db-backup-20240215 for production-db in prod-vms. Does not mention skills. Realistic.

**Tests:** Conceptual (safety, confirmation, verification). Fair.

**Mock MCP:** Virt mock. Adequate.

**Remarks:** None.

---

## rh-virt__vm-snapshot-list

**Instructions:** Clear. List snapshots for production-db in prod-vms. Does not mention skills. Realistic.

**Tests:** Conceptual (snapshot list, status, timestamps). Fair.

**Mock MCP:** Virt mock. Check if VirtualMachineSnapshot is supported. Adequate.

**Remarks:** None.

---

## rh-virt__vm-snapshot-restore

**Instructions:** Clear. Restore production-db from snapshot production-db-backup-20240301. Does not mention skills. Realistic.

**Tests:** Conceptual (readiness, VM state, safeguards). Fair.

**Mock MCP:** Virt mock. Adequate.

**Remarks:** None.

---

## Summary

**Overall:** Instructions are clear, realistic, and do not mention skills. Tests use conceptual checks and avoid exact tool/field matching. Mocks are generally appropriate.

**Notable points:**
- ai-observability: Mock uses rhoai/openshift, not ai-observability MCP; acceptable for methodology documentation.
- workbench-manage: Confirm workbench tools exist in mock if execution is expected.
- debug-build: Confirm mock includes a failing build scenario.
- rh-sre minimal instructions (execution-summary, fleet-inventory, etc.): Vague but fair; optional minor clarification.
- rh-virt: Several tasks reference VMs/namespaces (production-db, prod-vms, etc.) not in mock; acceptable for planning/methodology tasks.
