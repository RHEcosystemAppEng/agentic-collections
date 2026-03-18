# Official Red Hat Sources

All documentation in this collection is derived from or references official Red Hat and Ansible documentation. Content is used in accordance with Red Hat's documentation license (CC BY-SA 4.0).

## Primary Sources

### 1. Red Hat AAP 2.5 - Configuring Automation Execution: Security Best Practices (Ch. 15)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices

**Sections Used**:
- Sec. 15.1.2: Minimize administrative accounts
- Sec. 15.1.4: Remove user access to credentials
- Sec. 15.1.5: Enforce separation of duties
- Sec. 15.2.1: Use teams for role-based access
- Sec. 15.2.2: External authentication (LDAP, SAML, OAuth)

**Referenced By**: governance-readiness.md (Domains 3, 4, Bonus), execution-governance.md (secret scanning)

**Date Accessed**: 2026-02-20

---

### 2. Red Hat AAP 2.5 - Automation Controller User Guide: Workflows (Ch. 9)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-workflows

**Sections Used**:
- Workflow job templates
- Sec. 9.4: Workflow RBAC
- Approval nodes

**Referenced By**: governance-readiness.md (Domain 1), execution-governance.md

**Date Accessed**: 2026-02-20

---

### 3. Red Hat AAP 2.5 - Automation Controller User Guide: Notifications (Ch. 25)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-notifications

**Sections Used**:
- Notification templates
- Sec. 25.1: Notification inheritance hierarchy
- Notification types (Email, Slack, Webhook, PagerDuty)

**Referenced By**: governance-readiness.md (Domain 2)

**Date Accessed**: 2026-02-20

---

### 4. Red Hat AAP 2.5 - Automation Controller User Guide: RBAC (Ch. 4)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-role-based-access-controls

**Sections Used**:
- Role-based access controls
- Role definitions
- Team assignments

**Referenced By**: governance-readiness.md (Domain 3)

**Date Accessed**: 2026-02-20

---

### 5. Red Hat AAP 2.5 - Configuring Automation Execution: Instance Groups (Ch. 17)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-instance-groups

**Sections Used**:
- Instance groups for workload isolation
- max_forks configuration
- Policy settings

**Referenced By**: governance-readiness.md (Domain 6)

**Date Accessed**: 2026-02-20

---

### 6. Red Hat AAP 2.5 - Automation Controller User Guide: Activity Stream

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-activity-stream

**Sections Used**:
- Activity stream audit logging
- Event filtering

**Referenced By**: governance-readiness.md (Domain 7)

**Date Accessed**: 2026-02-20

---

### 7. Red Hat AAP 2.6 - Creating and Using Execution Environments

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html-single/creating_and_using_execution_environments/index

**Sections Used**:
- Custom EE creation
- Dependency pinning
- ansible-builder

**Referenced By**: governance-readiness.md (Domain 5), error-classification.md (EE issues)

**Date Accessed**: 2026-02-20

---

### 8. Red Hat AAP 2.6 - Hardening Guide

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/hardening_guide

**Sections Used**:
- Platform hardening
- Credential rotation
- Audit requirements

**Referenced By**: governance-readiness.md

**Date Accessed**: 2026-02-20

---

### 9. Red Hat AAP 2.6 - Troubleshooting Guide: Troubleshoot Jobs

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs

**Sections Used**:
- Job failure analysis
- Common job errors
- Event interpretation

**Referenced By**: job-troubleshooting.md, error-classification.md

**Date Accessed**: 2026-02-20

---

### 10. Red Hat AAP 2.5 - Automation Controller User Guide: Job Templates (Ch. 9)

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-job-templates

**Sections Used**:
- Job template configuration
- job_type (run/check)
- diff_mode, limit, extra_vars
- Job slicing
- Relaunch

**Referenced By**: execution-governance.md, job-troubleshooting.md

**Date Accessed**: 2026-02-20

---

### 11. Red Hat AAP 2.5 - Configuring Automation Execution: Controller Best Practices

**URL**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-best-practices

**Sections Used**:
- Inventory management
- Environment separation

**Referenced By**: execution-governance.md (risk classification)

**Date Accessed**: 2026-02-20

---

### 12. Ansible Playbook Guide: Check Mode

**URL**: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html

**Sections Used**:
- Check mode behavior
- diff mode
- Limitations (shell/command modules)

**Referenced By**: execution-governance.md (check mode section)

**Date Accessed**: 2026-02-20

---

### 13. Ansible Built-in Module Documentation

**URL**: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html

**Sections Used**:
- Module return values
- Error conditions
- Check mode behavior per module

**Referenced By**: error-classification.md

**Date Accessed**: 2026-02-20
