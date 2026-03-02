#!/bin/bash
#
# validate-skills.sh
# Universal skill validation for all agentic collections
#
# Validates skills against:
# - Tier 1: agentskills.io specification (via run-skill-linter.sh)
# - Tier 2: Repository design principles (SKILL_DESIGN_PRINCIPLES.md)
#
# Usage:
#   ./scripts/validate-skills.sh [path]           # Validate specific skill or collection
#   ./scripts/validate-skills.sh                  # Validate all collections
#   ./scripts/validate-skills.sh --strict         # Exit on first error
#

set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_SKILLS=0
PASSED_SKILLS=0
FAILED_SKILLS=0
TOTAL_ERRORS=0

# Flags
STRICT_MODE=false
VERBOSE=false
TARGET_PATHS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [PATH...]"
            echo ""
            echo "Options:"
            echo "  --strict      Exit on first error"
            echo "  --verbose,-v  Show detailed validation steps"
            echo "  --help,-h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Validate all skills in current directory"
            echo "  $0 path/to/collection/               # Validate all skills in collection"
            echo "  $0 path/to/skill-dir/                # Validate single skill"
            echo "  $0 path/to/dir/*                     # Validate multiple paths using glob"
            echo "  $0 skill1/ skill2/ skill3/           # Validate specific skills"
            echo "  $0 --strict path/                    # Exit on first error"
            exit 0
            ;;
        *)
            TARGET_PATHS+=("$1")
            shift
            ;;
    esac
done

# Validation functions

log_info() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}ℹ${NC} $1"
    fi
}

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    ((TOTAL_ERRORS++))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Section 0: agentskills.io Specification Compliance
validate_agentskills_spec() {
    local skill_dir="$1"
    local skill_name=$(basename "$skill_dir")
    local errors=0

    log_info "Validating agentskills.io specification for $skill_name"

    # Check SKILL.md exists
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
        log_error "$skill_name: Missing SKILL.md file"
        ((errors++))
    fi

    # Validate name format (1-64 chars, lowercase, numbers, hyphens only)
    if ! echo "$skill_name" | grep -Eq '^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$'; then
        log_error "$skill_name: Invalid name format (must be 1-64 chars, lowercase, no consecutive hyphens)"
        ((errors++))
    fi

    # Check for consecutive hyphens
    if echo "$skill_name" | grep -q '\-\-'; then
        log_error "$skill_name: Name contains consecutive hyphens (--)"
        ((errors++))
    fi

    # Check name matches directory
    if [[ -f "$skill_dir/SKILL.md" ]]; then
        local frontmatter_name=$(awk '/^---$/{if(++n==2) exit} n==1' "$skill_dir/SKILL.md" | grep '^name:' | sed 's/name: *//' | tr -d '"' | tr -d "'")
        if [[ -n "$frontmatter_name" && "$frontmatter_name" != "$skill_name" ]]; then
            log_error "$skill_name: Name in frontmatter ($frontmatter_name) doesn't match directory name"
            ((errors++))
        fi
    fi

    return $errors
}

