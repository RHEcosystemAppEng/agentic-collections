#!/bin/bash
# Skill Specification Linter Reporter
# Runs agentskills.io spec linter on skills and generates detailed error report + summary table
# Usage: ./run-skill-linter.sh [skill-dir1] [skill-dir2] ...
#   No args: validates ALL skills
#   With args: validates only specified skill directories

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Counters
TOTAL_SKILLS=0
PASSED_SKILLS=0
WARNED_SKILLS=0
FAILED_SKILLS=0
HAS_ERRORS=false

# Storage for failed skills details
FAILED_DETAILS_FILE=$(mktemp)
SUMMARY_FILE=$(mktemp)

# Header
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}            Skill Specification Linter Report${NC}"
echo -e "${BOLD}         agentskills.io Specification Compliance${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Determine which skills to validate
if [ $# -eq 0 ]; then
  # No arguments: validate ALL collection skills (exclude .claude/ internal tooling)
  SKILL_PATHS=$(find . -name "SKILL.md" -type f | grep -E "(rh-sre|rh-developer|rh-virt|ocp-admin|rh-support-engineer)/skills/" | sort)
  VALIDATION_MODE="all"
else
  # Arguments provided: validate only specified skill directories
  SKILL_PATHS=""
  for skill_dir in "$@"; do
    # Remove trailing slash if present
    skill_dir="${skill_dir%/}"
    # Add SKILL.md path
    if [ -f "$skill_dir/SKILL.md" ]; then
      SKILL_PATHS="$SKILL_PATHS$skill_dir/SKILL.md"$'\n'
    else
      echo -e "${YELLOW}⚠️  Warning: $skill_dir/SKILL.md not found, skipping${NC}"
    fi
  done
  SKILL_PATHS=$(echo "$SKILL_PATHS" | grep -v '^$' | sort)
  VALIDATION_MODE="changed"
fi

if [ -z "$SKILL_PATHS" ]; then
  echo -e "${BLUE}ℹ️  No skills to validate${NC}"
  exit 0
fi

# Count total skills
TOTAL_SKILLS=$(echo "$SKILL_PATHS" | wc -l | tr -d ' ')

if [ "$VALIDATION_MODE" = "all" ]; then
  echo -e "${BLUE}Validating ALL skills: ${TOTAL_SKILLS} skill(s)${NC}"
else
  echo -e "${BLUE}Validating CHANGED skills: ${TOTAL_SKILLS} skill(s)${NC}"
fi
echo ""

# Validate each skill
while IFS= read -r skill_file; do
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  collection=$(echo "$skill_dir" | cut -d'/' -f2)

  # Run linter and capture output
  LINTER_OUTPUT=$(mktemp)
  ./.claude/skills/skill-linter/scripts/validate-skill.sh "$skill_dir" > "$LINTER_OUTPUT" 2>&1
  EXIT_CODE=$?

  # Parse output for pass/warn/fail
  if [ $EXIT_CODE -eq 0 ]; then
    if grep -q "\[WARN\]" "$LINTER_OUTPUT"; then
      # Passed with warnings
      WARNED_SKILLS=$((WARNED_SKILLS + 1))
      echo -e "⚠️  ${YELLOW}${collection}/${skill_name}${NC} - PASSED WITH WARNINGS"
    else
      # Clean pass
      PASSED_SKILLS=$((PASSED_SKILLS + 1))
      echo -e "✅ ${GREEN}${collection}/${skill_name}${NC}"
    fi
  else
    # Failed
    FAILED_SKILLS=$((FAILED_SKILLS + 1))
    HAS_ERRORS=true
    echo -e "❌ ${RED}${collection}/${skill_name}${NC} - FAILED"

    # Store detailed output for failed skills
    echo "" >> "$FAILED_DETAILS_FILE"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >> "$FAILED_DETAILS_FILE"
    echo -e "${RED}${BOLD}FAILED: ${collection}/${skill_name}${NC}" >> "$FAILED_DETAILS_FILE"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >> "$FAILED_DETAILS_FILE"
    cat "$LINTER_OUTPUT" >> "$FAILED_DETAILS_FILE"
    echo "" >> "$FAILED_DETAILS_FILE"
  fi

  # Store summary entry
  if [ $EXIT_CODE -eq 0 ]; then
    if grep -q "\[WARN\]" "$LINTER_OUTPUT"; then
      echo "${collection}/${skill_name}|⚠️  WARNINGS" >> "$SUMMARY_FILE"
    else
      echo "${collection}/${skill_name}|✅ PASSED" >> "$SUMMARY_FILE"
    fi
  else
    echo "${collection}/${skill_name}|❌ FAILED" >> "$SUMMARY_FILE"
  fi

  rm -f "$LINTER_OUTPUT"
done <<< "$SKILL_PATHS"

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Show detailed errors if any
if [ "$FAILED_SKILLS" -gt 0 ]; then
  echo ""
  echo -e "${RED}${BOLD}DETAILED ERROR REPORT${NC}"
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  cat "$FAILED_DETAILS_FILE"
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
fi

# Summary Table
echo ""
echo -e "${BOLD}VALIDATION SUMMARY${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
printf "${BOLD}%-42s%s${NC}\n" "Metric" "Count"
echo "────────────────────────────────────────────────────────────────"
printf "%-42s${BLUE}%s${NC}\n" "Total Skills:" "$TOTAL_SKILLS"
printf "✅ %-39s${GREEN}%s${NC}\n" "Passed:" "$PASSED_SKILLS"
printf "⚠️  %-40s${YELLOW}%s${NC}\n" "Passed with Warnings:" "$WARNED_SKILLS"
printf "❌ %-39s${RED}%s${NC}\n" "Failed:" "$FAILED_SKILLS"
echo ""

# Status indicator
if [ "$HAS_ERRORS" = true ]; then
  echo -e "${RED}${BOLD}❌ VALIDATION FAILED - ERRORS DETECTED${NC}"
  echo -e "${RED}Skills with errors must be fixed before merge${NC}"
  EXIT_STATUS=1
elif [ "$WARNED_SKILLS" -gt 0 ]; then
  echo -e "${YELLOW}${BOLD}⚠️  PASSED WITH WARNINGS${NC}"
  echo -e "${YELLOW}Review warnings above - PR can be merged${NC}"
  EXIT_STATUS=0
else
  echo -e "${GREEN}${BOLD}✅ ALL SKILLS PASSED${NC}"
  EXIT_STATUS=0
fi

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Additional guidance on errors
if [ "$FAILED_SKILLS" -gt 0 ]; then
  echo -e "${BOLD}How to fix:${NC}"
  echo "1. Review the detailed error report above"
  echo "2. Run locally: ./.claude/skills/skill-linter/scripts/validate-skill.sh <skill-dir>"
  echo "3. See agentskills.io specification: https://agentskills.io/specification"
  echo ""
fi

# Cleanup
rm -f "$FAILED_DETAILS_FILE" "$SUMMARY_FILE"

# Save exit code for workflow
echo "$EXIT_STATUS" > /tmp/skill-linter-exit-code

exit $EXIT_STATUS
