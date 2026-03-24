#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Creation Plan

## Target: test-vm in vm-testing

### VirtualMachine Specification

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: test-vm
  namespace: vm-testing
spec:
  runStrategy: Always
  template:
    spec:
      domain:
        cpu:
          cores: 2
        resources:
          requests:
            memory: 4Gi
        devices:
          disks:
          - name: rootdisk
            disk:
              bus: virtio
      volumes:
      - name: rootdisk
        dataVolume:
          name: test-vm-rootdisk
  dataVolumeTemplates:
  - metadata:
      name: test-vm-rootdisk
    spec:
      source:
        registry:
          url: docker://registry.redhat.io/rhel9/rhel-guest-image:latest
      storage:
        resources:
          requests:
            storage: 30Gi
```

### Storage Configuration
- Using DataVolume with registry source for RHEL 9 guest image
- DataVolume automatically provisions PVC via CDI
- Default StorageClass used (annotated with storageclass.kubernetes.io/is-default-class)

### VM Lifecycle
- `runStrategy: Always` ensures VM starts automatically and restarts on failure
- Alternative: `running: true` for simple start, but runStrategy provides more control
- Instance type/size: small (2 vCPU, 4Gi) for testing purposes

### Default Credentials
- RHEL 9 guest image: requires cloud-init or SSH key for access

### Prerequisite Checks
- Verify namespace vm-testing exists
- Check default StorageClass is configured (annotation storageclass.kubernetes.io/is-default-class)
- Verify KubeVirt operator is running
- Ensure sufficient node resources (2 CPU, 4Gi memory)

### Error Handling (from vm-create skill)
- **ErrorUnschedulable**: Consult scheduling-errors.md; add tolerations via oc patch if node taints block scheduling
- **ErrorDataVolumeNotReady**: Storage provisioning; verify StorageClass, check CDI/DataVolume status
- Access VM: `virtctl console test-vm -n vm-testing` or VNC via OpenShift Console

REPORT_EOF
