/**
 * agentic-collections Documentation Site
 *
 * SECURITY: All DOM manipulation uses textContent and createElement
 * to prevent XSS vulnerabilities. No innerHTML with user data.
 */

let data = null;
let allPacks = [];
let allMCPServers = [];

/**
 * Update toolbar counter badges
 */
function updateToolbarCounters(packs, mcpServers) {
    // Count total skills and agents across all packs
    const totalSkills = packs.reduce((sum, pack) => sum + pack.skills.length, 0);
    const totalAgents = packs.reduce((sum, pack) => sum + pack.agents.length, 0);

    // Count total docs (sources) across all packs
    const totalDocs = packs.reduce((sum, pack) => {
        return sum + (pack.docs || []).reduce((docSum, doc) => {
            return docSum + (doc.sources?.length || 0);
        }, 0);
    }, 0);

    // Update counter badges
    document.querySelector('#packs-badge .counter-number').textContent = packs.length;
    document.querySelector('#skills-badge .counter-number').textContent = totalSkills;
    document.querySelector('#agents-badge .counter-number').textContent = totalAgents;
    document.querySelector('#docs-badge .counter-number').textContent = totalDocs;
    document.querySelector('#mcp-badge .counter-number').textContent = mcpServers.length;
}

/**
 * Initialize the application
 */
async function init() {
    try {
        // Load data.json
        const response = await fetch('data.json');
        data = await response.json();

        // Store original data for search
        allPacks = data.packs;
        allMCPServers = data.mcp_servers;

        // Update toolbar counters
        updateToolbarCounters(allPacks, allMCPServers);

        // Render sections
        renderPacks(allPacks);
        renderMCPServers(allMCPServers);

        // Setup search
        document.getElementById('searchInput').addEventListener('input', handleSearch);

        // Setup modal close handlers
        setupModals();

    } catch (error) {
        console.error('Failed to load data:', error);
        showError('Failed to load documentation data. Please try refreshing the page.');
    }
}

/**
 * Display error message
 */
function showError(message) {
    const main = document.querySelector('main');
    const errorDiv = document.createElement('div');
    errorDiv.style.color = '#ee0000';
    errorDiv.style.padding = '2rem';
    errorDiv.style.textAlign = 'center';
    errorDiv.textContent = `Error: ${message}`;
    main.insertBefore(errorDiv, main.firstChild);
}

/**
 * Render agentic packs grid
 */
function renderPacks(packs) {
    const grid = document.getElementById('packs-grid');
    const count = document.getElementById('packs-count');

    // Clear existing content
    grid.textContent = '';
    count.textContent = `(${packs.length})`;

    if (packs.length === 0) {
        const noResults = document.createElement('p');
        noResults.textContent = 'No packs found matching your search.';
        noResults.style.color = '#d2d2d2';
        grid.appendChild(noResults);
        return;
    }

    packs.forEach(pack => {
        const card = createPackCard(pack);
        grid.appendChild(card);
    });
}

/**
 * Create a pack card (XSS-safe)
 */
function createPackCard(pack) {
    const div = document.createElement('div');
    div.className = 'card pack-card';

    // Pack name
    const h3 = document.createElement('h3');
    h3.textContent = pack.plugin.name || pack.name;
    div.appendChild(h3);

    // Version
    const version = document.createElement('p');
    version.className = 'version';
    version.textContent = `v${pack.plugin.version || '0.0.0'}`;
    div.appendChild(version);

    // Description
    const desc = document.createElement('p');
    desc.className = 'description';
    desc.textContent = pack.plugin.description || 'No description available';
    div.appendChild(desc);

    // Stats
    const stats = document.createElement('div');
    stats.className = 'stats';

    const skillSpan = document.createElement('span');
    skillSpan.textContent = `${pack.skills.length} skill${pack.skills.length !== 1 ? 's' : ''}`;
    stats.appendChild(skillSpan);

    const agentSpan = document.createElement('span');
    agentSpan.textContent = `${pack.agents.length} agent${pack.agents.length !== 1 ? 's' : ''}`;
    stats.appendChild(agentSpan);

    // Add docs count (count sources, not doc files)
    const docsCount = (pack.docs || []).reduce((sum, doc) => {
        return sum + (doc.sources?.length || 0);
    }, 0);
    if (docsCount > 0) {
        const docsSpan = document.createElement('span');
        docsSpan.textContent = `${docsCount} doc${docsCount !== 1 ? 's' : ''}`;
        stats.appendChild(docsSpan);
    }

    div.appendChild(stats);

    // View button
    const button = document.createElement('button');
    button.textContent = 'View Details';
    button.onclick = () => showPackDetails(pack.name);
    div.appendChild(button);

    return div;
}

