/**
 * agentic-collections Documentation Site
 *
 * SECURITY: All DOM manipulation uses textContent and createElement
 * to prevent XSS vulnerabilities. No innerHTML with user data.
 */

let data = null;
let allPacks = [];
let allMCPServers = [];
let allCommunityMCPServers = [];

/**
 * Update toolbar counter badges
 */
function updateToolbarCounters(packs, mcpServers, communityMCPServers) {
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
    document.querySelector('#mcp-badge .counter-number').textContent = mcpServers.length + communityMCPServers.length;
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
        
        // Separate MCP servers by tier
        allMCPServers = data.mcp_servers.filter(server => server.tier !== 'Community');
        allCommunityMCPServers = data.mcp_servers.filter(server => server.tier === 'Community');

        // Update toolbar counters
        updateToolbarCounters(allPacks, allMCPServers, allCommunityMCPServers);

        // Render sections
        renderPacks(allPacks);
        renderMCPServers(allMCPServers);
        renderCommunityMCPServers(allCommunityMCPServers);

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

    // Pack name with icon
    const h3 = document.createElement('h3');
    h3.style.display = 'flex';
    h3.style.alignItems = 'center';
    h3.style.gap = '0.5rem';
    
    // Custom icon (if available)
    if (pack.icon) {
        const customIcon = document.createElement('span');
        customIcon.className = 'card-icon';
        customIcon.textContent = pack.icon;
        customIcon.style.fontSize = '1.2rem';
        h3.appendChild(customIcon);
    }
    
    const titleText = document.createElement('span');
    titleText.textContent = pack.plugin.title || pack.plugin.name || pack.name;
    h3.appendChild(titleText);
    
    div.appendChild(h3);

    // Owner subtitle
    const owner = document.createElement('p');
    owner.className = 'pack-owner';
    owner.textContent = 'By Red Hat';
    owner.style.color = 'var(--text-muted)';
    owner.style.fontSize = '0.85rem';
    owner.style.marginTop = '0.25rem';
    div.appendChild(owner);

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

    // Add MCP count (count MCP servers for this pack - both Official and Community)
    const mcpCount = [...allMCPServers, ...allCommunityMCPServers].filter(server => server.pack === pack.name).length;
    if (mcpCount > 0) {
        const mcpSpan = document.createElement('span');
        mcpSpan.textContent = `${mcpCount} MCP`;
        stats.appendChild(mcpSpan);
    }

    div.appendChild(stats);

    // View details link
    const link = document.createElement('a');
    link.className = 'card-link';
    link.textContent = 'View details';
    link.href = '#';
    link.onclick = (e) => {
        e.preventDefault();
        showPackDetails(pack.name);
    };
    div.appendChild(link);

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
 * Render Community MCP servers grid
 */
function renderCommunityMCPServers(servers) {
    const grid = document.getElementById('community-mcp-grid');
    const count = document.getElementById('community-mcp-count');

    // Clear existing content
    grid.textContent = '';
    count.textContent = `(${servers.length})`;

    if (servers.length === 0) {
        const noResults = document.createElement('p');
        noResults.textContent = 'No community MCP servers found matching your search.';
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

    // Server title with icon
    const h3 = document.createElement('h3');
    h3.style.display = 'flex';
    h3.style.alignItems = 'center';
    h3.style.gap = '0.5rem';
    
    // Custom icon (if available)
    if (server.icon) {
        const customIcon = document.createElement('span');
        customIcon.className = 'card-icon';
        customIcon.textContent = server.icon;
        customIcon.style.fontSize = '1.2rem';
        h3.appendChild(customIcon);
    }
    
    const titleText = document.createElement('span');
    titleText.textContent = server.title || server.name;
    h3.appendChild(titleText);
    
    // HTTP remote indicator (if applicable)
    if (server.type === 'http') {
        const icon = document.createElement('span');
        icon.textContent = '🌐';
        icon.title = 'HTTP Remote Server';
        icon.style.fontSize = '1rem';
        h3.appendChild(icon);
    }
    
    div.appendChild(h3);

    // Owner subtitle
    const owner = document.createElement('p');
    owner.className = 'mcp-owner';
    owner.textContent = `By ${server.owner || 'Red Hat'}`;
    owner.style.color = 'var(--text-muted)';
    owner.style.fontSize = '0.85rem';
    owner.style.marginTop = '0.25rem';
    div.appendChild(owner);

    // Type and connection info
    const connectionInfo = document.createElement('p');
    connectionInfo.className = 'container';

    if (server.type === 'http') {
        // HTTP remote server
        connectionInfo.textContent = `Type: HTTP Remote`;
    } else {
        // Container-based server
        connectionInfo.textContent = `Type: Container`;
    }

    div.appendChild(connectionInfo);

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

    // View details link
    const link = document.createElement('a');
    link.className = 'card-link';
    link.textContent = 'View details';
    link.href = '#';
    link.style.marginTop = 'auto';
    link.onclick = (e) => {
        e.preventDefault();
        showMCPDetails(server.name, server.pack);
    };
    div.appendChild(link);

    return div;
}

/**
 * Handle search input
 */
function handleSearch(event) {
    const query = event.target.value.toLowerCase().trim();

    if (!query) {
        // Reset to show all
        updateToolbarCounters(allPacks, allMCPServers, allCommunityMCPServers);
        renderPacks(allPacks);
        renderMCPServers(allMCPServers);
        renderCommunityMCPServers(allCommunityMCPServers);
        return;
    }

    // Filter packs
    const filteredPacks = allPacks.filter(pack => {
        // Search in pack name, title, description, skills, agents
        const searchText = [
            pack.name,
            pack.plugin.name,
            pack.plugin.title,
            pack.plugin.description,
            ...pack.skills.map(s => s.name + ' ' + s.description),
            ...pack.agents.map(a => a.name + ' ' + a.description)
        ].join(' ').toLowerCase();

        return searchText.includes(query);
    });

    // Helper function to filter MCP servers
    const filterMCPServers = (servers) => servers.filter(server => {
        // Search in server name, title, owner, pack, command/URL, env vars
        const searchFields = [
            server.name,
            server.title,
            server.owner,
            server.pack,
            server.type,
            ...server.env
        ];

        // Add type-specific fields
        if (server.type === 'http') {
            searchFields.push(server.url);
            if (server.headers) {
                searchFields.push(...Object.keys(server.headers));
            }
        } else {
            searchFields.push(server.command);
        }

        const searchText = searchFields.join(' ').toLowerCase();
        return searchText.includes(query);
    });

    // Filter MCP servers
    const filteredServers = filterMCPServers(allMCPServers);
    const filteredCommunityServers = filterMCPServers(allCommunityMCPServers);

    // Update counters to reflect filtered results
    updateToolbarCounters(filteredPacks, filteredServers, filteredCommunityServers);
    renderPacks(filteredPacks);
    renderMCPServers(filteredServers);
    renderCommunityMCPServers(filteredCommunityServers);
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
    h2.textContent = pack.plugin.title || pack.plugin.name || pack.name;
    titleGroup.appendChild(h2);

    // Owner subtitle
    const ownerSubtitle = document.createElement('div');
    ownerSubtitle.className = 'pack-owner-subtitle';
    ownerSubtitle.textContent = 'By Red Hat';
    ownerSubtitle.style.color = 'var(--text-muted)';
    ownerSubtitle.style.fontSize = '0.95rem';
    ownerSubtitle.style.marginTop = '0.5rem';
    titleGroup.appendChild(ownerSubtitle);

    // Counts (skills + agents + MCPs)
    const counts = document.createElement('div');
    counts.className = 'modal-counts';
    const countParts = [];
    if (pack.skills.length > 0) {
        countParts.push(`${pack.skills.length} skill${pack.skills.length !== 1 ? 's' : ''}`);
    }
    if (pack.agents.length > 0) {
        countParts.push(`${pack.agents.length} agent${pack.agents.length !== 1 ? 's' : ''}`);
    }
    // Count both Official and Community MCPs for this pack
    const packMCPCount = [...allMCPServers, ...allCommunityMCPServers].filter(server => server.pack === pack.name).length;
    if (packMCPCount > 0) {
        countParts.push(`${packMCPCount} MCP`);
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

    // Plugin name field (if different from title)
    if (pack.plugin.name && pack.plugin.name !== pack.plugin.title) {
        const pluginNameDiv = document.createElement('div');
        pluginNameDiv.style.marginTop = '1rem';
        pluginNameDiv.style.fontSize = '0.9rem';
        pluginNameDiv.style.color = 'var(--text-muted)';
        
        const label = document.createElement('strong');
        label.textContent = 'Plugin name: ';
        label.style.color = 'var(--text-primary)';
        pluginNameDiv.appendChild(label);
        
        const nameCode = document.createElement('code');
        nameCode.textContent = pack.plugin.name;
        nameCode.style.backgroundColor = 'rgba(238, 0, 0, 0.1)';
        nameCode.style.padding = '0.25rem 0.5rem';
        nameCode.style.borderRadius = '4px';
        nameCode.style.fontSize = '0.85rem';
        pluginNameDiv.appendChild(nameCode);
        
        header.appendChild(pluginNameDiv);
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

    // MCP section (shown last, if MCP servers exist for this pack)
    // Include both Official and Community MCP servers for this pack
    const packMCPServers = [...allMCPServers, ...allCommunityMCPServers].filter(server => server.pack === pack.name);
    if (packMCPServers.length > 0) {
        const mcpSection = document.createElement('div');
        mcpSection.className = 'modal-section';

        const mcpHeader = document.createElement('div');
        mcpHeader.className = 'modal-section-header';
        mcpHeader.textContent = 'MCP';
        mcpSection.appendChild(mcpHeader);

        const mcpList = document.createElement('div');
        mcpList.className = 'item-list';

        packMCPServers.forEach(server => {
            const mcpDef = document.createElement('div');
            mcpDef.className = 'skill-definition mcp-link-item';
            mcpDef.style.cursor = 'pointer';
            mcpDef.style.transition = 'all 0.2s ease';
            mcpDef.style.borderLeft = '3px solid transparent';
            mcpDef.style.paddingLeft = '1rem';

            // MCP server name with icon and arrow (clickable)
            const nameBlock = document.createElement('div');
            nameBlock.className = 'definition-syntax';
            nameBlock.style.display = 'flex';
            nameBlock.style.alignItems = 'center';
            nameBlock.style.gap = '0.5rem';
            nameBlock.style.justifyContent = 'space-between';
            
            const nameGroup = document.createElement('div');
            nameGroup.style.display = 'flex';
            nameGroup.style.alignItems = 'center';
            nameGroup.style.gap = '0.5rem';
            
            // Custom icon (if available)
            if (server.icon) {
                const customIcon = document.createElement('span');
                customIcon.className = 'item-icon';
                customIcon.textContent = server.icon;
                customIcon.style.fontSize = '0.9rem';
                nameGroup.appendChild(customIcon);
            }
            
            const nameCode = document.createElement('code');
            nameCode.textContent = server.title || server.name;
            nameCode.style.color = 'var(--primary)';
            nameGroup.appendChild(nameCode);
            
            // HTTP remote indicator (if applicable)
            if (server.type === 'http') {
                const icon = document.createElement('span');
                icon.textContent = '🌐';
                icon.title = 'HTTP Remote Server';
                icon.style.fontSize = '0.9rem';
                nameGroup.appendChild(icon);
            }
            
            nameBlock.appendChild(nameGroup);
            
            // Add arrow indicator
            const arrow = document.createElement('span');
            arrow.textContent = '→';
            arrow.style.color = 'var(--text-muted)';
            arrow.style.fontSize = '1.2rem';
            arrow.style.transition = 'transform 0.2s ease';
            nameBlock.appendChild(arrow);
            
            mcpDef.appendChild(nameBlock);

            // MCP owner subtitle
            const ownerText = document.createElement('div');
            ownerText.className = 'definition-description';
            ownerText.textContent = `By ${server.owner || 'Red Hat'}`;
            ownerText.style.color = 'var(--text-muted)';
            ownerText.style.fontSize = '0.85rem';
            ownerText.style.marginTop = '0.25rem';
            mcpDef.appendChild(ownerText);

            // Hover effects
            mcpDef.onmouseenter = () => {
                mcpDef.style.borderLeftColor = 'var(--primary)';
                mcpDef.style.backgroundColor = 'rgba(238, 0, 0, 0.05)';
                arrow.style.transform = 'translateX(4px)';
            };
            
            mcpDef.onmouseleave = () => {
                mcpDef.style.borderLeftColor = 'transparent';
                mcpDef.style.backgroundColor = 'transparent';
                arrow.style.transform = 'translateX(0)';
            };

            // Click to open MCP details
            mcpDef.onclick = () => showMCPDetails(server.name, server.pack);

            mcpList.appendChild(mcpDef);
        });

        mcpSection.appendChild(mcpList);
        body.appendChild(mcpSection);
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
    h2.style.display = 'flex';
    h2.style.alignItems = 'center';
    h2.style.gap = '0.5rem';
    
    // Custom icon (if available)
    if (server.icon) {
        const customIcon = document.createElement('span');
        customIcon.className = 'card-icon';
        customIcon.textContent = server.icon;
        customIcon.style.fontSize = '1.8rem';
        h2.appendChild(customIcon);
    }
    
    const titleText = document.createElement('span');
    titleText.textContent = server.title || server.name;
    h2.appendChild(titleText);
    
    // HTTP remote indicator (if applicable)
    if (server.type === 'http') {
        const icon = document.createElement('span');
        icon.textContent = '🌐';
        icon.title = 'HTTP Remote Server';
        icon.style.fontSize = '1.5rem';
        h2.appendChild(icon);
    }
    
    titleGroup.appendChild(h2);

    // Owner subtitle
    const ownerSubtitle = document.createElement('div');
    ownerSubtitle.className = 'mcp-owner-subtitle';
    ownerSubtitle.textContent = `By ${server.owner || 'Red Hat'}`;
    ownerSubtitle.style.color = 'var(--text-muted)';
    ownerSubtitle.style.fontSize = '0.95rem';
    ownerSubtitle.style.marginTop = '0.5rem';
    titleGroup.appendChild(ownerSubtitle);

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

    // Connection section (command or URL based on type)
    if (server.type === 'http') {
        // URL section for HTTP servers
        const urlSection = document.createElement('div');
        urlSection.className = 'modal-section';

        const urlHeader = document.createElement('div');
        urlHeader.className = 'modal-section-header';
        urlHeader.textContent = 'ENDPOINT URL';
        urlSection.appendChild(urlHeader);

        const urlCodeWrapper = document.createElement('div');
        urlCodeWrapper.className = 'install-code-wrapper';

        const urlPre = document.createElement('pre');
        const urlCode = document.createElement('code');
        urlCode.textContent = server.url;
        urlPre.appendChild(urlCode);
        urlCodeWrapper.appendChild(urlPre);

        const urlCopyBtn = document.createElement('button');
        urlCopyBtn.className = 'copy-button';
        urlCopyBtn.textContent = 'Copy';
        urlCopyBtn.onclick = () => copyToClipboard(urlCode.textContent, urlCopyBtn);
        urlCodeWrapper.appendChild(urlCopyBtn);

        urlSection.appendChild(urlCodeWrapper);
        body.appendChild(urlSection);

        // Headers section for HTTP servers
        if (server.headers && Object.keys(server.headers).length > 0) {
            const headersSection = document.createElement('div');
            headersSection.className = 'modal-section';

            const headersHeader = document.createElement('div');
            headersHeader.className = 'modal-section-header';
            headersHeader.textContent = 'HTTP HEADERS';
            headersSection.appendChild(headersHeader);

            const headersList = document.createElement('ul');
            headersList.className = 'simple-list';

            Object.entries(server.headers).forEach(([key, value]) => {
                const li = document.createElement('li');
                const strong = document.createElement('strong');
                strong.textContent = `${key}: `;
                li.appendChild(strong);
                li.appendChild(document.createTextNode(value));
                headersList.appendChild(li);
            });

            headersSection.appendChild(headersList);
            body.appendChild(headersSection);
        }
    } else {
        // Command section for command-based servers
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
    }

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

    // Security section (only for command-based servers)
    if (server.type !== 'http' && server.security && Object.keys(server.security).length > 0) {
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
    }

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
