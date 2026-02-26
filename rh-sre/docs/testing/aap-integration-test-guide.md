---
title: AAP Integration Test Guide
category: testing
sources:
  - title: Internal Testing Documentation
    date_accessed: 2024-01-20
tags: [testing, aap-integration, workflow-verification, remediation-testing]
semantic_keywords: [aap integration testing, workflow verification, remediation test]
use_cases: [remediator, playbook-executor]
related_docs: [aap-job-execution.md, playbook-integration-aap.md]
last_updated: 2024-01-20
---

# AAP Integration Test Guide

## Overview

This guide provides a comprehensive testing plan for the AAP MCP integration, covering the complete CVE remediation workflow from analysis through execution to verification.

## Prerequisites for Testing

### Required Setup

1. **AAP Environment**:
   - AAP 2.4+ instance accessible
   - Valid API token with appropriate permissions
   - At least one project configured
   - At least one inventory with test systems
   - At least one job template (or ability to create one)

2. **Environment Variables**:
   ```bash
   export AAP_MCP_SERVER="https://your-aap-mcp-endpoint.com"
   export AAP_API_TOKEN="your-api-token"
   ```

3. **Test Systems**:
   - At least 2-3 RHEL systems in AAP inventory
   - Systems registered with Red Hat Lightspeed
   - Systems have known CVEs for testing
   - SSH access configured with credentials in AAP

4. **MCP Configuration**:
   - `rh-sre/.mcp.json` configured with AAP MCP servers
   - `lightspeed-mcp` configured and working
   - All environment variables set

### Verification Checklist

Before starting tests, verify:

- [ ] AAP Web UI accessible (your AAP instance URL)
- [ ] Can log in with your credentials
- [ ] API token has been generated
- [ ] Environment variables are set (run: `env | grep AAP`)
- [ ] Test systems visible in AAP inventory
- [ ] Test systems have CVEs in Red Hat Lightspeed
- [ ] Git repository available for playbook storage

## Test Plan Structure

```
Test Phase 1: Component Testing
├─ Test 1.1: AAP MCP Validator
├─ Test 1.2: Job Template Lister
├─ Test 1.3: Playbook Generator
└─ Test 1.4: Inventory Access

Test Phase 2: Integration Testing
├─ Test 2.1: Template Selection Workflow
├─ Test 2.2: Dry-Run Execution
├─ Test 2.3: Production Execution
└─ Test 2.4: Error Handling

Test Phase 3: End-to-End Testing
├─ Test 3.1: Full Remediator Workflow
├─ Test 3.2: Multi-CVE Remediation
└─ Test 3.3: Partial Failure Recovery

Test Phase 4: Performance Testing
└─ Test 4.1: Large-Scale Execution
```

## Test Phase 1: Component Testing

### Test 1.1: AAP MCP Validator

**Objective**: Verify AAP MCP server connectivity and resource availability.

**Steps**:
1. Invoke the mcp-aap-validator skill
2. Observe validation checks
3. Confirm all checks pass

**Expected Results**:
```
✓ AAP MCP Validation: PASSED

Configuration:
✓ MCP server aap-mcp-job-management configured
✓ MCP server aap-mcp-inventory-management configured
✓ Environment variable AAP_MCP_SERVER is set
✓ Environment variable AAP_API_TOKEN is set
✓ Job management server connectivity verified
✓ Inventory management server connectivity verified

Resources:
✓ Found N job template(s) available
✓ Found M inventory/inventories available

Ready to execute AAP operations.
```

**Pass Criteria**:
- All configuration checks pass
- Both MCP servers connect successfully
- At least 1 job template found
- At least 1 inventory found

**Troubleshooting**:
- If fails: Review error message and fix configuration
- If partial: Note warnings but may proceed if resources exist
- If connection fails: Check AAP server status and credentials

### Test 1.2: Job Template Lister

**Objective**: Verify ability to list and filter job templates.

**Test Command**: Use `job_templates_list` MCP tool via skill

**Steps**:
1. Request list of all job templates
2. Verify response contains expected templates
3. Note template IDs for later tests

**Expected Results**:
- List of templates with IDs, names, projects, inventories
- At least 1 template suitable for remediation

**Pass Criteria**:
- Tool returns valid response
- Template data includes required fields
- Can identify suitable template for testing

### Test 1.3: Playbook Generator

**Objective**: Verify playbook generation from CVE data.

