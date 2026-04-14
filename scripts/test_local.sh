#!/bin/bash

# Exit on any error
set -e

echo "🧪 Running local tests..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check data.json exists
echo -n "1. Checking data.json exists... "
if [ -f "docs/data.json" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: docs/data.json not found"
    exit 1
fi

# Test 2: Validate JSON syntax
echo -n "2. Validating JSON syntax... "
if python -m json.tool docs/data.json > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Invalid JSON in docs/data.json"
    exit 1
fi

# Test 3: Check required HTML files
echo -n "3. Checking HTML files... "
missing_files=()
for file in index.html styles.css app.js .nojekyll; do
    if [ ! -f "docs/$file" ]; then
        missing_files+=("$file")
    fi
done
if [ ${#missing_files[@]} -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Missing files: ${missing_files[*]}"
    exit 1
fi

# Test 4: Verify data.json structure
echo -n "4. Verifying data.json structure... "
python - <<EOF
import json
import sys

with open('docs/data.json') as f:
    data = json.load(f)

# Check required top-level keys
required_keys = ['repository', 'packs', 'mcp_servers', 'generated_at']
missing = [k for k in required_keys if k not in data]
if missing:
    print(f"Missing keys: {missing}")
    sys.exit(1)

# Check repository structure
if 'name' not in data['repository']:
    print("Missing repository.name")
    sys.exit(1)

# Check packs structure
if not isinstance(data['packs'], list):
    print("packs should be a list")
    sys.exit(1)

# Check each pack has required fields
for pack in data['packs']:
    if 'name' not in pack or 'plugin' not in pack:
        print(f"Pack missing required fields: {pack.get('name', 'unknown')}")
        sys.exit(1)

# Check MCP servers structure
if not isinstance(data['mcp_servers'], list):
    print("mcp_servers should be a list")
    sys.exit(1)

print("OK", end='')
EOF
echo -e " ${GREEN}✓${NC}"

# Test 5: Count discovered packs and MCP servers
echo -n "5. Counting discovered items... "
PACK_COUNT=$(python -c "import json; print(len(json.load(open('docs/data.json'))['packs']))")
MCP_COUNT=$(python -c "import json; print(len(json.load(open('docs/data.json'))['mcp_servers']))")
SKILL_COUNT=$(python -c "import json; packs = json.load(open('docs/data.json'))['packs']; print(sum(len(p['skills']) for p in packs))")
AGENT_COUNT=$(python -c "import json; packs = json.load(open('docs/data.json'))['packs']; print(sum(len(p['agents']) for p in packs))")

echo -e "${GREEN}✓${NC}"
echo ""
echo "   Found:"
echo "   - ${PACK_COUNT} agentic collections"
echo "   - ${SKILL_COUNT} skills"
echo "   - ${AGENT_COUNT} agents"
echo "   - ${MCP_COUNT} MCP servers"

# Test 6: Check for XSS vulnerabilities in JavaScript
echo -n "6. Checking for XSS vulnerabilities... "
if grep -q "innerHTML.*\${" docs/app.js 2>/dev/null; then
    echo -e "${RED}✗${NC}"
    echo "Warning: Potential XSS vulnerability detected (innerHTML with template literal)"
    exit 1
elif grep -q "\.innerHTML\s*=" docs/app.js 2>/dev/null; then
    # Check if innerHTML is only used for static content (numbers/counts)
    if grep "\.innerHTML\s*=" docs/app.js | grep -v "stats\.innerHTML" > /dev/null; then
        echo -e "${YELLOW}⚠${NC}"
        echo "Warning: innerHTML usage detected - verify it's safe"
    else
        echo -e "${GREEN}✓${NC}"
    fi
else
    echo -e "${GREEN}✓${NC}"
fi

# Test 7: Verify no hardcoded credentials in MCP configs
echo -n "7. Checking for hardcoded credentials... "
if python - <<EOF
import json
import sys

with open('docs/data.json') as f:
    data = json.load(f)

# Check for non-variable env values (should all be uppercase with underscores)
    for server in data['mcp_servers']:
        for env_var in server.get('env', []):
            # Accept standard placeholder-style names: UPPER_SNAKE or all-caps (e.g. KUBECONFIG)
            if not env_var.isupper():
                print(f"Suspicious env var: {env_var} in {server['name']}")
                sys.exit(1)
            if not (env_var.replace("_", "").isalnum() and env_var.replace("_", "").isupper()):
                print(f"Suspicious env var: {env_var} in {server['name']}")
                sys.exit(1)

print("OK", end='')
EOF
then
    echo -e " ${GREEN}✓${NC}"
else
    echo -e " ${RED}✗${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run 'make serve' to start local server"
echo "  2. Visit http://localhost:8000 in your browser"
echo "  3. Test search, collapsible sections, and modals"
echo "  4. Verify pack and MCP server cards display correctly"
