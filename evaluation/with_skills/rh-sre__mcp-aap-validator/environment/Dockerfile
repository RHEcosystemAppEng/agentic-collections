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



COPY docs /root/docs

RUN mkdir -p /logs/agent/sessions && \
    ln -s /root/docs /logs/agent/sessions/docs

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

RUN echo '{ \
  "mcpServers": { \
    "lightspeed-mcp": { \
      "command": "python3", \
      "args": ["/root/.mcp-servers/mock-lightspeed-mcp.py"] \
    }, \
    "aap-mcp": { \
      "command": "python3", \
      "args": ["/root/.mcp-servers/mock-aap-mcp.py"] \
    } \
  } \
}' > /root/.mcp.json

WORKDIR /root
