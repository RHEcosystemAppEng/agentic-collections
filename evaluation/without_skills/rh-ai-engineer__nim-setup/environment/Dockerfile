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
RUN mkdir -p /root/.kube && echo '\
apiVersion: v1\n\
kind: Config\n\
current-context: ocp-prod\n\
clusters:\n\
- name: ocp-prod\n\
  cluster:\n\
    server: https://api.ocp-prod.example.com:6443\n\
contexts:\n\
- name: ocp-prod\n\
  context:\n\
    cluster: ocp-prod\n\
    user: admin\n\
    namespace: default\n\
users:\n\
- name: admin\n\
  user:\n\
    token: mock-token-for-testing\n' > /root/.kube/config

COPY docs /root/docs

RUN mkdir -p /logs/agent/sessions && \
    ln -s /root/docs /logs/agent/sessions/docs

COPY docs /root/.claude/docs
COPY docs /root/.codex/docs
COPY docs /root/.opencode/docs
COPY docs /root/.goose/docs
COPY docs /root/.factory/docs
COPY docs /root/.agents/docs
COPY docs /root/.gemini/docs

COPY mcp-servers /root/.mcp-servers

RUN echo '{ \
  "mcpServers": { \
    "openshift": { \
      "command": "python3", \
      "args": ["/root/.mcp-servers/mock-openshift-mcp.py"] \
    }, \
    "rhoai": { \
      "command": "python3", \
      "args": ["/root/.mcp-servers/mock-rhoai-mcp.py"] \
    } \
  } \
}' > /root/.mcp.json

WORKDIR /root