/**
 * Render MCP servers grid
 */
function renderMCPServers(servers) {
    const grid = document.getElementById('mcp-grid');
    const count = document.getElementById('mcp-count');

    // Clear existing content
    grid.textContent = '';
    count.textContent = `(${servers.length})`;

    if (servers.length === 0) {
        const noResults = document.createElement('p');
        noResults.textContent = 'No MCP servers found matching your search.';
        noResults.style.color = '#d2d2d2';
        grid.appendChild(noResults);
        return;
    }

    servers.forEach(server => {
        const card = createMCPCard(server);
        grid.appendChild(card);
    });
}

/**
 * Create an MCP server card (XSS-safe)
 */
function createMCPCard(server) {
    const div = document.createElement('div');
    div.className = 'card mcp-card';
    div.style.position = 'relative'; // For absolute positioning of README button

    // README button in top-right corner (if repository exists)
    if (server.repository) {
        const readmeButton = document.createElement('a');
        readmeButton.href = server.repository;
        readmeButton.target = '_blank';
        readmeButton.className = 'readme-badge';
        readmeButton.textContent = 'README';
        readmeButton.onclick = (e) => e.stopPropagation(); // Prevent card click
        div.appendChild(readmeButton);
    }

    // Server name
    const h3 = document.createElement('h3');
    h3.textContent = server.name;
    div.appendChild(h3);

    // Pack tag
    const packTag = document.createElement('p');
    packTag.className = 'pack-tag';
    packTag.textContent = `Collection: ${server.pack}`;
    div.appendChild(packTag);

    // Container
    const container = document.createElement('p');
    container.className = 'container';
    container.textContent = `Container: ${server.command}`;
    div.appendChild(container);

    // Environment variables
    const envVars = document.createElement('div');
    envVars.className = 'env-vars';
    envVars.textContent = server.env.length > 0
        ? `${server.env.length} env var${server.env.length !== 1 ? 's' : ''}`
        : 'No env vars';
    div.appendChild(envVars);

    // Tools count
    if (server.tools && server.tools.length > 0) {
        const toolsInfo = document.createElement('div');
        toolsInfo.className = 'env-vars';
        toolsInfo.textContent = `${server.tools.length} tool${server.tools.length !== 1 ? 's' : ''}`;
        div.appendChild(toolsInfo);
    }

    // Details button
    const detailsButton = document.createElement('button');
    detailsButton.textContent = 'Details';
    detailsButton.onclick = () => showMCPDetails(server.name, server.pack);
    detailsButton.style.marginTop = 'auto';
    div.appendChild(detailsButton);

    return div;
}

/**
 * Handle search input
 */
function handleSearch(event) {
    const query = event.target.value.toLowerCase().trim();

    if (!query) {
        // Reset to show all
        updateToolbarCounters(allPacks, allMCPServers);
        renderPacks(allPacks);
        renderMCPServers(allMCPServers);
        return;
    }

    // Filter packs
    const filteredPacks = allPacks.filter(pack => {
        // Search in pack name, description, skills, agents
        const searchText = [
            pack.name,
            pack.plugin.name,
            pack.plugin.description,
            ...pack.skills.map(s => s.name + ' ' + s.description),
            ...pack.agents.map(a => a.name + ' ' + a.description)
        ].join(' ').toLowerCase();

        return searchText.includes(query);
    });

    // Filter MCP servers
    const filteredServers = allMCPServers.filter(server => {
        // Search in server name, pack, command
        const searchText = [
            server.name,
            server.pack,
            server.command,
            ...server.env
        ].join(' ').toLowerCase();

        return searchText.includes(query);
    });

    // Update counters to reflect filtered results
    updateToolbarCounters(filteredPacks, filteredServers);
    renderPacks(filteredPacks);
    renderMCPServers(filteredServers);
}

