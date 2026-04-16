# Model Testing Plan for Air-Gapped LLM Deployment

## Overview

This document defines the testing plan for evaluating 5 open-source LLM models in the air-gapped OpenShift environment. The goal is to identify the optimal model that can execute skills from the `agentic-collections` repository with performance comparable to Claude Sonnet 4.5.

**Testing Environment:**
- Red Hat OpenShift 4.20+
- Red Hat OpenShift AI 2.22+
- NVIDIA GPU infrastructure
- vLLM serving runtime
- OpenCode as the client interface

**Success Criteria:**
- Response latency: < 5 seconds for typical queries
- Skills execution success rate: > 95%
- Response quality: Comparable to Claude Sonnet 4.5
- Hardware footprint: Reasonable for production deployment

---

## Model Candidates

| # | Model | Parameters | Quantization | Context Window | License | Download Size | Status |
|---|-------|------------|--------------|----------------|---------|---------------|--------|
| 1 | Llama 3.1 405B Instruct | 405B | FP8 | 128K | Llama 3.1 Community | ~210 GB | Testing |
| 2 | Qwen 2.5 72B Instruct | 72B | FP8 | 128K | Apache 2.0 | ~40 GB | Planned |
| 3 | DeepSeek V3 | 671B (37B active) | FP8 | 128K | MIT | ~350 GB | Planned |
| 4 | Nemotron 70B Instruct | 70B | FP8 | 128K | NVIDIA Open Model | ~38 GB | Planned |
| 5 | Mixtral 8x22B Instruct | 141B (39B active) | FP8 | 64K | Apache 2.0 | ~75 GB | Planned |

**Notes:**
- All sizes are for FP8 quantization (reduced from FP16/BF16 baseline)
- DeepSeek V3 and Mixtral use MoE (Mixture of Experts) architecture - only active parameters load per request
- Context window is maximum supported; actual usage may be lower

---

## Testing Metrics Table

### Hardware & Performance Metrics

| Model | GPU Type | GPU Count | Total VRAM | CPU Cores | System RAM | Tensor Parallelism | Avg Latency (simple) | Avg Latency (complex) | Tokens/sec |
|-------|----------|-----------|------------|-----------|------------|-------------------|---------------------|----------------------|------------|
| Llama 3.1 405B | H100 80GB | 8 | 640 GB | 64 | 512 GB | 8 | TBD | TBD | TBD |
| Qwen 2.5 72B | H100 80GB | 2 | 160 GB | 32 | 256 GB | 2 | TBD | TBD | TBD |
| DeepSeek V3 | H100 80GB | 6 | 480 GB | 64 | 512 GB | 6 | TBD | TBD | TBD |
| Nemotron 70B | H100 80GB | 2 | 160 GB | 32 | 256 GB | 2 | TBD | TBD | TBD |
| Mixtral 8x22B | H100 80GB | 4 | 320 GB | 48 | 384 GB | 4 | TBD | TBD | TBD |

**Latency Definitions:**
- **Simple query**: Basic information retrieval (e.g., `/cluster-report` with namespace listing)
- **Complex query**: Multi-step reasoning or code generation (e.g., `/playbook-generator`)

---

### Skills Execution Results

| Model | `/cluster-report` | `/cve-impact` | `/playbook-generator` | `/remediation` | Long Context (50K+) | Overall Success Rate |
|-------|-------------------|---------------|----------------------|----------------|---------------------|---------------------|
| Llama 3.1 405B | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | TBD |
| Qwen 2.5 72B | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | TBD |
| DeepSeek V3 | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | TBD |
| Nemotron 70B | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | TBD |
| Mixtral 8x22B | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending | TBD |

**Legend:**
- ✅ Pass (meets criteria)
- ⚠️ Partial (works but with limitations)
- ❌ Fail (does not meet criteria)
- ⏳ Pending (not yet tested)

---

### Response Quality Assessment

| Model | Accuracy | Reasoning Depth | Code Quality | Tool Calling | Instruction Following | Hallucination Rate | Overall Quality Score |
|-------|----------|----------------|--------------|--------------|----------------------|-------------------|----------------------|
| Llama 3.1 405B | TBD | TBD | TBD | TBD | TBD | TBD | TBD / 10 |
| Qwen 2.5 72B | TBD | TBD | TBD | TBD | TBD | TBD | TBD / 10 |
| DeepSeek V3 | TBD | TBD | TBD | TBD | TBD | TBD | TBD / 10 |
| Nemotron 70B | TBD | TBD | TBD | TBD | TBD | TBD | TBD / 10 |
| Mixtral 8x22B | TBD | TBD | TBD | TBD | TBD | TBD | TBD / 10 |

