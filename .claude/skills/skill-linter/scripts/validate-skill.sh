#!/bin/bash
# Skill Linter - Validates skills against agentskills.io specification
# Usage: ./validate-skill.sh path/to/skill-directory

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

pass() {
  echo -e "${GREEN}[PASS]${NC} $1"
  PASS=$((PASS + 1))
}

fail() {
  echo -e "${RED}[FAIL]${NC} $1"
  FAIL=$((FAIL + 1))
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
  WARN=$((WARN + 1))
}

# Validate arguments
if [ $# -lt 1 ]; then
  echo "Usage: $0 <skill-directory>"
  echo "Example: $0 plugins/majestic-tools/skills/brainstorming"
  exit 1
fi

SKILL_DIR="$1"
SKILL_DIR="${SKILL_DIR%/}" # Remove trailing slash if present

echo ""
echo "Validating: $SKILL_DIR"
echo "-------------------------------------------"

# 1. Check directory exists
if [ ! -d "$SKILL_DIR" ]; then
  fail "Directory does not exist: $SKILL_DIR"
  exit 1
fi

# 2. Check SKILL.md exists
SKILL_FILE="$SKILL_DIR/SKILL.md"
if [ ! -f "$SKILL_FILE" ]; then
  fail "SKILL.md not found"
  exit 1
fi
pass "SKILL.md exists"

# 3. Extract frontmatter
CONTENT=$(cat "$SKILL_FILE")

# Check for frontmatter delimiters
if ! echo "$CONTENT" | head -1 | grep -q '^---$'; then
  fail "Missing frontmatter opening delimiter (---)"
  exit 2
fi

# Find closing delimiter (skip first line)
CLOSING_LINE=$(echo "$CONTENT" | tail -n +2 | grep -n '^---$' | head -1 | cut -d: -f1)
if [ -z "$CLOSING_LINE" ]; then
  fail "Missing frontmatter closing delimiter (---)"
  exit 2
fi
pass "Frontmatter delimiters present"

# Extract frontmatter content (between delimiters) - portable approach
# CLOSING_LINE is position of --- in tail-n+2 output, so frontmatter is lines 2 to CLOSING_LINE in original
FRONTMATTER=$(echo "$CONTENT" | sed -n "2,${CLOSING_LINE}p")

# 4. Validate name field
NAME=$(echo "$FRONTMATTER" | grep '^name:' | sed 's/^name:[[:space:]]*//' | tr -d '"' | tr -d "'")

if [ -z "$NAME" ]; then
  fail "Missing required field: name"
  exit 3
fi

# Check name length (1-64)
NAME_LEN=${#NAME}
if [ "$NAME_LEN" -lt 1 ] || [ "$NAME_LEN" -gt 64 ]; then
  fail "Name length must be 1-64 chars (got $NAME_LEN)"
  exit 3
fi

# Check name pattern: lowercase alphanumeric with hyphens
# Must not start/end with hyphen, no consecutive hyphens
if ! echo "$NAME" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'; then
  # More specific error messages
  if echo "$NAME" | grep -qE '^-'; then
    fail "Name cannot start with hyphen: $NAME"
  elif echo "$NAME" | grep -qE '-$'; then
    fail "Name cannot end with hyphen: $NAME"
  elif echo "$NAME" | grep -qE '--'; then
    fail "Name cannot contain consecutive hyphens: $NAME"
  elif echo "$NAME" | grep -qE '[A-Z]'; then
    fail "Name must be lowercase: $NAME"
  elif echo "$NAME" | grep -qE '[_]'; then
    fail "Name cannot contain underscores (use hyphens): $NAME"
  else
    fail "Name must match pattern ^[a-z][a-z0-9]*(-[a-z0-9]+)*$: $NAME"
  fi
  exit 3
fi
pass "Name '$NAME' valid ($NAME_LEN chars)"

# 5. Check name matches directory
DIR_NAME=$(basename "$SKILL_DIR")
if [ "$NAME" != "$DIR_NAME" ]; then
  fail "Name '$NAME' does not match directory name '$DIR_NAME'"
  exit 3
fi
pass "Name matches directory"

# 6. Validate description field
# Handle multi-line descriptions
DESCRIPTION=$(echo "$FRONTMATTER" | awk '/^description:/{flag=1; sub(/^description:[[:space:]]*/, ""); print; next} flag && /^[a-z_-]+:/{exit} flag{print}' | tr '\n' ' ' | sed 's/[[:space:]]*$//')

if [ -z "$DESCRIPTION" ]; then
  fail "Missing required field: description"
  exit 4
fi

# Check description length (1-1024)
DESC_LEN=${#DESCRIPTION}
if [ "$DESC_LEN" -lt 1 ]; then
  fail "Description cannot be empty"
  exit 4
fi
if [ "$DESC_LEN" -gt 1024 ]; then
  fail "Description exceeds 1024 chars (got $DESC_LEN)"
  exit 4
fi
pass "Description valid ($DESC_LEN chars)"

# 7. Validate optional fields if present

# Check compatibility (if present, max 500 chars)
COMPAT=$(echo "$FRONTMATTER" | grep '^compatibility:' | sed 's/^compatibility:[[:space:]]*//' || true)
if [ -n "$COMPAT" ]; then
  COMPAT_LEN=${#COMPAT}
  if [ "$COMPAT_LEN" -gt 500 ]; then
    fail "Compatibility exceeds 500 chars (got $COMPAT_LEN)"
    exit 5
  fi
  pass "Compatibility valid ($COMPAT_LEN chars)"
fi

# Check allowed-tools (if present)
TOOLS=$(echo "$FRONTMATTER" | grep '^allowed-tools:' | sed 's/^allowed-tools:[[:space:]]*//' || true)
if [ -n "$TOOLS" ]; then
  # FAIL if commas found (must be space-delimited)
  if echo "$TOOLS" | grep -qE ','; then
    fail "allowed-tools must be space-delimited, not comma-separated: $TOOLS"
  # FAIL if bracket array syntax found
  elif echo "$TOOLS" | grep -qE '[\[\]]'; then
    fail "allowed-tools must be space-delimited, not array syntax: $TOOLS"
  else
    pass "Allowed-tools field valid"
  fi
fi
# FAIL if YAML multi-line array detected (allowed-tools:\n  - item)
if echo "$FRONTMATTER" | grep -q '^allowed-tools:$'; then
  NEXT_LINE=$(echo "$FRONTMATTER" | grep -A1 '^allowed-tools:$' | tail -1)
  if echo "$NEXT_LINE" | grep -qE '^[[:space:]]*-[[:space:]]'; then
    fail "allowed-tools must be space-delimited, not YAML array"
  fi
fi

# 8. Check line count (max 500)
LINE_COUNT=$(wc -l < "$SKILL_FILE" | tr -d ' ')
if [ "$LINE_COUNT" -gt 500 ]; then
  fail "Line count exceeds 500 (got $LINE_COUNT)"
  exit 6
fi
pass "Line count: $LINE_COUNT/500"

# 9. Check subdirectories (only scripts/, references/, assets/ allowed)
ALLOWED_DIRS="scripts references assets"
INVALID_DIRS=""
HAS_RESOURCES=false

for subdir in "$SKILL_DIR"/*/; do
  if [ -d "$subdir" ]; then
    subdir_name=$(basename "$subdir")
    if [ "$subdir_name" = "resources" ]; then
      HAS_RESOURCES=true
    elif ! echo "$ALLOWED_DIRS" | grep -qw "$subdir_name"; then
      INVALID_DIRS="$INVALID_DIRS $subdir_name"
    fi
  fi
done

if [ -n "$INVALID_DIRS" ]; then
  warn "Non-standard subdirectories found:$INVALID_DIRS (allowed: scripts, references, assets)"
else
  pass "Subdirectories valid"
fi

if [ "$HAS_RESOURCES" = true ]; then
  warn "resources/ is deprecated — use references/, assets/, scripts/ instead"
fi

# 10. Content analysis - strip fenced code blocks for checks that need prose-only content
CONTENT_NO_FENCES=$(awk '/^```/{skip=!skip; next} !skip{print}' "$SKILL_FILE")

# 10a. Check for ASCII art outside fenced code blocks (WARN)
if echo "$CONTENT_NO_FENCES" | grep -qE '[─│┌┐└┘├┤┬┴┼╭╮╯╰═║╔╗╚╝╠╣╦╩╬↑↓←→↔⇒⇐⇔▲▼◄►]{3,}'; then
  warn "ASCII art detected outside code blocks - use plain lists or tables"
else
  pass "No ASCII art outside code blocks"
fi

# 10b. Check for persona statements outside fenced code blocks (FAIL)
if echo "$CONTENT_NO_FENCES" | grep -qiE '^[[:space:]]*You are (a|an|the) '; then
  fail "Persona statement detected ('You are a/an/the...') - use Audience/Goal framing"
else
  pass "No persona statements"
fi

# 11. Check description routing quality (WARN)
if ! echo "$DESCRIPTION" | grep -qiE "(use when|don't use|not for|triggers on)"; then
  warn "Description lacks routing keywords (use when, don't use, not for, triggers on)"
else
  pass "Description has routing keywords"
fi

# 12. Check for marketing copy in description (WARN)
if echo "$DESCRIPTION" | grep -qiE "(comprehensive|powerful|robust|cutting-edge|world-class|state-of-the-art|best-in-class|game-changing)"; then
  warn "Description contains marketing buzzwords - use precise, functional language"
else
  pass "No marketing copy in description"
fi

# Summary
echo "-------------------------------------------"
echo -e "Result: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$WARN warnings${NC}"

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC}"
  exit 1
fi

if [ "$WARN" -gt 0 ]; then
  echo -e "${YELLOW}PASSED WITH WARNINGS${NC}"
  exit 0
fi

echo -e "${GREEN}ALL CHECKS PASSED${NC}"
exit 0