# Section 1: YAML Frontmatter
validate_yaml_frontmatter() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating YAML frontmatter for $skill_name"

    # Extract frontmatter (between first two --- markers)
    if ! grep -q '^---$' "$skill_file"; then
        log_error "$skill_name: Missing YAML frontmatter delimiters (---)"
        ((errors++))
        return $errors
    fi

    local frontmatter=$(awk '/^---$/{if(++n==2) exit} n==1' "$skill_file")

    # Check required fields
    if ! echo "$frontmatter" | grep -q '^name:'; then
        log_error "$skill_name: Missing 'name' field in frontmatter"
        ((errors++))
    fi

    if ! echo "$frontmatter" | grep -q '^description:'; then
        log_error "$skill_name: Missing 'description' field in frontmatter"
        ((errors++))
    fi

    # Check model field exists
    if ! echo "$frontmatter" | grep -q '^model:'; then
        log_error "$skill_name: Missing 'model' field in frontmatter (MANDATORY)"
        ((errors++))
    else
        # Validate model value is one of: inherit, sonnet, haiku
        local model_value=$(echo "$frontmatter" | grep '^model:' | sed 's/model: *//' | tr -d '"' | tr -d "'" | xargs)
        if [[ "$model_value" != "inherit" && "$model_value" != "sonnet" && "$model_value" != "haiku" ]]; then
            log_error "$skill_name: Invalid model value '$model_value' (must be: inherit, sonnet, or haiku)"
            ((errors++))
        fi
    fi

    # Check color field exists (MANDATORY)
    if ! echo "$frontmatter" | grep -q '^color:'; then
        log_error "$skill_name: Missing 'color' field in frontmatter (MANDATORY)"
        ((errors++))
    else
        # Validate color value is one of: cyan, green, blue, yellow, red
        local color_value=$(echo "$frontmatter" | grep '^color:' | sed 's/color: *//' | tr -d '"' | tr -d "'" | xargs)
        if [[ "$color_value" != "cyan" && "$color_value" != "green" && "$color_value" != "blue" && "$color_value" != "yellow" && "$color_value" != "red" ]]; then
            log_error "$skill_name: Invalid color value '$color_value' (must be: cyan, green, blue, yellow, or red)"
            ((errors++))
        fi
    fi

    # Check description has "Use when" examples (check in full frontmatter)
    if ! echo "$frontmatter" | grep -qi "use when\|trigger\|request"; then
        log_warn "$skill_name: Description should include 'Use when' examples"
    fi

    # Check description has "NOT for" anti-pattern
    if ! echo "$frontmatter" | grep -qi "NOT for\|Do NOT\|not for"; then
        log_warn "$skill_name: Description should include 'NOT for' anti-pattern"
    fi

    # Check description length (approximate - under 1024 chars per agentskills.io)
    # Extract just the description value
    local description=$(echo "$frontmatter" | awk '/^description:/,/^[a-z_]+:/ {if (!/^[a-z_]+:/ || /^description:/) print}' | sed '1d')
    local desc_length=$(echo "$description" | wc -c)
    if [[ $desc_length -gt 1024 ]]; then
        log_error "$skill_name: Description exceeds 1024 characters ($desc_length chars)"
        ((errors++))
    fi

    return $errors
}

# Section 1.5: SKILL.md Header Format (Section 12 in checklist)
validate_skill_header() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating SKILL.md header format for $skill_name"

    # Extract the first heading after frontmatter
    local first_heading=$(awk '/^---$/{if(++n==2) {getline; while(getline) {if(/^# /) {print; exit}}}}' "$skill_file")

    if [[ -z "$first_heading" ]]; then
        log_error "$skill_name: Missing level 1 heading (# ) after frontmatter"
        ((errors++))
        return $errors
    fi

    # Validate heading format: # /<skill-name> Skill or # [Skill Name]
    # Extract heading text (remove leading "# ")
    local heading_text=$(echo "$first_heading" | sed 's/^# *//')

    # Check if it follows one of the standard formats
    local valid_format=false

    # Format 1: /<skill-name> Skill
    if echo "$heading_text" | grep -Eq "^/$skill_name Skill$"; then
        valid_format=true
    fi

    # Format 2: [Title Case] Skill (flexible matching)
    if echo "$heading_text" | grep -Eq " Skill$"; then
        valid_format=true
    fi

    if [[ "$valid_format" == false ]]; then
        log_warn "$skill_name: Heading '$heading_text' should follow format: '/$skill_name Skill' or '[Skill Name]'"
    fi

    # Check for overview paragraph after heading
    # Get first non-empty line after the heading
    local overview=$(awk '/^---$/{if(++n==2) found=1} found && /^# / {getline; while(getline) {if(/^[^#]/ && NF>0) {print; exit}}}' "$skill_file")

    if [[ -z "$overview" ]]; then
        log_warn "$skill_name: Missing overview paragraph (1-2 sentences) immediately after heading"
    fi

    return $errors
}

# Section 2: Mandatory Section Order
validate_section_order() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating section order for $skill_name"

    # Required sections in order (after frontmatter)
    local required_sections=(
        "^# "
        "^## Prerequisites"
        "^## When to Use This Skill"
        "^## Workflow"
        "^## Dependencies"
    )

    local prev_line=0
    for section in "${required_sections[@]}"; do
        local line_num=$(grep -n "$section" "$skill_file" | head -1 | cut -d: -f1)

        if [[ -z "$line_num" ]]; then
            log_error "$skill_name: Missing required section matching '$section'"
            ((errors++))
            continue
        fi

        if [[ $line_num -le $prev_line ]]; then
            log_error "$skill_name: Section '$section' out of order (line $line_num, expected after line $prev_line)"
            ((errors++))
        fi

        prev_line=$line_num
    done

    return $errors
}