**Quality Metrics (each rated 1-10):**
- **Accuracy**: Factual correctness of responses
- **Reasoning Depth**: Multi-step logic and analysis quality
- **Code Quality**: Syntactic correctness, best practices, error handling
- **Tool Calling**: Ability to correctly invoke MCP tools/skills
- **Instruction Following**: Adherence to prompts and constraints
- **Hallucination Rate**: Lower is better (10 = no hallucinations)

---

### Cost & Operational Metrics

| Model | Deployment Time | Cold Start Time | Update Complexity | Storage Required | Est. Monthly Power Cost | Total Cost Score |
|-------|-----------------|-----------------|-------------------|------------------|------------------------|------------------|
| Llama 3.1 405B | TBD | TBD | Medium | 250 GB | TBD | TBD / 10 |
| Qwen 2.5 72B | TBD | TBD | Low | 50 GB | TBD | TBD / 10 |
| DeepSeek V3 | TBD | TBD | Medium | 400 GB | TBD | TBD / 10 |
| Nemotron 70B | TBD | TBD | Low | 50 GB | TBD | TBD / 10 |
| Mixtral 8x22B | TBD | TBD | Medium | 100 GB | TBD | TBD / 10 |

**Cost Score (1-10):**
- 10 = Most cost-effective (lower hardware, faster deployment, easier maintenance)
- 1 = Highest cost (maximum hardware, complex operations)

---

## Testing Methodology

### Phase 1: Infrastructure Setup (Per Model)

**Steps:**
1. Deploy model to PVC using helper pod
2. Create ServingRuntime with appropriate vLLM configuration
3. Deploy InferenceService with KServe
4. Verify endpoint accessibility
5. Run basic health check (simple prompt test)

**Success Criteria:**
- Model loads successfully without OOM errors
- Endpoint returns valid responses
- Latency is within acceptable range (< 10s for first token)

---

### Phase 2: Skills Execution Testing

Execute skills from each category defined in the original study:

#### Test Case 1: Simple Information Retrieval
**Skill:** `/cluster-report` (namespace listing)

**Test Prompt:**
```
List all namespaces in the OpenShift cluster and categorize them by purpose 
(system, operators, applications, AI/ML workloads).
```

**Success Criteria:**
- Response time: < 5 seconds
- Accuracy: 100% (all namespaces identified correctly)
- Format: Properly structured output

---

#### Test Case 2: Complex CVE Analysis
**Skill:** `/cve-impact` (CVE-2024-3094 xz backdoor)

**Test Prompt:**
```
Analyze CVE-2024-3094 (xz utils backdoor). Provide:
1. CVSS score and severity
2. Affected systems in RHEL ecosystem
3. Attack vector explanation
4. Immediate mitigation steps
5. Long-term remediation strategy
```

**Success Criteria:**
- Identifies correct CVSS score (10.0)
- Lists affected RHEL versions accurately
- Provides actionable mitigation steps
- Explains technical details correctly
- No hallucinations about unaffected systems

---

#### Test Case 3: Code Generation
**Skill:** `/playbook-generator` (Ansible playbook for patching)

**Test Prompt:**
```
Generate an Ansible playbook to patch CVE-2024-3094 on RHEL 8 and RHEL 9 systems.
Requirements:
- Check if xz-utils is affected version
- Backup current xz package before update
- Update to patched version
- Verify patch success
- Include error handling and rollback capability
- Follow Ansible best practices (idempotency, tags, handlers)
```

**Success Criteria:**
- Valid YAML syntax
- Runnable without errors
- Includes all required tasks
- Implements error handling
- Follows Ansible best practices (uses modules correctly, idempotent)

---

#### Test Case 4: Orchestration Workflow
**Skill:** `/remediation` (end-to-end CVE remediation)

**Test Prompt:**
```
Execute complete CVE remediation workflow for CVE-2024-3094:
1. Identify affected systems
2. Assess risk and prioritize
3. Generate remediation playbook
4. Simulate execution plan
5. Verify remediation completeness
6. Generate compliance report
```

**Success Criteria:**
- Correctly sequences all 6 sub-tasks
- Maintains context across multi-step workflow
- Generates valid outputs at each stage
- Provides coherent final report
- No task omissions or duplications

---

#### Test Case 5: Long Context Handling
**Test:** Analyze all SKILL.md files from `rh-sre/skills/`

**Test Prompt:**
```
Read and analyze all skill definitions in the rh-sre collection.
Provide:
1. Total number of skills
2. Categorization by purpose (monitoring, remediation, analysis, etc.)
3. Dependency graph (which skills call other skills)
4. Common patterns across skills
5. Recommendations for new skills to fill gaps
```