/**
 * Toggle section visibility
 */
function toggleSection(sectionId) {
    const section = document.getElementById(`${sectionId}-section`);
    section.classList.toggle('collapsed');
}

/**
 * Show pack details modal (XSS-safe)
 */
function showPackDetails(packName) {
    const pack = data.packs.find(p => p.name === packName);
    if (!pack) return;

    const modal = document.getElementById('pack-modal');
    const details = document.getElementById('pack-details');

    // Clear previous content
    details.textContent = '';

    // Create modal header
    const header = document.createElement('div');
    header.className = 'modal-header';

    // Close button
    const closeBtn = document.createElement('span');
    closeBtn.className = 'close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore background scrolling
    };
    header.appendChild(closeBtn);

    const headerTop = document.createElement('div');
    headerTop.className = 'modal-header-top';

    const titleGroup = document.createElement('div');
    titleGroup.className = 'modal-title-group';

    const h2 = document.createElement('h2');
    h2.textContent = pack.plugin.name || pack.name;
    titleGroup.appendChild(h2);

    // Counts (skills + agents)
    const counts = document.createElement('div');
    counts.className = 'modal-counts';
    const countParts = [];
    if (pack.skills.length > 0) {
        countParts.push(`${pack.skills.length} skill${pack.skills.length !== 1 ? 's' : ''}`);
    }
    if (pack.agents.length > 0) {
        countParts.push(`${pack.agents.length} agent${pack.agents.length !== 1 ? 's' : ''}`);
    }
    counts.textContent = countParts.join(' ');
    titleGroup.appendChild(counts);

    headerTop.appendChild(titleGroup);

    // Meta (version badge + readme button if available)
    const meta = document.createElement('div');
    meta.className = 'modal-meta';

    const versionBadge = document.createElement('span');
    versionBadge.className = 'version-badge';
    versionBadge.textContent = `v${pack.plugin.version || '0.0.0'}`;
    meta.appendChild(versionBadge);

    if (pack.has_readme) {
        const readmeButton = document.createElement('a');
        readmeButton.className = 'readme-button';
        readmeButton.textContent = 'README';
        readmeButton.href = `https://github.com/RHEcosystemAppEng/agentic-collections/tree/main/${pack.name}`;
        readmeButton.target = '_blank';
        meta.appendChild(readmeButton);
    }

    headerTop.appendChild(meta);
    header.appendChild(headerTop);

    // Description
    if (pack.plugin.description) {
        const desc = document.createElement('div');
        desc.className = 'modal-description';
        desc.textContent = pack.plugin.description;
        header.appendChild(desc);
    }

    details.appendChild(header);

    // Create modal body
    const body = document.createElement('div');
    body.className = 'modal-body';

    // Installation section
    const installSection = document.createElement('div');
    installSection.className = 'modal-section';

    const installHeader = document.createElement('div');
    installHeader.className = 'modal-section-header';
    installHeader.textContent = 'INSTALLATION';
    installSection.appendChild(installHeader);

    // Claude installation
    const claudeLabel = document.createElement('div');
    claudeLabel.className = 'modal-section-label';
    claudeLabel.textContent = 'Claude Code:';
    claudeLabel.style.marginTop = '1rem';
    installSection.appendChild(claudeLabel);

    const claudeCodeWrapper = document.createElement('div');
    claudeCodeWrapper.className = 'install-code-wrapper';

    const claudePre = document.createElement('pre');
    const claudeCode = document.createElement('code');
    // Get plugin name from plugin.json or use pack name as fallback
    const pluginName = pack.plugin.name || pack.name;
    claudeCode.textContent = `claude plugin marketplace remove redhat-agentic-collections
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install ${pluginName}`;
    claudePre.appendChild(claudeCode);
    claudeCodeWrapper.appendChild(claudePre);

    const claudeCopyBtn = document.createElement('button');
    claudeCopyBtn.className = 'copy-button';
    claudeCopyBtn.textContent = 'Copy';
    claudeCopyBtn.onclick = () => copyToClipboard(claudeCode.textContent, claudeCopyBtn);
    claudeCodeWrapper.appendChild(claudeCopyBtn);

    installSection.appendChild(claudeCodeWrapper);

    // Cursor installation
    const cursorLabel = document.createElement('div');
    cursorLabel.className = 'modal-section-label';
    cursorLabel.textContent = 'Cursor:';
    cursorLabel.style.marginTop = '1.5rem';
    installSection.appendChild(cursorLabel);

    const cursorNote = document.createElement('div');
    cursorNote.style.color = 'var(--text-muted)';
    cursorNote.style.fontSize = '0.9rem';
    cursorNote.style.fontStyle = 'italic';
    cursorNote.style.marginTop = '0.5rem';
    cursorNote.textContent = 'Coming soon - Cursor support is planned for future releases';
    installSection.appendChild(cursorNote);

    body.appendChild(installSection);

    // Agents section (shown first)
    if (pack.agents.length > 0) {
        const agentsSection = document.createElement('div');
        agentsSection.className = 'modal-section';

        const agentsHeader = document.createElement('div');
        agentsHeader.className = 'modal-section-header';
        agentsHeader.textContent = 'AGENTS';
        agentsSection.appendChild(agentsHeader);

        const agentsList = document.createElement('div');
        agentsList.className = 'item-list';

        pack.agents.forEach(agent => {
            const agentDef = document.createElement('div');
            agentDef.className = 'agent-definition';

            // Agent syntax block
            const syntaxBlock = document.createElement('div');
            syntaxBlock.className = 'definition-syntax';
            const syntaxCode = document.createElement('code');
            syntaxCode.textContent = agent.name;
            syntaxBlock.appendChild(syntaxCode);
            agentDef.appendChild(syntaxBlock);

            // Agent description (with expand/collapse for long text)
            const desc = document.createElement('div');
            desc.className = 'definition-description';
            desc.appendChild(createExpandableText(agent.description, 200));
            agentDef.appendChild(desc);

            agentsList.appendChild(agentDef);
        });

        agentsSection.appendChild(agentsList);
        body.appendChild(agentsSection);
    }

    // Skills section (shown second)
    if (pack.skills.length > 0) {
        const skillsSection = document.createElement('div');
        skillsSection.className = 'modal-section';

        const skillsHeader = document.createElement('div');
        skillsHeader.className = 'modal-section-header';
        skillsHeader.textContent = 'SKILLS';
        skillsSection.appendChild(skillsHeader);

        const skillsList = document.createElement('div');
        skillsList.className = 'item-list';

        pack.skills.forEach(skill => {
            const skillDef = document.createElement('div');
            skillDef.className = 'skill-definition';

            // Skill syntax block
            const syntaxBlock = document.createElement('div');
            syntaxBlock.className = 'definition-syntax';
            const syntaxCode = document.createElement('code');
            syntaxCode.textContent = skill.name;
            syntaxBlock.appendChild(syntaxCode);
            skillDef.appendChild(syntaxBlock);

            // Skill description (with expand/collapse for long text)
            const desc = document.createElement('div');
            desc.className = 'definition-description';
            desc.appendChild(createExpandableText(skill.description, 200));
            skillDef.appendChild(desc);

            skillsList.appendChild(skillDef);
        });

        skillsSection.appendChild(skillsList);
        body.appendChild(skillsSection);
    }

    // Docs section (shown third, if documentation exists)
    if (pack.docs && pack.docs.length > 0) {
        const docsSection = document.createElement('div');
        docsSection.className = 'modal-section';

        const docsHeader = document.createElement('div');
        docsHeader.className = 'modal-section-header';
        docsHeader.textContent = 'DOCS';
        docsSection.appendChild(docsHeader);

        // Group docs by category
        const docsByCategory = {};
        pack.docs.forEach(doc => {
            const category = doc.category || 'general';
            if (!docsByCategory[category]) {
                docsByCategory[category] = [];
            }
            docsByCategory[category].push(doc);
        });

        // Render each category
        Object.keys(docsByCategory).sort().forEach(category => {
            const categorySection = document.createElement('div');
            categorySection.style.marginBottom = '1.5rem';

            // Category header
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'modal-section-label';
            categoryHeader.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            categorySection.appendChild(categoryHeader);

            // Doc list for this category
            const docsList = document.createElement('div');
            docsList.className = 'item-list';

            docsByCategory[category].forEach(doc => {
                const docDef = document.createElement('div');
                docDef.className = 'skill-definition';

                // Doc title
                const titleBlock = document.createElement('div');
                titleBlock.className = 'definition-syntax';
                const titleCode = document.createElement('code');
                titleCode.textContent = doc.title;
                titleBlock.appendChild(titleCode);
                docDef.appendChild(titleBlock);

                // Sources section
                if (doc.sources && doc.sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'definition-description';

                    doc.sources.forEach((source, index) => {
                        // Add separator between sources
                        if (index > 0) {
                            sourcesDiv.appendChild(document.createElement('br'));
                        }

                        // Source title label
                        const sourceLabel = document.createElement('span');
                        sourceLabel.textContent = 'Source: ';
                        sourceLabel.style.color = 'var(--text-muted)';
                        sourceLabel.style.fontSize = '0.85rem';
                        sourcesDiv.appendChild(sourceLabel);

                        // Source link
                        const sourceLink = document.createElement('a');
                        sourceLink.href = source.url;
                        sourceLink.target = '_blank';
                        sourceLink.textContent = source.title;
                        sourceLink.style.color = 'var(--primary)';
                        sourceLink.style.textDecoration = 'none';
                        sourceLink.onmouseover = () => { sourceLink.style.textDecoration = 'underline'; };
                        sourceLink.onmouseout = () => { sourceLink.style.textDecoration = 'none'; };
                        sourcesDiv.appendChild(sourceLink);
                    });

                    docDef.appendChild(sourcesDiv);
                }

                docsList.appendChild(docDef);
            });

            categorySection.appendChild(docsList);
            docsSection.appendChild(categorySection);
        });

        // Link to full documentation on GitHub
        const docsLink = document.createElement('div');
        docsLink.style.marginTop = '1.5rem';
        docsLink.style.paddingTop = '1rem';
        docsLink.style.borderTop = '1px solid var(--border)';
        const link = document.createElement('a');
        link.href = `https://github.com/RHEcosystemAppEng/agentic-collections/tree/main/${pack.name}/docs`;
        link.target = '_blank';
        link.textContent = 'View full documentation on GitHub →';
        link.style.color = 'var(--primary)';
        link.style.textDecoration = 'none';
        link.style.fontWeight = '600';
        link.onmouseover = () => { link.style.textDecoration = 'underline'; };
        link.onmouseout = () => { link.style.textDecoration = 'none'; };
        docsLink.appendChild(link);
        docsSection.appendChild(docsLink);

        body.appendChild(docsSection);
    }

    details.appendChild(body);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