# Section 3: Prerequisites Section
validate_prerequisites() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating Prerequisites section for $skill_name"

    # Check Prerequisites section exists
    if ! grep -q "^## Prerequisites" "$skill_file"; then
        log_error "$skill_name: Missing Prerequisites section"
        ((errors++))
        return $errors
    fi

    # Extract Prerequisites section
    local prereqs=$(awk '/^## Prerequisites$/,/^## [^P]/' "$skill_file")

    # Check for required subsections (relaxed checking)
    if ! echo "$prereqs" | grep -qi "required.*mcp.*server\|mcp.*server"; then
        log_warn "$skill_name: Prerequisites should list Required MCP Servers"
    fi

    if ! echo "$prereqs" | grep -qi "verification\|verify"; then
        log_warn "$skill_name: Prerequisites should include verification steps"
    fi

    if ! echo "$prereqs" | grep -qi "human notification\|error.*protocol"; then
        log_warn "$skill_name: Prerequisites should include human notification protocol"
    fi

    # Check for security warning about credentials
    if ! echo "$prereqs" | grep -qi "never.*display\|never.*expose\|credential.*value"; then
        log_warn "$skill_name: Prerequisites should warn against exposing credentials"
    fi

    return $errors
}

# Section 4: When to Use This Skill
validate_when_to_use() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating 'When to Use' section for $skill_name"

    if ! grep -q "^## When to Use This Skill" "$skill_file"; then
        log_error "$skill_name: Missing 'When to Use This Skill' section"
        ((errors++))
        return $errors
    fi

    local when_section=$(awk '/^## When to Use This Skill$/,/^## [^W]/' "$skill_file")

    # Check for "Use when" scenarios
    if ! echo "$when_section" | grep -qi "use.*when\|trigger.*when\|invoke.*when"; then
        log_warn "$skill_name: 'When to Use' section should list specific scenarios"
    fi

    # Check for "Do NOT use" anti-patterns
    if ! echo "$when_section" | grep -qi "do not\|NOT for\|not when"; then
        log_error "$skill_name: 'When to Use' section must include 'Do NOT use' anti-patterns"
        ((errors++))
    fi

    # Check that anti-patterns mention alternative skills
    if echo "$when_section" | grep -qi "do not\|NOT for" && \
       ! echo "$when_section" | grep -qi "use.*skill\|instead\|alternative"; then
        log_warn "$skill_name: Anti-patterns should reference alternative skills by name"
    fi

    return $errors
}

# Section 5: Workflow Section
validate_workflow() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating Workflow section for $skill_name"

    if ! grep -q "^## Workflow" "$skill_file"; then
        log_error "$skill_name: Missing Workflow section"
        ((errors++))
        return $errors
    fi

    local workflow=$(awk '/^## Workflow$/,/^## [^W]/' "$skill_file")

    # Check for workflow steps
    if ! echo "$workflow" | grep -q "^### Step\|^### [0-9]"; then
        log_warn "$skill_name: Workflow should have numbered steps (### Step N: or ### 1.)"
    fi

    # Check for MCP Tool references
    if ! echo "$workflow" | grep -qi "\*\*MCP Tool\*\*\|mcp.*tool"; then
        log_warn "$skill_name: Workflow should specify MCP Tools used"
    fi

    # Check for Parameters specification
    if echo "$workflow" | grep -qi "\*\*MCP Tool\*\*" && \
       ! echo "$workflow" | grep -qi "\*\*Parameters\*\*"; then
        log_warn "$skill_name: Workflow steps with MCP Tools should specify parameters"
    fi

    # Check for Error Handling
    if ! echo "$workflow" | grep -qi "\*\*Error.*Handling\*\*\|error.*condition"; then
        log_warn "$skill_name: Workflow steps should include error handling"
    fi

    return $errors
}

