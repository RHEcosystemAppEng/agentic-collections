# Red Hat AI Engineer Agentic Pack

Automation tools for AI/ML engineers working with Red Hat OpenShift AI (RHOAI). Deploy and manage models using KServe with vLLM, NVIDIA NIM, and Caikit+TGIS serving runtimes.

## Skills

| Command | Description |
|---------|-------------|
| `/nim-setup` | Configure NVIDIA NIM platform on OpenShift AI (NGC credentials, Account CR) |
| `/model-deploy` | Deploy AI/ML models with vLLM, NIM, or Caikit+TGIS runtimes |
| `/serving-runtime-config` | Configure custom ServingRuntime CRs for model serving frameworks |
| `/debug-inference` | Troubleshoot failed or slow InferenceService deployments |
| `/ai-observability` | Analyze model performance, GPU utilization, cluster health, and distributed traces |

## Prerequisites

### Tools
- `oc` CLI (OpenShift client) for cluster access

### Environment Variables
- `KUBECONFIG` - Path to Kubernetes configuration file
- `AI_OBSERVABILITY_MCP_URL` (optional) - URL for the AI Observability MCP server

### Cluster Requirements
- OpenShift cluster with Red Hat OpenShift AI operator installed
- KServe model serving platform configured
- NVIDIA GPU nodes available (for GPU-accelerated inference)

### For NIM Deployments
- NVIDIA GPU Operator installed
- Node Feature Discovery (NFD) Operator installed
- NGC API key

## MCP Servers

| Server | Type | Required | Description |
|--------|------|----------|-------------|
| `openshift` | Container (podman) | Yes | Kubernetes resource CRUD, pod management, logs, events |
| `ai-observability` | Remote HTTP | No | vLLM metrics, GPU monitoring, distributed tracing |

The `ai-observability` MCP server is optional. When available, it enables GPU pre-flight checks before deployment and post-deployment performance validation. See [ai-observability-summarizer](https://github.com/rh-ai-quickstart/ai-observability-summarizer/tree/main/src/mcp_server) for deployment instructions.

## Supported Runtimes

| Runtime | Use Case | Setup Required |
|---------|----------|----------------|
| vLLM | Default for open-source LLMs (Llama, Granite, Mixtral, Mistral) | None |
| NVIDIA NIM | Optimized inference with TensorRT-LLM on NVIDIA GPUs | `/nim-setup` |
| Caikit+TGIS | Models in Caikit format with gRPC API | Model conversion |

See [supported-runtimes.md](docs/references/supported-runtimes.md) for detailed runtime comparison.

## Supported Models

Common models with known hardware profiles:

| Model | Parameters | Min GPUs | Default Runtime |
|-------|-----------|----------|-----------------|
| Llama 3.1 8B | 8B | 1x (16GB VRAM) | vLLM |
| Llama 3.1 70B | 70B | 4x A100 80GB | vLLM / NIM |
| Granite 3.1 8B | 8B | 1x (16GB VRAM) | vLLM |
| Mixtral 8x7B | 46.7B MoE | 2x A100 80GB | vLLM |
| Mistral 7B | 7B | 1x (16GB VRAM) | vLLM |

See [known-model-profiles.md](docs/references/known-model-profiles.md) for full profiles. Models not listed are supported via live documentation lookup.