/**
 * Show MCP server details modal (XSS-safe)
 */
function showMCPDetails(serverName, packName) {
    const server = data.mcp_servers.find(s => s.name === serverName && s.pack === packName);
    if (!server) return;

    const modal = document.getElementById('mcp-modal');
    const details = document.getElementById('mcp-details');

    // Clear previous content
    details.textContent = '';

    // Create modal header
    const header = document.createElement('div');
    header.className = 'modal-header';

    // Close button
    const closeBtn = document.createElement('span');
    closeBtn.className = 'close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore background scrolling
    };
    header.appendChild(closeBtn);

    const headerTop = document.createElement('div');
    headerTop.className = 'modal-header-top';

    const titleGroup = document.createElement('div');
    titleGroup.className = 'modal-title-group';

    const h2 = document.createElement('h2');
    h2.textContent = server.name;
    titleGroup.appendChild(h2);

    headerTop.appendChild(titleGroup);
    header.appendChild(headerTop);

    // Description from .mcp.json or pack name
    const desc = document.createElement('div');
    desc.className = 'modal-description';
    if (server.description) {
        desc.appendChild(renderMarkdown(server.description));
    } else {
        desc.textContent = `MCP server from ${server.pack} pack`;
    }
    header.appendChild(desc);

    // Repository link (if available)
    if (server.repository) {
        const repoLink = document.createElement('div');
        repoLink.className = 'modal-repository-link';

        const repoLabel = document.createElement('span');
        repoLabel.textContent = 'Repository: ';
        repoLabel.style.color = 'var(--text-muted)';
        repoLink.appendChild(repoLabel);

        const repoUrl = document.createElement('a');
        repoUrl.href = server.repository;
        repoUrl.target = '_blank';
        repoUrl.textContent = server.repository;
        repoUrl.style.color = 'var(--primary)';
        repoUrl.style.textDecoration = 'none';
        repoUrl.style.transition = 'color var(--transition-speed) ease';
        repoUrl.onmouseover = () => { repoUrl.style.textDecoration = 'underline'; };
        repoUrl.onmouseout = () => { repoUrl.style.textDecoration = 'none'; };
        repoLink.appendChild(repoUrl);

        header.appendChild(repoLink);
    }

    details.appendChild(header);

    // Create modal body
    const body = document.createElement('div');
    body.className = 'modal-body';

    // Command section
    const cmdSection = document.createElement('div');
    cmdSection.className = 'modal-section';

    const cmdHeader = document.createElement('div');
    cmdHeader.className = 'modal-section-header';
    cmdHeader.textContent = 'COMMAND';
    cmdSection.appendChild(cmdHeader);

    const codeWrapper = document.createElement('div');
    codeWrapper.className = 'install-code-wrapper';

    const cmdPre = document.createElement('pre');
    const cmdCode = document.createElement('code');

    // Format command with line breaks for readability
    let formattedCmd = server.command;
    if (server.args.length > 0) {
        formattedCmd += ' ' + server.args[0]; // First arg on same line
        for (let i = 1; i < server.args.length; i++) {
            formattedCmd += ' \\\n  ' + server.args[i]; // Subsequent args indented
        }
    }
    cmdCode.textContent = formattedCmd;
    cmdPre.appendChild(cmdCode);
    codeWrapper.appendChild(cmdPre);

    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-button';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = () => copyToClipboard(cmdCode.textContent, copyBtn);
    codeWrapper.appendChild(copyBtn);

    cmdSection.appendChild(codeWrapper);
    body.appendChild(cmdSection);

    // Environment variables section
    if (server.env.length > 0) {
        const envSection = document.createElement('div');
        envSection.className = 'modal-section';

        const envHeader = document.createElement('div');
        envHeader.className = 'modal-section-header';
        envHeader.textContent = 'ENVIRONMENT VARIABLES';
        envSection.appendChild(envHeader);

        const envList = document.createElement('ul');
        envList.className = 'simple-list';

        server.env.forEach(v => {
            const li = document.createElement('li');
            li.textContent = v;
            envList.appendChild(li);
        });

        envSection.appendChild(envList);
        body.appendChild(envSection);
    }

    // Security section
    const secSection = document.createElement('div');
    secSection.className = 'modal-section';

    const secHeader = document.createElement('div');
    secHeader.className = 'modal-section-header';
    secHeader.textContent = 'SECURITY';
    secSection.appendChild(secHeader);

    const secList = document.createElement('ul');
    secList.className = 'simple-list';

    ['isolation', 'network', 'credentials'].forEach(key => {
        const li = document.createElement('li');
        const strong = document.createElement('strong');
        const keyLabel = key.charAt(0).toUpperCase() + key.slice(1);
        strong.textContent = `${keyLabel}: `;
        li.appendChild(strong);
        li.appendChild(document.createTextNode(server.security[key] || 'N/A'));
        secList.appendChild(li);
    });

    secSection.appendChild(secList);
    body.appendChild(secSection);

    // Tools section (if available)
    if (server.tools && server.tools.length > 0) {
        const toolsSection = document.createElement('div');
        toolsSection.className = 'modal-section';

        const toolsHeader = document.createElement('div');
        toolsHeader.className = 'modal-section-header';
        toolsHeader.textContent = 'TOOLS';
        toolsSection.appendChild(toolsHeader);

        const toolsList = document.createElement('div');
        toolsList.className = 'item-list';

        server.tools.forEach(tool => {
            const toolDef = document.createElement('div');
            toolDef.className = 'skill-definition';

            // Tool name in syntax block
            const syntaxBlock = document.createElement('div');
            syntaxBlock.className = 'definition-syntax';
            const syntaxCode = document.createElement('code');
            syntaxCode.textContent = tool.name;
            syntaxBlock.appendChild(syntaxCode);
            toolDef.appendChild(syntaxBlock);

            // Tool description (with expand/collapse for long text)
            const desc = document.createElement('div');
            desc.className = 'definition-description';
            desc.appendChild(createExpandableText(tool.description, 200));
            toolDef.appendChild(desc);

            toolsList.appendChild(toolDef);
        });

        toolsSection.appendChild(toolsList);
        body.appendChild(toolsSection);
    }

    details.appendChild(body);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

