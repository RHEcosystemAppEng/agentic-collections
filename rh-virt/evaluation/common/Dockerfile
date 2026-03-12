FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root

RUN pip3 install --break-system-packages \
    pyyaml==6.0.1 \
    fastmcp

ENV KUBECONFIG=/root/.kube/config

# Canonical docs location (absolute fallback for all agents)
COPY docs /root/docs

# Pre-create Claude Code's session path so skill-relative doc references resolve.
# Skills reference docs via ../../docs/ which from /logs/agent/sessions/skills/X/
# resolves to /logs/agent/sessions/docs/. The symlink bridges that gap.
RUN mkdir -p /logs/agent/sessions && \
    ln -s /root/docs /logs/agent/sessions/docs

# Copy skills and docs to standard directories for different AI coding assistants
COPY skills /root/.claude/skills
COPY docs /root/.claude/docs
COPY skills /root/.codex/skills
COPY docs /root/.codex/docs
COPY skills /root/.opencode/skill
COPY docs /root/.opencode/docs
COPY skills /root/.goose/skills
COPY docs /root/.goose/docs
COPY skills /root/.factory/skills
COPY docs /root/.factory/docs
COPY skills /root/.agents/skills
COPY docs /root/.agents/docs
COPY skills /root/.gemini/skills
COPY docs /root/.gemini/docs

COPY mcp-servers /root/.mcp-servers

# Mock kubeconfig — the MCP server is a mock so no real cluster access needed
RUN mkdir -p /root/.kube && echo '\
apiVersion: v1\n\
kind: Config\n\
current-context: ocp-virt-prod\n\
clusters:\n\
- name: ocp-virt-prod\n\
  cluster:\n\
    server: https://api.ocp-virt-prod.example.com:6443\n\
contexts:\n\
- name: ocp-virt-prod\n\
  context:\n\
    cluster: ocp-virt-prod\n\
    user: admin\n\
    namespace: default\n\
users:\n\
- name: admin\n\
  user:\n\
    token: mock-token-for-testing\n' > /root/.kube/config

# MCP server config — name matches what skills reference as "openshift-virtualization"
RUN echo '{ \
  "mcpServers": { \
    "openshift-virtualization": { \
      "command": "python3", \
      "args": ["/root/.mcp-servers/mock-virt-mcp.py"] \
    } \
  } \
}' > /root/.mcp.json

WORKDIR /root
