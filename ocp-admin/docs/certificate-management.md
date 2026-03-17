# Certificate Management

Certificate lifecycle management in OpenShift clusters.

---

## Certificate Types

### Cluster Certificates (Auto-Managed)

| Certificate | Purpose | Location | Expiration | Auto-Rotated |
|------------|---------|----------|------------|--------------|
| **API Server** | API access | kube-apiserver-certs | 30 days | Yes |
| **etcd** | etcd cluster communication | etcd-certs | 3 years | Yes |
| **Kubelet** | Node authentication | /var/lib/kubelet/pki/ | 1 year | Yes |
| **Ingress** | Default router HTTPS | openshift-ingress | 90 days | Yes (if Let's Encrypt) |

### User Certificates (Manual)

- **Client Certificates** (kubeconfig): 24 hours, auto-renewed on `oc` use
- **Custom Ingress**: User-provided, manual renewal required
- **Application Certs**: Managed by application teams

---

## Checking Certificate Expiration

**API Server**:
```bash
oc get secret -n openshift-kube-apiserver-operator kube-apiserver-to-kubelet-signer \
  -o jsonpath='{.metadata.annotations.auth\.openshift\.io/certificate-not-after}'
```

**Ingress**:
```bash
oc get secret -n openshift-ingress router-certs-default -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -enddate
```

**etcd** (from control plane node):
```bash
oc debug node/<master-node>
chroot /host
openssl x509 -in /etc/kubernetes/static-pod-resources/etcd-certs/etcd-serving-*.crt -noout -enddate
```

**Check via External Tool**:
```bash
echo | openssl s_client -connect api.<cluster>.<domain>:6443 2>/dev/null | \
  openssl x509 -noout -enddate
```

---

## Certificate Rotation

### Automatic Rotation

OpenShift automatically rotates:
- API server certificates (30 days before expiration)
- Kubelet certificates (approaching expiration)
- Service account tokens (pod lifecycle)

**No manual intervention required** for cluster-managed certificates.

### Manual Rotation Required

**Custom Ingress Certificate**:
```bash
# Update secret with new certificate
oc create secret tls router-certs-default \
  --cert=new-ingress.crt --key=new-ingress.key \
  -n openshift-ingress --dry-run=client -o yaml | oc replace -f -
```

**Custom Route Certificate**:
```bash
oc create secret tls my-route-cert --cert=route.crt --key=route.key -n myapp
```

**Force API Server Rotation** (if auto-rotation fails):
```bash
oc patch kubeapiserver/cluster --type=merge \
  -p '{"spec":{"forceRedeploymentReason":"cert-rotation-'"$(date +%s)"'"}}'
```

---

## Custom Certificate Authority

**Add Custom CA to Cluster**:
```bash
# Create ConfigMap with CA bundle
oc create configmap custom-ca --from-file=ca-bundle.crt=<ca-file> -n openshift-config

# Patch cluster proxy
oc patch proxy/cluster --type=merge -p '{"spec":{"trustedCA":{"name":"custom-ca"}}}'
```

**Custom API Server Certificate**:
```bash
# Create secret
oc create secret tls api-server-cert --cert=api.crt --key=api.key -n openshift-config

# Patch API server
oc patch apiserver cluster --type=merge -p \
  '{"spec":{"servingCerts":{"namedCertificates":[{"names":["api.<cluster>.<domain>"],"servingCertificate":{"name":"api-server-cert"}}]}}}'
```

---

## Certificate Signing Requests (CSR)

**Approve Pending CSRs** (nodes joining or cert renewal):
```bash
# List pending
oc get csr | grep Pending

# Approve specific CSR
oc adm certificate approve <csr-name>

# Approve all (use with caution in trusted environments)
oc get csr -o name | xargs oc adm certificate approve
```

---

## Monitoring

**Prometheus Alert**: `KubeClientCertificateExpiration`
```bash
oc get alerts | grep -i cert
```

**Custom Alert for <30 Days**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: certificate-expiration
  namespace: openshift-monitoring
spec:
  groups:
  - name: certificates
    rules:
    - alert: CertificateExpiringSoon
      expr: (openshift_certificate_not_after_seconds - time()) / 86400 < 30
      annotations:
        summary: "Certificate expires in < 30 days"
```

---

## Troubleshooting

### "x509: certificate signed by unknown authority"

**Resolution**: Trust cluster CA
```bash
oc get secret -n openshift-ingress router-ca -o jsonpath='{.data.tls\.crt}' | \
  base64 -d > cluster-ca.crt
sudo cp cluster-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust
```

### "certificate has expired"

**Resolution**: Force rotation
```bash
oc patch kubeapiserver/cluster --type=merge \
  -p '{"spec":{"forceRedeploymentReason":"cert-expired-'"$(date +%s)"'"}}'
```

### CSRs Not Auto-Approved

**Resolution**: Restart approver and manually approve
```bash
oc delete pod -l app=machine-approver -n openshift-cluster-machine-approver
oc get csr -o name | grep Pending | xargs oc adm certificate approve
```

---

## Best Practices

- ✅ Monitor certificate expiration (30-day warning)
- ✅ Trust automatic rotation for cluster certs
- ✅ Plan manual rotation for custom certs (90 days recommended)
- ✅ Use wildcard certs for ingress (`*.apps.<cluster>.<domain>`)
- ✅ Store private keys securely (never commit to Git)
- ✅ Use RSA 2048+ or ECDSA 256+ key sizes

---

## References

- [OpenShift Certificate Types](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/security_and_compliance/certificate-types-and-descriptions)
- [Replacing Ingress Certificate](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/security_and_compliance/cert-manager-operator-managing-certificates)
- [API Server Certificates](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/security_and_compliance/configuring-certificates)
- [Quick Reference](./quick-reference.md)
- [INDEX](./INDEX.md)

---

**Last Updated**: 2026-03-17
**OpenShift Version**: 4.18
