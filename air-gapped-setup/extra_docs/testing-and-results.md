# Part 3: Testing and Results

Validate your deployment, configure OpenCode, and ensure production readiness.

---

**📚 Documentation Navigation:**
- **[← Previous: Installation Guide](./installation.md)**
- **[Back to Index](./index.md)**

---

## Table of Contents

1. [OpenCode Configuration](#10-opencode-configuration)
2. [Validation and Testing](#11-validation-and-testing)
3. [Security Considerations](#12-security-considerations)
4. [Troubleshooting](#13-troubleshooting)
5. [References](#14-references)

---

## Prerequisites Checklist

Before proceeding, ensure you have completed:

- [ ] Completed Part 1: Context and Preparation
- [ ] Completed Part 2: Installation Guide
- [ ] Model InferenceService is Running
- [ ] Route URL is accessible
- [ ] Basic curl test to model endpoint succeeded

**Not ready?** Go back to [Installation Guide](./installation.md)

---

## 10. OpenCode Configuration

### 10.1 Prerequisites

```bash
# Verify OpenCode installation
claude --version

# If not installed:
npm install -g @anthropic-ai/claude-code
```

### 9.2 Configure OpenCode to Use Local Model

#### Step 1: Create Configuration File

```bash
# Create configuration directory
mkdir -p ~/.config/claude-code

# Create custom configuration
cat > ~/.config/claude-code/config.json <<EOF
{
  "providers": [
    {
      "name": "llama-405b-local",
      "type": "openai-compatible",
      "baseURL": "https://$ROUTE_URL/v1",
      "apiKey": "not-required",
      "models": [
        {
          "id": "llama-3.1-405b-fp8",
          "name": "Llama 3.1 405B (Local)",
          "maxTokens": 16384,
          "contextWindow": 128000
        }
      ],
      "default": true
    }
  ],
  "defaultModel": "llama-3.1-405b-fp8",
  "timeout": 120000,
  "verify_ssl": false
}
EOF
```

**Note**: `verify_ssl: false` is temporary for development. In production, configure valid certificates.

#### Step 2: Configure Environment Variables (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_CODE_PROVIDER="llama-405b-local"
export CLAUDE_CODE_MODEL="llama-3.1-405b-fp8"
export CLAUDE_CODE_BASE_URL="https://$ROUTE_URL/v1"
```

### 9.3 Verify Connection

```bash
# Connectivity test
claude chat "Hello, can you confirm you're running locally on OpenShift?"

# Technical capabilities test
claude chat "List the main components of Red Hat OpenShift AI"

# Skill execution test (example)
claude exec "/health-check" --project ./agentic-collections/rh-sre
```

### 9.4 Configure OpenCode for the Repository

#### Step 1: Navigate to Repository

```bash
cd ~/agentic-collections
```

#### Step 2: Initialize OpenCode in Project

```bash
# Initialize project configuration
claude init

# Select provider: llama-405b-local
# Select model: llama-3.1-405b-fp8
```

#### Step 3: Test Repository Skills

```bash
# Test rh-sre skill
claude exec "/cve-impact" --cve CVE-2024-1234

# Test ocp-admin skill
claude exec "/cluster-report"

# Test rh-virt skill
claude exec "/vm-status"
```

---

## 11. Validation and Testing

### 11.1 Performance Testing

#### Latency Benchmark

```bash
# Benchmark script
cat > benchmark-latency.sh <<'EOF'
#!/bin/bash
ENDPOINT="https://$ROUTE_URL/v1/completions"

for i in {1..10}; do
  START=$(date +%s.%N)
  
  curl -k -s "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "llama-3.1-405b-fp8",
      "prompt": "Explain Kubernetes pods in one sentence.",
      "max_tokens": 100,
      "temperature": 0.7
    }' > /dev/null
  
  END=$(date +%s.%N)
  DURATION=$(echo "$END - $START" | bc)
  echo "Request $i: ${DURATION}s"
done
EOF

chmod +x benchmark-latency.sh
./benchmark-latency.sh
```

**Expected results**: 2-5 seconds per request with FP8 and 8x H100.

#### Throughput Test

```bash
# Test with multiple concurrent requests
cat > benchmark-throughput.sh <<'EOF'
#!/bin/bash
ENDPOINT="https://$ROUTE_URL/v1/completions"
CONCURRENT=4

parallel -j $CONCURRENT "curl -k -s '$ENDPOINT' \
  -H 'Content-Type: application/json' \
  -d '{
    \"model\": \"llama-3.1-405b-fp8\",
    \"prompt\": \"Test prompt {}\",
    \"max_tokens\": 100
  }' | jq -r '.choices[0].text'" ::: {1..20}
EOF

chmod +x benchmark-throughput.sh
./benchmark-throughput.sh
```

### 10.2 Complete Skills Testing

#### Test 1: rh-sre/cve-impact

```bash
claude chat "Using the /cve-impact skill, analyze CVE-2024-3094 (xz backdoor)"
```

**Validation**: Should generate complete impact analysis, severity, and recommendations.

#### Test 2: ocp-admin/cluster-report

```bash
claude chat "Generate a cluster health report using /cluster-report"
```

**Validation**: Should connect to cluster, collect metrics, and generate report.

#### Test 3: rh-virt/vm-deploy

```bash
claude chat "Using /vm-deploy, describe the steps to deploy a RHEL 9 VM on OpenShift Virtualization"
```

**Validation**: Should generate valid YAML and correct oc commands.

### 10.3 Long Context Test

```bash
# Test with skill requiring lots of context
claude chat "Analyze all SKILL.md files in rh-sre/skills/ and summarize their purposes"
```

**Validation**: Should process multiple files (>50K tokens) without truncating.

### 10.4 System Monitoring

#### GPU Utilization

```bash
# Inside vLLM pod
oc exec -n llama-inference -it $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Should show ~95% GPU memory utilization across 8 GPUs
```

#### vLLM Metrics

```bash
# vLLM metrics (if exposed)
curl -k https://$ROUTE_URL/metrics

# Key metrics:
# - vllm:num_requests_running
# - vllm:num_requests_waiting
# - vllm:gpu_cache_usage_perc
# - vllm:time_to_first_token_seconds
# - vllm:time_per_output_token_seconds
```

---

## 12. Security Considerations

### 12.1 Authentication and Authorization

#### Option 1: API Keys (Development)

```bash
# Create secret with API key
oc create secret generic llama-api-keys \
  -n llama-inference \
  --from-literal=api-key-1=$(openssl rand -hex 32)

# Modify InferenceService to require API key
# (Requires configuring vLLM with authentication middleware)
```

#### Option 2: OAuth2 with OpenShift OAuth (Recommended)

```bash
# Annotate service to use OAuth
oc annotate route llama-405b-route \
  -n llama-inference \
  haproxy.router.openshift.io/hsts_header="max-age=31536000;includeSubDomains;preload"

# Create ServiceAccount for OAuth
oc create sa llama-client -n llama-inference

# Grant permissions
oc adm policy add-role-to-user view system:serviceaccount:llama-inference:llama-client

# Get token
SA_TOKEN=$(oc sa get-token llama-client -n llama-inference)

# Use token in requests
curl -k -H "Authorization: Bearer $SA_TOKEN" \
  https://$ROUTE_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-405b-fp8", "prompt": "Test"}'
```

### 11.2 Network Policies

```bash
cat <<EOF | oc apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llama-inference-netpol
  namespace: llama-inference
spec:
  podSelector:
    matchLabels:
      serving.kserve.io/inferenceservice: llama-405b
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: openshift-ingress
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: openshift-apiserver
      ports:
        - protocol: TCP
          port: 443
    - to:
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
EOF
```

### 11.3 TLS Certificates

#### Option 1: Let's Encrypt (requires public DNS)

```bash
# Install cert-manager
oc apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | oc apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: openshift-default
EOF

# Annotate route to use cert-manager
oc annotate route llama-405b-route \
  -n llama-inference \
  cert-manager.io/issuer-kind=ClusterIssuer \
  cert-manager.io/issuer-name=letsencrypt-prod
```

#### Option 2: Internal Certificate (Recommended for AirGapped)

```bash
# Generate internal CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
  -out ca.crt -subj "/CN=Internal CA"

# Generate certificate for the service
openssl genrsa -out llama-tls.key 2048
openssl req -new -key llama-tls.key -out llama-tls.csr \
  -subj "/CN=$ROUTE_URL"

openssl x509 -req -in llama-tls.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out llama-tls.crt -days 365 -sha256

# Create secret with certificate
oc create secret tls llama-tls-cert \
  -n llama-inference \
  --cert=llama-tls.crt \
  --key=llama-tls.key

# Modify route to use certificate
oc patch route llama-405b-route -n llama-inference \
  -p '{"spec":{"tls":{"certificate":"'"$(cat llama-tls.crt)"'","key":"'"$(cat llama-tls.key)"'"}}}'
```

### 11.4 Audit Logging

```bash
# Enable audit logging in OpenShift
cat <<EOF | oc apply -f -
apiVersion: config.openshift.io/v1
kind: APIServer
metadata:
  name: cluster
spec:
  audit:
    profile: WriteRequestBodies
EOF

# View audit logs
oc adm node-logs --role=master --path=openshift-apiserver/audit.log
```

---

## 13. Troubleshooting

### 13.1 Common Issues

#### Issue 1: Pod Won't Start - OOMKilled

**Symptom**:
```bash
oc get pods -n llama-inference
# NAME                          READY   STATUS      RESTARTS
# llama-405b-predictor-...      0/1     OOMKilled   3
```

**Solution**:
```bash
# Increase pod memory
oc edit inferenceservice llama-405b -n llama-inference

# Change:
resources:
  limits:
    memory: 600Gi  # Increase from 400Gi to 600Gi
```

#### Issue 2: GPUs Not Detected

**Symptom**:
```bash
oc logs -n llama-inference llama-405b-predictor-...
# Error: No GPUs found
```

**Solution**:
```bash
# Verify GPU operator
oc get pods -n nvidia-gpu-operator

# Restart device plugin
oc delete pod -n nvidia-gpu-operator -l app=nvidia-device-plugin-daemonset

# Verify node has GPUs
oc describe node $GPU_NODE | grep nvidia.com/gpu
```

#### Issue 3: Model Won't Download from S3

**Symptom**:
```bash
oc logs -n llama-inference llama-405b-predictor-...
# Error downloading model from S3: Access Denied
```

**Solution**:
```bash
# Verify S3 credentials
oc get secret aws-connection-llama-models -n llama-inference -o yaml

# Test access manually
oc run -it --rm debug --image=amazon/aws-cli --restart=Never -- \
  aws s3 ls s3://airgapped-llm-models/llama-3.1-405b-fp8/ \
  --region us-east-1
```

#### Issue 4: High Latency (>10s)

**Diagnosis**:
```bash
# Verify GPU utilization
oc exec -n llama-inference $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Review tensor parallelism configuration
oc get inferenceservice llama-405b -n llama-inference -o yaml | grep tensor-parallel-size

# Check vLLM logs
oc logs -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b --tail=100
```

**Solution**:
```bash
# Adjust vLLM parameters in ServingRuntime
oc edit servingruntime vllm-nvidia-gpu-runtime -n redhat-ods-applications

# Optimize:
args:
  - --max-model-len
  - "8192"  # Reduce if you don't need ultra-long context
  - --gpu-memory-utilization
  - "0.98"  # Increase utilization
```

### 12.2 Advanced Debugging

#### Access vLLM Pod

```bash
# Shell into pod
oc exec -it -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- /bin/bash

# Verify loaded model
ls -lh /mnt/models/

# Verify GPUs from inside
nvidia-smi

# View Python processes
ps aux | grep vllm
```

#### Capture Traffic

```bash
# Install tcpdump in pod (for temporary debugging)
oc exec -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- apt-get update && apt-get install -y tcpdump

# Capture requests
oc exec -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- tcpdump -i any -s 0 -w /tmp/traffic.pcap port 8080

# Copy capture
oc cp llama-inference/$(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o jsonpath='{.items[0].metadata.name}'):/tmp/traffic.pcap ./traffic.pcap
```

### 12.3 Logs and Metrics

#### Centralize Logs

```bash
# View all llama-405b related logs
oc logs -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b --tail=1000

# Follow logs in real-time
oc logs -f -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b

# Export logs for analysis
oc logs -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b --since=1h > llama-logs.txt
```

#### Prometheus Metrics (if enabled)

```bash
# Verify ServiceMonitor
oc get servicemonitor -n llama-inference

# Query in Prometheus
# vllm_request_duration_seconds
# vllm_num_requests_running
# vllm_gpu_cache_usage_perc
```

---

## 14. References

### 14.1 Official Documentation

- [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.20/)
- [vLLM Official Documentation](https://docs.vllm.ai/)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-405B-Instruct)
- [AWS P5 Instances](https://aws.amazon.com/ec2/instance-types/p5/)
- [NVIDIA GPU Operator Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [KServe Documentation](https://kserve.github.io/website/)

### 13.2 Technical Articles and Blogs

- [Installing and Deploying LLaMA 3.1 405B Into Production](https://nlpcloud.com/installing-deploying-llama-3-1-405b-into-production-on-gcp-compute-engine.html)
- [Llama 3.1 Support in vLLM](https://blog.vllm.ai/2024/07/23/llama31.html)
- [Serve and Benchmark Models with vLLM on OpenShift](https://developers.redhat.com/articles/2026/03/03/serve-and-benchmark-prithvi-models-vllm-openshift)
- [How to Deploy Language Models with Red Hat OpenShift AI](https://developers.redhat.com/articles/2025/09/10/how-deploy-language-models-red-hat-openshift-ai)
- [Autoscaling vLLM with OpenShift AI](https://developers.redhat.com/articles/2025/10/02/autoscaling-vllm-openshift-ai)

### 13.3 Code Repositories

- [eartvit/llm-on-ocp](https://github.com/eartvit/llm-on-ocp) - Deploy LLM on OpenShift
- [KempnerInstitute/distributed-inference-vllm](https://github.com/KempnerInstitute/distributed-inference-vllm) - Distributed vLLM inference

### 13.4 Mentioned Tools

- **OpenCode**: https://claude.ai/code
- **vLLM**: https://github.com/vllm-project/vllm
- **Hugging Face Hub**: https://huggingface.co/
- **AWS CLI**: https://aws.amazon.com/cli/
- **oc (OpenShift CLI)**: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html

---

## Appendices

### Appendix A: Useful Commands Summary

```bash
# Verify cluster status
oc get nodes
oc get pods -A | grep -i gpu

# Verify RHOAI
oc get inferenceservice -A
oc get servingruntimes -A

# Model monitoring
oc logs -f -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b
oc exec -n llama-inference $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Test endpoint
ROUTE_URL=$(oc get route llama-405b-route -n llama-inference -o jsonpath='{.spec.host}')
curl -k https://$ROUTE_URL/health

# OpenCode
claude chat "Test message"
claude exec "/cluster-report"
```

### Appendix B: Cost Estimation

| Component | Monthly Cost (USD) |
|-----------|-------------------|
| AWS p5.48xlarge (24/7) | ~$70,800 |
| AWS p5.48xlarge (8h/day weekdays) | ~$13,400 |
| EBS Storage (2TB gp3) | ~$160 |
| S3 Storage (1TB) | ~$23 |
| Data Transfer | Variable |
| **Total (8h/day)** | **~$13,583/month** |

**Optimizations**:
- Use Spot Instances (up to 70% discount)
- Use Reserved Instances (up to 45% discount)
- Shutdown instance outside business hours

### Appendix C: Deployment Checklist

- [ ] OpenShift 4.20+ cluster installed
- [ ] AWS p5.48xlarge instance created
- [ ] GPU node added to cluster
- [ ] Node Feature Discovery Operator installed
- [ ] NVIDIA GPU Operator installed
- [ ] 8 H100 GPUs detected and available
- [ ] Red Hat OpenShift AI Operator installed
- [ ] DataScienceCluster configured
- [ ] Llama 3.1 405B model downloaded
- [ ] Model uploaded to S3-compatible storage
- [ ] Data Connection created
- [ ] vLLM ServingRuntime configured
- [ ] InferenceService deployed
- [ ] vLLM pod in Running state
- [ ] Route exposed and accessible
- [ ] Inference test successful
- [ ] OpenCode configured
- [ ] Repository skills tested

---

**End of Document**

Version: 1.0  
Last updated: 2026-04-03  
Maintainer: Agentic Collections Team

---

## 📍 Navigation

**You've completed Part 3: Testing and Results**

🎉 **Congratulations!** You should now have:
- OpenCode configured and connected to your local LLM
- Validated model performance through benchmarks
- Tested skills from the agentic-collections repository
- Implemented security hardening measures
- Troubleshooting knowledge for common issues

**What's Next:**
- Deploy additional models for comparison
- Optimize performance based on benchmarks
- Integrate with your production workflows
- Share feedback and improvements

---

**[← Previous: Installation Guide](./installation.md)** | **[Back to Index](./index.md)**

---

## 🙏 Acknowledgments

This guide was created by the Agentic Collections Team based on:
- Official Red Hat OpenShift AI documentation
- Community best practices
- Real-world deployment experience

**Questions or issues?** Refer to the [Troubleshooting](#13-troubleshooting) section or consult official Red Hat documentation.