**Steps**:
1. Invoke playbook-generator skill with a known CVE
2. Review generated playbook
3. Verify playbook has required sections

**Test Input**:
- CVE ID: Use a real CVE affecting your test systems
- Target systems: Your test system UUIDs

**Expected Results**:
- Valid Ansible YAML playbook generated
- Includes: pre-flight checks, package updates, service restarts
- Follows Red Hat best practices
- Has proper error handling

**Pass Criteria**:
- Playbook is syntactically valid YAML
- Contains all remediation tasks
- Includes backup/rollback steps
- Has audit logging

### Test 1.4: Inventory Access

**Objective**: Verify ability to query AAP inventories and hosts.

**Test Command**: Use `inventories_list` and `hosts_list` MCP tools

**Steps**:
1. List all inventories
2. Select test inventory
3. List hosts in that inventory
4. Verify test systems are present

**Expected Results**:
- Inventory list returned
- Can query hosts within inventory
- Test systems visible with correct metadata

**Pass Criteria**:
- At least 1 inventory returned
- Hosts query succeeds
- Test systems found in inventory

## Test Phase 2: Integration Testing

### Test 2.1: Template Selection Workflow

**Objective**: Test the template selection and creation workflow.

**Scenario A: Existing Template**

**Steps**:
1. Invoke playbook-executor skill
2. Skill lists available templates
3. Select an existing compatible template
4. Verify selection is accepted

**Expected Results**:
```
Found N compatible job template(s):

1. "CVE Remediation Template" (ID: 10)
   - Inventory: Production Servers (1)
   - Project: Remediation Playbooks (5)
   - Credentials: ✓ Configured

Select template number or "create" for new: 1

✓ Using template: CVE Remediation Template (ID: 10)
```

**Pass Criteria**:
- Templates listed successfully
- User can select a template
- Selection is confirmed

**Scenario B: Create New Template**

**Steps**:
1. Invoke playbook-executor skill
2. Choose "create" option
3. Follow template creation guidance
4. Verify template appears in AAP

**Expected Results**:
- User guided through Web UI creation
- Template created with correct settings
- Template visible in `job_templates_list`

**Pass Criteria**:
- Guidance is clear and actionable
- Template created successfully
- Template has required configuration

### Test 2.2: Dry-Run Execution

**Objective**: Test check mode (dry-run) execution.

**Steps**:
1. Generate a remediation playbook
2. Select job template
3. Choose "yes" when asked about dry-run
4. Wait for dry-run to complete
5. Review dry-run results

**Expected Results**:
```
⏳ Dry-run in progress...

Job ID: 1234
Status: running

# Dry-Run Results

## Job Summary
**Job ID**: 1234
**Status**: ✓ Successful (Check Mode)
**Duration**: 2m 15s

## Simulated Changes
| Host | Would Change | OK | Failed | Status |
|------|--------------|-----|--------|--------|
| test-01 | 2 | 6 | 0 | ✓ Ready |
| test-02 | 2 | 6 | 0 | ✓ Ready |

✓ No errors detected in dry-run
```

**Pass Criteria**:
- Job launches with `job_type: "check"`
- Execution completes successfully
- Results show "would change" counts
- No actual changes made to systems
- User asked to proceed with actual execution

### Test 2.3: Production Execution

**Objective**: Test actual playbook execution (run mode).

**Steps**:
1. After successful dry-run, approve actual execution
2. Monitor execution progress
3. Wait for completion
4. Review execution report

**Expected Results**:
```
⏳ Execution in progress...

Job ID: 1235
Status: running

# Playbook Execution Report

## Job Summary
**Job ID**: 1235
**Status**: ✅ Successful
**Duration**: 3m 45s

## Per-Host Results
| Host | OK | Changed | Failed | Unreachable | Status |
|------|-----|---------|--------|-------------|--------|
| test-01 | 6 | 2 | 0 | 0 | ✅ Success |
| test-02 | 6 | 2 | 0 | 0 | ✅ Success |

**Summary**: 2 of 2 hosts successfully remediated

## Next Steps
☐ Verify remediation with remediation-verifier skill
```

**Pass Criteria**:
- Job launches with `job_type: "run"`
- Real-time progress displayed
- Execution completes successfully
- All hosts show success status
- Comprehensive report generated
- AAP URL provided for detailed view

### Test 2.4: Error Handling

**Objective**: Test error handling and recovery.

**Scenario A: Partial Host Failure**

