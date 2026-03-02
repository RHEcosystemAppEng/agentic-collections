#!/usr/bin/env bash
# Detect changed skills in CI (PRs and pushes to main)
# Outputs ALL skills in affected packs (not just changed skills)
# Exits 0 if no skills changed
#
# Strategy: If ANY skill changes in a pack (e.g., rh-virt),
#           validate ALL skills in that pack for consistency

set -e

if [ -n "$VALIDATE_INCLUDE_UNCOMMITTED" ]; then
  # Local dev: include staged + unstaged changes vs HEAD
  DIFF_CMD="git diff --name-only HEAD"
elif [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
  # Three-dot diff: merge-base(base, HEAD)..HEAD = changes in the PR
  BASE_REF="${GITHUB_BASE_REF:-main}"
  git fetch origin "$BASE_REF" 2>/dev/null || true
  DIFF_CMD="git diff --name-only origin/$BASE_REF...HEAD"
elif [ "$GITHUB_EVENT_NAME" = "push" ]; then
  # Push event: diff between before and after
  BEFORE="${GITHUB_EVENT_BEFORE:-}"
  if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
    # No base commit for diff, exit with no changes
    exit 0
  fi
  DIFF_CMD="git diff --name-only $BEFORE HEAD"
else
  # Default: local dev, include uncommitted changes
  DIFF_CMD="git diff --name-only HEAD"
fi

# Find changed SKILL.md files
# Exclude .claude/ directory (internal tooling, not subject to same validation)
CHANGED_FILES=$($DIFF_CMD 2>/dev/null | grep -E '^[^/]+/skills/[^/]+/SKILL\.md$' | grep -v '^\.claude/' || true)

if [ -z "$CHANGED_FILES" ]; then
  exit 0
fi

# Extract unique pack names (rh-virt, rh-sre, etc.)
AFFECTED_PACKS=$(echo "$CHANGED_FILES" | cut -d'/' -f1 | sort -u)

# For each affected pack, find ALL skills in that pack
for pack in $AFFECTED_PACKS; do
  find "$pack/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort
done
