# Air-Gapped LLM Deployment on OpenShift

Complete guide for deploying Large Language Models on Red Hat OpenShift in disconnected environments.

---

## 📖 Documentation Structure

This guide is divided into three main sections for better readability:

### 1. [Context and Preparation](./context-and-preparation.md)
**What you'll learn:**
- Understanding air-gapped environments and their importance
- Solution architecture overview
- Model selection criteria and testing methodology
- Required Red Hat components
- Hardware provisioning requirements

**Time to read:** ~15 minutes  
**Prerequisites:** Basic OpenShift knowledge

---

### 2. [Installation Guide](./installation.md)
**What you'll learn:**
- Step-by-step operator installation (NFD, NVIDIA GPU, RHOAI)
- OpenShift cluster configuration for GPU workloads
- Model deployment with vLLM and KServe
- Complete copy-paste ready commands

**Time to complete:** 2-4 hours (depending on model size)  
**Prerequisites:** 
- OpenShift 4.20+ cluster with cluster-admin access
- GPU-enabled node provisioned (see Context & Preparation)
- `oc` CLI installed and authenticated

---

### 3. [Testing and Results](./testing-and-results.md)
**What you'll learn:**
- OpenCode configuration for local model access
- Performance benchmarking procedures
- Skills testing methodology
- Security hardening (authentication, TLS, network policies)
- Troubleshooting common issues

**Time to complete:** 1-2 hours  
**Prerequisites:** Completed installation from Section 2

---

## 🎯 Quick Start

**New to this?** Start here:
1. Read [Context and Preparation](./context-and-preparation.md) to understand the architecture
2. Follow [Installation Guide](./installation.md) step-by-step
3. Validate with [Testing and Results](./testing-and-results.md)

**Already familiar?** Jump directly to:
- [Operator Installation Commands](./installation.md#operator-installation)
- [Model Deployment](./installation.md#model-deployment-with-vllm)
- [Troubleshooting Guide](./testing-and-results.md#troubleshooting)

---

## 🔧 Reference Configuration

This guide documents deployment of:
- **Platform:** Red Hat OpenShift 4.20+
- **AI Framework:** Red Hat OpenShift AI 2.22+
- **Inference Runtime:** vLLM (RawDeployment mode)
- **Example Model:** Llama 3.1 405B (FP8 quantized)
- **Hardware:** AWS p5.48xlarge (8x NVIDIA H100 80GB)

**Note:** Instructions are adaptable to other models and hardware configurations.

---

## 📋 Prerequisites Summary

Before starting, ensure you have:

- [ ] OpenShift cluster 4.20+ installed and accessible
- [ ] Cluster-admin access credentials
- [ ] `oc` CLI tool installed locally
- [ ] GPU-enabled node provisioned (or plan to provision)
- [ ] S3-compatible storage for model weights
- [ ] Valid Red Hat subscriptions for OpenShift AI

**Not sure?** See [Prerequisites Details](./context-and-preparation.md#prerequisites) for complete checklist.

---

## 🎓 Learning Path

### Beginner
1. Start with [Context and Preparation](./context-and-preparation.md)
2. Understand the architecture diagrams
3. Review model selection criteria
4. Provision required hardware

### Intermediate
1. Skip to [Installation Guide](./installation.md)
2. Execute operator installations
3. Configure GPU nodes
4. Deploy your first model

### Advanced
1. Review [Testing and Results](./testing-and-results.md)
2. Implement security hardening
3. Optimize performance based on benchmarks
4. Customize for production use

---

## 🆘 Support Resources

**Official Red Hat Documentation:**
- [OpenShift AI 2.22 - Model Serving](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.22/html/serving_models/about-model-serving_about-model-serving)
- [OpenShift AI 3.2 - Deploying Models](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.2/html-single/deploying_models/index)
- [NVIDIA GPU Operator Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)

**Community Resources:**
- [Red Hat Developer Articles](https://developers.redhat.com/topics/ai-ml)
- [KServe Documentation](https://kserve.github.io/website/)
- [vLLM Documentation](https://docs.vllm.ai/)

**Issues & Feedback:**
- Found a problem? See [Troubleshooting](./testing-and-results.md#troubleshooting)
- Have a suggestion? Open an issue in this repository

---

## 📄 Document Information

**Version:** 1.0  
**Last Updated:** 2026-04-03  
**Maintained By:** Agentic Collections Team  
**License:** Follow your organization's documentation guidelines

---

**Ready to begin?** Start with [Context and Preparation →](./context-and-preparation.md)