**Setup**:
- Use 3 test systems
- Cause failure on 1 system (e.g., remove package, stop service)

**Steps**:
1. Execute remediation playbook
2. Observe partial failure
3. Review error report
4. Choose to relaunch for failed host

**Expected Results**:
```
⚠️ Playbook Execution Completed with Failures

Job ID: 1236
Systems Remediated: 2 of 3
Failed Systems: test-03

## Failed Tasks Details
**Host**: test-03
**Task**: Update package httpd
**Error**: "No package httpd available"
**Recommendation**: Check repository configuration

Would you like to:
1. Relaunch for failed host only
2. Fix issues manually and relaunch
```

**Pass Criteria**:
- Failure detected and reported
- Specific error message provided
- Troubleshooting guidance given
- Relaunch option offered
- Can successfully relaunch for failed host only

**Scenario B: Connection Failure**

**Setup**:
- Block SSH to one test system (firewall rule)

**Steps**:
1. Execute remediation playbook
2. Observe connection failure
3. Review error categorization

**Expected Results**:
```
❌ Host test-02: unreachable

**Error Category**: Connection Failure

**Troubleshooting**:
1. Check SSH service: systemctl status sshd
2. Verify firewall: firewall-cmd --list-all
3. Test connectivity: ping test-02
```

**Pass Criteria**:
- Connection failure detected
- Categorized as connection error
- Specific troubleshooting provided

## Test Phase 3: End-to-End Testing

### Test 3.1: Full Remediator Workflow

**Objective**: Test complete CVE remediation from analysis to verification.

**Steps**:
1. **Invoke remediator agent** with a known CVE
2. **Impact Analysis**: Review CVE risk assessment
3. **CVE Validation**: Confirm CVE is valid and has remediation
4. **System Context**: Review affected systems and strategy
5. **Playbook Generation**: Review generated playbook, approve
6. **Dry-Run**: Run check mode, review results, approve production
7. **Execution**: Monitor real execution, review report
8. **Verification**: Verify CVE status updated in Lightspeed

**Test Input**:
```
User: "Remediate CVE-YYYY-NNNNN on my test systems"
```

**Expected Flow**:
1. Agent analyzes CVE impact
2. Agent validates CVE exists
3. Agent gathers system context
4. Agent generates playbook
5. Agent offers dry-run → User approves
6. Agent shows dry-run results
7. Agent asks for production execution → User approves
8. Agent executes playbook
9. Agent reports success
10. Agent suggests verification
11. User invokes remediation-verifier
12. Verifier confirms CVE resolved

**Pass Criteria**:
- All steps complete without errors
- User prompted at appropriate points
- Dry-run shows simulated changes
- Production execution succeeds
- CVE status updated in Lightspeed
- Comprehensive report at each stage

**Timeline**: ~10-15 minutes for full workflow

### Test 3.2: Multi-CVE Remediation

**Objective**: Test batch remediation of multiple CVEs.

**Steps**:
1. Invoke remediator agent with 2-3 CVEs
2. Verify agent handles batch processing
3. Confirm single consolidated playbook generated
4. Execute remediation
5. Verify all CVEs resolved

**Test Input**:
```
User: "Remediate CVE-2024-1234, CVE-2024-5678, CVE-2024-9012"
```

**Expected Results**:
- Agent processes all CVEs
- Consolidated playbook with all fixes
- Single job execution covering all changes
- Report shows results per CVE

**Pass Criteria**:
- Batch processing works correctly
- Playbook includes all remediation tasks
- Execution handles multiple changes
- Verification confirms all CVEs resolved

### Test 3.3: Partial Failure Recovery

**Objective**: Test recovery from partial failures.

**Scenario**: 5 test systems, 2 fail during execution

**Steps**:
1. Execute remediation on 5 systems
2. Observe 2 failures
3. Review error analysis
4. Fix issues on failed systems
5. Relaunch for failed systems only
6. Verify all systems eventually succeed

**Expected Results**:
- Partial success reported (3 of 5)
- Failed systems identified
- Relaunch targets only failed systems
- Second execution succeeds
- Final report shows 5 of 5 success

**Pass Criteria**:
- Partial failure handled gracefully
- Relaunch doesn't re-run successful hosts
- Ultimate success achieved
- Audit trail shows full history

## Test Phase 4: Performance Testing

### Test 4.1: Large-Scale Execution

**Objective**: Test performance with larger number of systems.

