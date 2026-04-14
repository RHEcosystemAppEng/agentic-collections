#!/usr/bin/env python3
"""
Generate static collection pages under docs/collections/.

This keeps the main catalog page dynamic while restoring fork-equivalent
collection-page UX with fully rendered markdown.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Dict, List

import markdown


REPO_ROOT = Path(__file__).resolve().parent.parent


def md_to_html(text: Any) -> str:
    """Render markdown to HTML using the same extensions as the fork."""
    if text is None:
        return ""
    raw = str(text).strip()
    if not raw:
        return ""
    md = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br"])
    return md.convert(raw)


def extract_mcp_configuration_section(deploy_text: str) -> tuple[str, str]:
    """
    Pull ### MCP configuration (and body) out so it is not folded into
    ### Installation (Cursor) / other platform blocks by split_deploy_into_sections.
    """
    pattern = re.compile(
        r"(?:^|\n)(### MCP configuration\s*\n.*?)(?=\n### |\Z)",
        re.DOTALL,
    )
    m = pattern.search(deploy_text)
    if not m:
        return deploy_text, ""
    section = m.group(1).strip()
    rest = deploy_text[: m.start()] + deploy_text[m.end() :]
    return rest.strip(), section


def split_deploy_into_sections(deploy_text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Split deploy_and_use content into preface + platform install blocks.

    Matches headings like:
      ### Installation (Claude Code)
      ### Installation (Cursor)
      ### Installation (Open Code)

    Call extract_mcp_configuration_section() first so MCP prose is not captured
    inside the last Installation (...) block.
    """
    pattern = re.compile(
        r"### Installation \((Claude Code|Cursor|Open Code)\)\s*\n(.*?)(?=### Installation \(|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(deploy_text)
    if not matches:
        return deploy_text.strip(), []
    pre_end = deploy_text.find("### Installation (")
    pre_content = deploy_text[:pre_end].strip() if pre_end > 0 else ""
    return pre_content, [(platform, content.strip()) for platform, content in matches]


def _render_skills_list(skills: List[Dict[str, Any]], pack_name: str) -> str:
    items: List[str] = []
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        name = str(skill.get("name", ""))
        desc = html.escape(str(skill.get("description", "")))
        summary = md_to_html(skill.get("summary_markdown", ""))
        skill_path = f"https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/{pack_name}/skills/{name}/SKILL.md"
        block = [
            "<li>",
            f"<div><code>/{html.escape(name)}</code> - {desc}</div>",
        ]
        if summary:
            block.append(f"<div class=\"collection-prose collection-prose-tight\">{summary}</div>")
        block.append(
            f"<a class=\"collection-inline-link\" href=\"{skill_path}\" target=\"_blank\" rel=\"noopener noreferrer\">"
            "View SKILL.md on GitHub -></a>"
        )
        block.append("</li>")
        items.append("\n".join(block))
    return f"<ol class=\"collection-skill-list\">{''.join(items)}</ol>" if items else ""


def _render_decision_guide(rows: List[Dict[str, Any]]) -> str:
    body_rows: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        user_request = md_to_html(row.get("user_request", row.get("user_quote", "")))
        skill_to_use = str(row.get("skill_to_use", ""))
        if skill_to_use and not skill_to_use.startswith("/"):
            skill_to_use = f"/{skill_to_use}"
        reason = md_to_html(row.get("reason", ""))
        body_rows.append(
            "<tr>"
            f"<td>{user_request}</td>"
            f"<td>{html.escape(skill_to_use)}</td>"
            f"<td>{reason}</td>"
            "</tr>"
        )
    if not body_rows:
        return ""
    return (
        "<table class=\"collection-decision-table\">"
        "<thead><tr><th>User request</th><th>Skill to use</th><th>Reason</th></tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


def _render_resources(resources: List[Dict[str, Any]], pack_name: str) -> str:
    if not resources:
        return "<p class=\"collection-missing\">No resources.</p>"

    out = ["<h2>References</h2>", "<ul class=\"simple-list collection-resources\">"]
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        title = html.escape(str(resource.get("title", "")))
        description = html.escape(str(resource.get("description", "")))
        url = str(resource.get("url", "")).strip()
        embedded = str(resource.get("embedded_doc", "")).strip()
        line = ["<li>"]
        if url:
            safe_url = html.escape(url, quote=True)
            line.append(
                f'<a class="collection-resource-link" href="{safe_url}" '
                'target="_blank" rel="noopener noreferrer">'
                f"{title}</a>"
            )
        else:
            line.append(f"<strong>{title}</strong>")
        if description:
            line.append(f" - {description}")
        if embedded:
            embed_url = (
                "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
                f"{pack_name}/{embedded.lstrip('/')}"
            )
            line.append(
                f' <a class="collection-inline-link" href="{html.escape(embed_url, quote=True)}" '
                'target="_blank" rel="noopener noreferrer">[embedded doc]</a>'
            )
        line.append("</li>")
        out.append("".join(line))
    out.append("</ul>")
    return "".join(out)


def _render_agents_tab(
    workflows: List[Dict[str, Any]],
    mcp_servers: List[Dict[str, Any]],
) -> str:
    out: List[str] = ["<h2>MCP Server Integrations</h2>"]
    if mcp_servers:
        out.append('<div class="collection-mcp-grid">')
        for server in mcp_servers:
            title = html.escape(str(server.get("title") or server.get("name") or ""))
            owner = html.escape(str(server.get("owner") or "Red Hat"))
            server_type = "HTTP Remote" if server.get("type") == "http" else "Container"
            icon = str(server.get("icon") or "")
            icon_html = f"<span>{html.escape(icon)}</span>" if icon else ""
            pack = html.escape(str(server.get("pack") or ""))
            name = html.escape(str(server.get("name") or ""))
            out.append(
                '<div class="collection-mcp-card" role="button" tabindex="0" '
                f'data-mcp-pack="{pack}" data-mcp-name="{name}">'
                f'<div class="collection-mcp-card-title">{icon_html}<span>{title}</span></div>'
                f'<div class="collection-mcp-card-meta">By {owner} - {server_type}</div>'
                "</div>"
            )
        out.append("</div>")
    else:
        out.append(
            "<p class=\"collection-missing\">No MCP servers are associated with this pack in the published site data.</p>"
        )

    out.append("<h2>Sample Workflows</h2>")
    valid_workflows = [
        w for w in workflows if isinstance(w, dict) and w.get("name") != "TODO: Add workflow"
    ]
    if not valid_workflows:
        valid_workflows = [{"name": "See collection.yaml", "workflow": "Add workflows in collection.yaml."}]
    for wf in valid_workflows:
        name = html.escape(str(wf.get("name", "")))
        workflow_html = md_to_html(wf.get("workflow", ""))
        out.append(f"<h3>{name}</h3>")
        out.append(f"<div class=\"collection-prose\">{workflow_html}</div>")
    return "".join(out)


def render_collection_page(pack: Dict[str, Any], mcp_data: List[Dict[str, Any]]) -> str:
    """Render a full static collection page for one pack."""
    collection = pack.get("collection") or {}
    collection_id = (
        collection.get("id")
        or pack.get("plugin", {}).get("name")
        or pack.get("name")
    )
    page_title = collection.get("name") or pack.get("plugin", {}).get("title") or pack.get("name")
    description = str(collection.get("description") or "").strip()
    subtitle = html.escape(description[:120].strip() + ("..." if len(description) > 120 else ""))
    yaml_link = (
        "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
        f"{pack['name']}/.catalog/collection.yaml"
    )
    readme_link = (
        "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
        f"{pack['name']}/README.md"
    )
    categories = collection.get("categories") or []
    personas = collection.get("personas") or []
    version = pack.get("plugin", {}).get("version")
    meta_line_parts: List[str] = [f"<strong>Module:</strong> {html.escape(str(pack['name']))}"]
    if version:
        meta_line_parts.append(html.escape(f"v{version}"))
    if personas:
        meta_line_parts.append(html.escape(", ".join(str(p) for p in personas)))
    metadata_line_html = f'<p class="collection-page-sub">{" · ".join(meta_line_parts)}</p>'

    # Overview tab
    overview_parts: List[str] = []
    if collection.get("summary"):
        overview_parts.append("<h2>Overview</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('summary'))}</div>")
    if collection.get("documentation_section"):
        overview_parts.append("<h2>Documentation</h2>")
        overview_parts.append(
            f"<div class=\"collection-prose\">{md_to_html(collection.get('documentation_section'))}</div>"
        )
    if collection.get("mcp_section"):
        overview_parts.append("<h2>MCP</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('mcp_section'))}</div>")
    if collection.get("deploy_and_use"):
        overview_parts.append("<h2>Quick Start</h2>")
        deploy_raw = str(collection.get("deploy_and_use"))
        deploy_for_installs, mcp_deploy_section = extract_mcp_configuration_section(deploy_raw)
        pre_content, install_sections = split_deploy_into_sections(deploy_for_installs)
        if pre_content:
            overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(pre_content)}</div>")
        if install_sections:
            overview_parts.append('<div class="install-accordion">')
            for idx, (platform, content) in enumerate(install_sections):
                open_attr = " open" if idx == 0 else ""
                overview_parts.append(
                    f'<details class="install-accordion-item"{open_attr}>'
                    f'<summary class="install-accordion-header">Installation ({html.escape(platform)})</summary>'
                    f'<div class="install-accordion-body collection-prose">{md_to_html(content)}</div>'
                    "</details>"
                )
            overview_parts.append("</div>")
        if mcp_deploy_section:
            overview_parts.append(
                f'<div class="collection-prose collection-mcp-after-install">{md_to_html(mcp_deploy_section)}</div>'
            )
    if collection.get("security_model"):
        overview_parts.append("<h2>Security Model</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('security_model'))}</div>")

    # Skills tab
    contents = collection.get("contents") or {}
    skills_parts = ["<h2>Skills</h2>"]
    if contents.get("description"):
        skills_parts.append(f"<div class=\"collection-prose\">{md_to_html(contents.get('description'))}</div>")
    orchestration = contents.get("orchestration_skills") or []
    skills = contents.get("skills") or []
    if orchestration:
        skills_parts.append(f"<h3>{'Orchestration Skill' if len(orchestration) == 1 else 'Orchestration Skills'}</h3>")
        skills_parts.append(_render_skills_list(orchestration, pack["name"]))
    if skills:
        skills_parts.append(f"<h3>{'Basic Skills' if orchestration else 'Skills'}</h3>")
        skills_parts.append(_render_skills_list(skills, pack["name"]))
    guide = contents.get("skills_decision_guide") or []
    if guide:
        skills_parts.append("<h2>Skills Decision Guide</h2>")
        skills_parts.append(_render_decision_guide(guide))
    if not orchestration and not skills and not guide and not contents.get("description"):
        skills_parts.append("<p class=\"collection-missing\">No skills content.</p>")

    # Resources tab
    resources_html = _render_resources(collection.get("resources") or [], pack["name"])

    # Agents tab
    pack_mcp = [s for s in mcp_data if s.get("pack") == pack.get("name")]
    agents_html = _render_agents_tab(collection.get("sample_workflows") or [], pack_mcp)

    category_line = (
        f'<p class="collection-tags"><strong>Categories:</strong> {html.escape(", ".join(str(c) for c in categories))}</p>'
        if categories
        else ""
    )
    repo_footer = (
        f'<p class="collection-footer-meta">{html.escape(str(collection.get("repository")))}</p>'
        if collection.get("repository")
        else ""
    )

    legal = collection.get("legal_resources") or {}
    license_nav_href = str(legal.get("license_agreement_url") or "").strip()
    if not license_nav_href:
        license_nav_href = "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/LICENSE"
    license_nav_href_esc = html.escape(license_nav_href, quote=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(str(page_title))} - Red Hat Agentic Catalog</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Red+Hat+Text:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css?v=34">
</head>
<body>
    <div class="site-brand-accent" aria-hidden="true"></div>
    <main>
        <section class="collection-page">
            <div class="collection-page-inner collection-content">
                <nav class="collection-nav" aria-label="Collection">
                    <div class="collection-nav-start">
                        <a href="../index.html" class="collection-back">← Back to Catalog</a>
                    </div>
                    <div class="collection-nav-center">
                        <a href="{html.escape(yaml_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">catalog YAML →</a>
                    </div>
                    <div class="collection-nav-end">
                        <a href="{html.escape(readme_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">README →</a>
                        <a href="{license_nav_href_esc}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">Apache 2.0 License →</a>
                    </div>
                </nav>
                <div class="collection-page-body collection-content-inner">
                    <h1 class="collection-page-title">{html.escape(str(page_title))}</h1>
                    <p class="collection-page-sub">{subtitle}</p>
                    {metadata_line_html}
                    {category_line}

                    <div class="collection-tabs" role="tablist">
                        <button type="button" class="collection-tab active" data-tab="overview" role="tab" aria-selected="true" aria-controls="tab-overview">Overview</button>
                        <button type="button" class="collection-tab" data-tab="skills" role="tab" aria-selected="false" aria-controls="tab-skills">Skills</button>
                        <button type="button" class="collection-tab" data-tab="resources" role="tab" aria-selected="false" aria-controls="tab-resources">Resources</button>
                        <button type="button" class="collection-tab" data-tab="agents" role="tab" aria-selected="false" aria-controls="tab-agents">Agents</button>
                    </div>

                    <div id="tab-overview" class="collection-tab-panel active" role="tabpanel">{''.join(overview_parts)}</div>
                    <div id="tab-skills" class="collection-tab-panel" role="tabpanel">{''.join(skills_parts)}</div>
                    <div id="tab-resources" class="collection-tab-panel" role="tabpanel">{resources_html}</div>
                    <div id="tab-agents" class="collection-tab-panel" role="tabpanel">{agents_html}</div>

                    {repo_footer}
                </div>
            </div>
        </section>
    </main>

    <div id="mcp-modal" class="modal">
        <div class="modal-content" id="mcp-details"></div>
    </div>

    <script src="../app.js?v=34"></script>
</body>
</html>
"""


def generate_collection_pages(pack_data: List[Dict[str, Any]], mcp_data: List[Dict[str, Any]]) -> int:
    """Generate docs/collections/*.html and return generated page count."""
    out_dir = REPO_ROOT / "docs" / "collections"
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_files = set()
    count = 0
    for pack in pack_data:
        if not pack.get("collection"):
            continue
        collection = pack.get("collection") or {}
        collection_id = (
            collection.get("id")
            or pack.get("plugin", {}).get("name")
            or pack.get("name")
        )
        file_name = f"{collection_id}.html"
        generated_files.add(file_name)
        page_html = render_collection_page(pack, mcp_data)
        (out_dir / file_name).write_text(page_html, encoding="utf-8")
        count += 1

    # Remove stale collection pages
    for page in out_dir.glob("*.html"):
        if page.name not in generated_files:
            page.unlink()

    return count