# Section 6: Document Consultation Transparency
validate_document_consultation() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating document consultation transparency for $skill_name"

    # If skill mentions consulting documents, verify it follows the pattern
    if grep -qi "consult.*document\|read.*doc" "$skill_file"; then
        if ! grep -qi "Read tool\|Read.*to understand" "$skill_file"; then
            log_warn "$skill_name: Document consultation should use Read tool first (CLAUDE.md Principle #1)"
        fi

        if ! grep -qi "I consulted\|Output to user" "$skill_file"; then
            log_warn "$skill_name: Document consultation should declare consultation to user"
        fi
    fi

    return $errors
}

# Section 7: Dependencies Section
validate_dependencies() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating Dependencies section for $skill_name"

    if ! grep -q "^## Dependencies" "$skill_file"; then
        log_error "$skill_name: Missing Dependencies section"
        ((errors++))
        return $errors
    fi

    local deps=$(awk '/^## Dependencies$/,/^## [^D]/' "$skill_file")

    # Check for required subsections
    if ! echo "$deps" | grep -qi "required.*mcp.*server"; then
        log_warn "$skill_name: Dependencies should list Required MCP Servers"
    fi

    if ! echo "$deps" | grep -qi "required.*mcp.*tool\|mcp.*tool"; then
        log_warn "$skill_name: Dependencies should list Required MCP Tools"
    fi

    return $errors
}

# Section 8: Human-in-the-Loop Requirements
validate_human_in_loop() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating Human-in-the-Loop requirements for $skill_name"

    # Check if skill modifies state (create, delete, update, restore, execute)
    local is_mutating=false
    if echo "$skill_name" | grep -Eq "create|delete|update|restore|execute|modify|run|deploy|clone"; then
        is_mutating=true
    fi

    # If mutating, should have Human-in-the-Loop section
    if [[ "$is_mutating" == true ]]; then
        if ! grep -q "^## Critical: Human-in-the-Loop Requirements" "$skill_file"; then
            log_warn "$skill_name: Modifying skill should have 'Human-in-the-Loop Requirements' section"
        else
            local hitl=$(awk '/^## Critical: Human-in-the-Loop Requirements$/,/^## [^C]/' "$skill_file")

            # Check for confirmation requirements
            if ! echo "$hitl" | grep -qi "confirmation\|confirm\|approval\|never assume"; then
                log_warn "$skill_name: Human-in-the-Loop section should specify confirmation requirements"
            fi
        fi
    fi

    return $errors
}

# Section 9: Security Requirements
validate_security() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating security requirements for $skill_name"

    # Check for credential exposure in examples
    if grep -q 'echo \$.*SECRET\|echo \$.*PASSWORD\|echo \$.*TOKEN\|echo \$.*KEY' "$skill_file"; then
        log_error "$skill_name: SECURITY VIOLATION - Exposing credential values with 'echo \$VAR'"
        ((errors++))
    fi

    # Check for hardcoded credentials (common patterns)
    if grep -Eq 'password.*=.*["'"'"'][^$]|secret.*=.*["'"'"'][^$]|token.*=.*["'"'"'][^$]' "$skill_file"; then
        log_warn "$skill_name: Possible hardcoded credentials found (review manually)"
    fi

    # Check for proper credential checking pattern
    if grep -q 'KUBECONFIG\|CLIENT_SECRET\|API_KEY\|TOKEN' "$skill_file"; then
        if grep -q 'test -n.*\$\|if \[ -n.*\$' "$skill_file"; then
            log_info "$skill_name: Uses proper credential checking (test -n)"
        fi
    fi

    return $errors
}

# Section 10: Content Quality
validate_content_quality() {
    local skill_file="$1"
    local skill_name="$2"
    local errors=0

    log_info "Validating content quality for $skill_name"

    # Check for broken markdown links (basic check)
    local broken_links=$(grep -o '\[.*\](.*\.md)' "$skill_file" | grep -o '(.*\.md)' | tr -d '()' || true)
    if [[ -n "$broken_links" ]]; then
        while IFS= read -r link; do
            # Convert relative path to absolute
            local skill_dir=$(dirname "$skill_file")
            local abs_link="$skill_dir/$link"

            # Resolve relative paths (../)
            abs_link=$(cd "$skill_dir" && realpath -m "$link" 2>/dev/null || echo "$abs_link")

            if [[ ! -f "$abs_link" ]]; then
                log_warn "$skill_name: Possibly broken link: $link"
            fi
        done <<< "$broken_links"
    fi

    # Check file size (recommend under 5000 tokens ≈ 20KB for text)
    local file_size=$(wc -c < "$skill_file")
    if [[ $file_size -gt 20480 ]]; then
        log_warn "$skill_name: SKILL.md is large ($file_size bytes). Consider moving content to references/"
    fi

    return $errors
}