**Setup**:
- Use 20+ systems in inventory
- Single CVE affecting all systems

**Steps**:
1. Execute remediation targeting 20+ systems
2. Monitor execution time
3. Review AAP resource usage
4. Verify all systems succeed

**Expected Results**:
- Execution completes in reasonable time
- Progress monitoring works at scale
- All systems remediated successfully
- Report generated efficiently

**Pass Criteria**:
- Job completes within expected timeframe
- No timeouts or performance degradation
- Monitoring provides useful progress updates
- Final report is comprehensive

**Performance Benchmarks**:
- 10 systems: ~5-10 minutes
- 20 systems: ~10-20 minutes
- 50 systems: ~20-40 minutes
(Times vary based on package size and network)

## Test Reporting Template

### Test Execution Report

```markdown
# AAP Integration Test Report

**Date**: YYYY-MM-DD
**Tester**: [Name]
**Environment**: [AAP Server URL]
**Test Phase**: [1-4]

## Summary
- Tests Run: N
- Tests Passed: N
- Tests Failed: N
- Pass Rate: NN%

## Phase 1: Component Testing
- [ ] Test 1.1: AAP MCP Validator - PASS/FAIL
- [ ] Test 1.2: Job Template Lister - PASS/FAIL
- [ ] Test 1.3: Playbook Generator - PASS/FAIL
- [ ] Test 1.4: Inventory Access - PASS/FAIL

## Phase 2: Integration Testing
- [ ] Test 2.1: Template Selection - PASS/FAIL
- [ ] Test 2.2: Dry-Run Execution - PASS/FAIL
- [ ] Test 2.3: Production Execution - PASS/FAIL
- [ ] Test 2.4: Error Handling - PASS/FAIL

## Phase 3: End-to-End Testing
- [ ] Test 3.1: Full Remediator Workflow - PASS/FAIL
- [ ] Test 3.2: Multi-CVE Remediation - PASS/FAIL
- [ ] Test 3.3: Partial Failure Recovery - PASS/FAIL

## Phase 4: Performance Testing
- [ ] Test 4.1: Large-Scale Execution - PASS/FAIL

## Issues Found
1. [Issue description] - Severity: High/Medium/Low
2. [Issue description] - Severity: High/Medium/Low

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Sign-Off
Tested by: [Name]
Approved by: [Name]
Date: YYYY-MM-DD
```

## Common Issues and Solutions

### Issue: "AAP MCP Validation Failed"

**Symptoms**: Validation fails with connection errors

**Solutions**:
1. Verify `AAP_MCP_SERVER` environment variable is correct (must point to the MCP endpoint of the AAP server)
2. Check API token is valid and not expired
3. Ensure AAP server is accessible from your network
4. Review AAP MCP server logs for errors

### Issue: "No Job Templates Found"

**Symptoms**: Validation passes but no templates available

**Solutions**:
1. Create job template via AAP Web UI
2. Ensure project is synced and contains playbooks
3. Verify inventory is configured
4. Check credentials are attached to template

### Issue: "Dry-Run Shows No Changes"

**Symptoms**: Dry-run completes but reports 0 changes

**Solutions**:
1. Verify systems actually need remediation
2. Check playbook targets correct hosts
3. Ensure package names are correct
4. Review playbook conditionals (when clauses)

### Issue: "Execution Hangs"

**Symptoms**: Job starts but never completes

**Solutions**:
1. Check AAP Web UI for job status
2. Review job output for stuck tasks
3. Verify systems are reachable
4. Increase job timeout in template settings

## Sign-Off Criteria

Before considering AAP integration complete, verify:

- [ ] All Phase 1 tests pass
- [ ] All Phase 2 tests pass
- [ ] At least Test 3.1 passes (full workflow)
- [ ] No critical issues remain
- [ ] Documentation is accurate
- [ ] Examples work as described
- [ ] Performance is acceptable

## Next Steps After Testing

1. **Document Results**: Complete test report template
2. **Fix Issues**: Address any failures found
3. **Update Documentation**: Correct any inaccuracies
4. **User Acceptance**: Have users test workflow
5. **Production Rollout**: Enable for production use

## Related Documentation

- [AAP Job Execution Guide](../ansible/aap-job-execution.md)
- [Playbook Integration with AAP](../ansible/playbook-integration-aap.md)
- [CVE Remediation Templates](../ansible/cve-remediation-templates.md)
