---
name: red-hat-diagnostics
description: Explain how to gather diagnostic information for Red Hat products (RHEL, OpenShift, Ansible Automation Platform, Satellite) to share with Red Hat Technical Support.
user_invocable: true
---

# Red Hat Diagnostic Information Gathering

Identify product and deployment type. If unclear, ask. Provide specific commands and upload instructions. If product not listed, use `WebFetch` on Red Hat docs -- `sos report` covers most RHEL-based products through plugins.

## RHEL

```bash
dnf install sos
sos report
```

Output: `.tar.xz` in `/var/tmp/`. Specific subsystems: `sos report --only-plugins networking,storage`

## OpenShift Container Platform (OCP)

```bash
oc adm must-gather --dest-dir ./must-gather
tar cvaf must-gather.tar.gz ./must-gather*/
```

Specific operators: `oc adm must-gather --image=<component-must-gather-image> --dest-dir ./must-gather`

If `registry.redhat.io` unavailable: `oc adm inspect <resource-type>/<resource-name>`

## Ansible Automation Platform (AAP)

Ask deployment type if not specified -- tool differs significantly.

VM/RPM-based: `sos report` (includes AAP plugins automatically)

Containerized:
```bash
ansible-playbook -i <path_to_inventory> ansible.containerized_installer.log_gathering \
  -e 'target_sos_directory=/tmp/aap-logs' \
  -e 'case_number=<your_case_number>' \
  -e 'clean=true' \
  -e 'upload=true'
```
Omit `upload=true` to collect locally first.

OCP-based (Operator):
```bash
# AAP 2.6
oc adm must-gather \
  --image=registry.redhat.io/ansible-automation-platform-26/aap-must-gather-rhel9 \
  --dest-dir ./must-gather \
  -- /usr/bin/ns-gather <namespace>

# AAP 2.5
oc adm must-gather \
  --image=registry.redhat.io/ansible-automation-platform-25/aap-must-gather-rhel8 \
  --dest-dir ./must-gather \
  -- /usr/bin/ns-gather <namespace>
```
Then: `tar cvaf aap-must-gather.tar.gz ./must-gather*/`

## Red Hat Satellite

```bash
sos report
foreman-debug -d /tmp/foreman-debug
```

`sos report` includes the satellite plugin automatically. `foreman-debug` provides deeper Foreman/Katello data.

## Sharing with Red Hat Support

Attach archives at [access.redhat.com/support](https://access.redhat.com/support). Large files: `ftp://dropbox.redhat.com` or Customer Portal file upload API.

## Reference Docs

- AAP troubleshooting: `WebFetch` -> `https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/diagnosing-the-problem`
- OCP must-gather: `WebFetch` -> `https://docs.redhat.com/en/documentation/openshift_container_platform/4.17/html/support/gathering-cluster-data`
- sos tool: `WebFetch` -> `https://access.redhat.com/solutions/3592`