**Success Criteria:**
- Processes > 50K tokens without truncation
- Accurate skill count and categorization
- Correct dependency identification
- No context loss or hallucinations
- Coherent cross-skill analysis

---

### Phase 3: Comparative Analysis

After all models are tested:

1. **Normalize scores** across all metrics
2. **Weight factors** based on importance:
   - Quality: 40%
   - Performance: 30%
   - Cost: 20%
   - Operational complexity: 10%
3. **Calculate final scores** for each model
4. **Select recommended model** based on total weighted score

---

## Test Execution Tracking

| Test Date | Model | Tester | Test Phase | Results Location | Notes |
|-----------|-------|--------|------------|------------------|-------|
| TBD | Llama 3.1 405B | TBD | Phase 1 | `results/llama31-405b/phase1.md` | Initial deployment |
| TBD | Qwen 2.5 72B | TBD | Phase 1 | `results/qwen25-72b/phase1.md` | - |
| TBD | DeepSeek V3 | TBD | Phase 1 | `results/deepseek-v3/phase1.md` | - |
| TBD | Nemotron 70B | TBD | Phase 1 | `results/nemotron-70b/phase1.md` | - |
| TBD | Mixtral 8x22B | TBD | Phase 1 | `results/mixtral-8x22b/phase1.md` | - |

---

## Model Selection Decision Matrix

After testing is complete, use this matrix to make the final decision:

| Factor | Weight | Llama 3.1 405B | Qwen 2.5 72B | DeepSeek V3 | Nemotron 70B | Mixtral 8x22B |
|--------|--------|----------------|--------------|-------------|--------------|---------------|
| **Response Quality** | 40% | TBD | TBD | TBD | TBD | TBD |
| **Performance (Latency)** | 30% | TBD | TBD | TBD | TBD | TBD |
| **Cost (Hardware)** | 20% | TBD | TBD | TBD | TBD | TBD |
| **Operational Complexity** | 10% | TBD | TBD | TBD | TBD | TBD |
| **TOTAL WEIGHTED SCORE** | 100% | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** |

**Decision Criteria:**
- **Minimum viable**: Total score ≥ 70/100
- **Production ready**: Total score ≥ 80/100
- **Optimal**: Highest score among production-ready candidates

---

## Additional Testing Considerations

### OpenCode Integration Testing

For the selected model, perform additional validation:

1. **MCP Server Compatibility**
   - Test all MCP servers configured in `.mcp.json`
   - Verify tool calling works correctly
   - Validate parameter passing and error handling

2. **Skills from Each Collection**
   - `rh-sre`: Test remediation workflow
   - `ocp-admin`: Test cluster-creator, cluster-inventory
   - `rh-virt`: Test VM management skills
   - `rh-developer`: Test code generation skills

3. **Error Recovery**
   - Test model behavior when MCP server is unavailable
   - Verify graceful degradation
   - Check error message quality

4. **Concurrent Usage**
   - Multiple users executing skills simultaneously
   - Resource contention handling
   - Response consistency under load

---

## Documentation Requirements

For each tested model, document:

1. **Deployment Guide**
   - Exact manifest files used
   - vLLM configuration parameters
   - Resource requirements (CPU, RAM, GPU, storage)

2. **Performance Report**
   - Raw test results
   - Latency percentiles (p50, p95, p99)
   - Throughput measurements

3. **Quality Assessment**
   - Example inputs and outputs
   - Failure cases and limitations
   - Comparison to Claude Sonnet 4.5

4. **Operational Notes**
   - Deployment time and complexity
   - Update procedures
   - Troubleshooting guide

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1**: Infrastructure setup for all models | 1 week | All models deployed and accessible |
| **Phase 2**: Skills execution testing | 2 weeks | Completed test results for all skills |
| **Phase 3**: Comparative analysis | 3 days | Final recommendation document |
| **Phase 4**: Production deployment of selected model | 1 week | Production-ready LLM service |

**Total Estimated Time:** 4-5 weeks

---

## Success Metrics Summary

**Must Have:**
- ✅ At least 1 model scores ≥ 80/100 (production ready)
- ✅ Response latency < 5 seconds for 95% of queries
- ✅ Skills success rate > 95%
- ✅ No critical hallucinations in safety-critical tasks (CVE analysis, system commands)

**Nice to Have:**
- Hardware requirements fit within 4 GPUs (cost optimization)
- Context window ≥ 128K tokens (for complex workflows)
- Apache 2.0 or similarly permissive license
- Active community support and documentation

---

## References

- [Air-Gapped Deployment Guide](./README.md)
- [Context and Preparation](./extra_docs/context-and-preparation.md)
- [agentic-collections Repository](../)
- [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/)

---

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2026-04-08  
**Next Review:** After Phase 1 completion