/**
 * Render simple markdown safely (bold, italic, line breaks)
 * No innerHTML - builds DOM elements for safety
 */
function renderMarkdown(text) {
    const container = document.createElement('span');

    // Split by lines first to preserve line breaks
    const lines = text.split('\n');

    lines.forEach((line, lineIndex) => {
        // Split by double asterisks for bold
        const parts = line.split(/(\*\*[^*]+\*\*)/g);

        parts.forEach(part => {
            if (part.startsWith('**') && part.endsWith('**')) {
                // Bold text
                const strong = document.createElement('strong');
                strong.textContent = part.slice(2, -2);
                container.appendChild(strong);
            } else {
                // Regular text
                container.appendChild(document.createTextNode(part));
            }
        });

        // Add line break after each line except the last
        if (lineIndex < lines.length - 1) {
            container.appendChild(document.createElement('br'));
        }
    });

    return container;
}

/**
 * Create expandable text with "show more" link
 */
function createExpandableText(text, maxLength = 200) {
    const container = document.createElement('div');
    container.className = 'expandable-text';

    if (text.length <= maxLength) {
        // Short text - just render normally
        container.appendChild(renderMarkdown(text));
        return container;
    }

    // Find a good truncation point (end of word, before maxLength)
    let truncateAt = maxLength;
    while (truncateAt > 0 && text[truncateAt] !== ' ' && text[truncateAt] !== '\n') {
        truncateAt--;
    }
    if (truncateAt === 0) truncateAt = maxLength; // Fallback if no space found

    const truncatedText = text.substring(0, truncateAt).trim();
    const remainingText = text.substring(truncateAt).trim();

    // Create collapsed view
    const collapsedSpan = document.createElement('span');
    collapsedSpan.className = 'text-collapsed';
    collapsedSpan.appendChild(renderMarkdown(truncatedText));

    const ellipsis = document.createElement('span');
    ellipsis.textContent = '... ';
    collapsedSpan.appendChild(ellipsis);

    const expandLink = document.createElement('a');
    expandLink.href = '#';
    expandLink.className = 'expand-link';
    expandLink.textContent = 'show more';
    collapsedSpan.appendChild(expandLink);

    // Create expanded view (hidden initially)
    const expandedSpan = document.createElement('span');
    expandedSpan.className = 'text-expanded';
    expandedSpan.style.display = 'none';
    expandedSpan.appendChild(renderMarkdown(text));

    const collapseLink = document.createElement('a');
    collapseLink.href = '#';
    collapseLink.className = 'collapse-link';
    collapseLink.textContent = ' show less';
    expandedSpan.appendChild(collapseLink);

    // Toggle behavior
    expandLink.onclick = (e) => {
        e.preventDefault();
        collapsedSpan.style.display = 'none';
        expandedSpan.style.display = 'inline';
    };

    collapseLink.onclick = (e) => {
        e.preventDefault();
        collapsedSpan.style.display = 'inline';
        expandedSpan.style.display = 'none';
    };

    container.appendChild(collapsedSpan);
    container.appendChild(expandedSpan);

    return container;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        button.textContent = 'Failed';
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    });
}

/**
 * Setup modal close handlers
 */
function setupModals() {
    // Close buttons
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });

    // Click outside modal to close
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
            document.body.style.overflow = ''; // Restore background scrolling
        }
    });

    // ESC key to close
    window.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
            document.body.style.overflow = ''; // Restore background scrolling
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