# Main validation function
validate_skill() {
    local skill_dir="$1"
    local skill_name=$(basename "$skill_dir")
    local skill_file="$skill_dir/SKILL.md"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Validating:${NC} $skill_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    ((TOTAL_SKILLS++))

    local skill_errors=0

    # Run all validations
    validate_agentskills_spec "$skill_dir" || ((skill_errors+=$?))

    if [[ -f "$skill_file" ]]; then
        validate_yaml_frontmatter "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_skill_header "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_section_order "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_prerequisites "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_when_to_use "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_workflow "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_document_consultation "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_dependencies "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_human_in_loop "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_security "$skill_file" "$skill_name" || ((skill_errors+=$?))
        validate_content_quality "$skill_file" "$skill_name" || ((skill_errors+=$?))
    fi

    # Report skill result
    echo ""
    if [[ $skill_errors -eq 0 ]]; then
        log_pass "Skill '$skill_name' passed validation"
        ((PASSED_SKILLS++))
    else
        log_error "Skill '$skill_name' failed with $skill_errors error(s)"
        ((FAILED_SKILLS++))

        if [[ "$STRICT_MODE" == true ]]; then
            echo ""
            echo -e "${RED}Strict mode enabled. Exiting on first failure.${NC}"
            exit 1
        fi
    fi

    return $skill_errors
}

# Find and validate skills
find_and_validate_skills() {
    local search_path="${1:-.}"

    # Check if path exists
    if [[ ! -e "$search_path" ]]; then
        echo -e "${YELLOW}Path not found: '$search_path'${NC}"
        return 0
    fi

    # If the path directly contains SKILL.md, validate it as a single skill
    if [[ -f "$search_path/SKILL.md" ]]; then
        validate_skill "$search_path"
        return 0
    fi

    # If the path IS a SKILL.md file, validate its parent directory
    if [[ -f "$search_path" && $(basename "$search_path") == "SKILL.md" ]]; then
        local skill_dir=$(dirname "$search_path")
        validate_skill "$skill_dir"
        return 0
    fi

    # Otherwise, search recursively for SKILL.md files
    local skill_files=()
    while IFS= read -r -d '' file; do
        skill_files+=("$file")
    done < <(find "$search_path" -type f -name "SKILL.md" -print0 2>/dev/null)

    if [[ ${#skill_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No skills found in '$search_path'${NC}"
        return 0
    fi

    # Validate each skill
    for skill_file in "${skill_files[@]}"; do
        local skill_dir=$(dirname "$skill_file")
        validate_skill "$skill_dir"
    done
}

# Main execution
main() {
    local repo_root
    repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
    cd "$repo_root" || exit 1

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Universal Skill Validator${NC}"
    echo "Validates skills against SKILL_DESIGN_PRINCIPLES.md"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Determine target paths
    if [[ ${#TARGET_PATHS[@]} -eq 0 ]]; then
        echo -e "Target: ${BLUE}Current directory (.)${NC}"
        TARGET_PATHS=(".")
    else
        echo -e "Target: ${BLUE}${#TARGET_PATHS[@]} path(s) specified${NC}"
    fi

    if [[ "$STRICT_MODE" == true ]]; then
        echo -e "Mode: ${RED}Strict (exit on first error)${NC}"
    fi

    echo ""

    # Run validation on all target paths
    for target_path in "${TARGET_PATHS[@]}"; do
        find_and_validate_skills "$target_path"
    done

    # Print summary
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Validation Summary${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Total Skills:    $TOTAL_SKILLS"
    echo -e "${GREEN}Passed:${NC}          $PASSED_SKILLS"
    echo -e "${RED}Failed:${NC}          $FAILED_SKILLS"
    echo -e "${RED}Total Errors:${NC}    $TOTAL_ERRORS"
    echo ""

    # Exit code
    if [[ $FAILED_SKILLS -eq 0 ]]; then
        echo -e "${GREEN}✓ All skills passed validation${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some skills failed validation${NC}"
        exit 1
    fi
}

# Run main
main "$@"
