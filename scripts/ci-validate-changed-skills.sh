#!/usr/bin/env bash
# Validate only changed skills in CI (PRs and pushes to main).
# Exits 0 if no skills changed or all changed skills pass validation.
#
# Local dev: set VALIDATE_INCLUDE_UNCOMMITTED=1 to include staged and unstaged changes.

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
    echo "No base commit for diff, skipping skill design validation"
    exit 0
  fi
  DIFF_CMD="git diff --name-only $BEFORE HEAD"
else
  # Default: local dev, include uncommitted changes
  DIFF_CMD="git diff --name-only HEAD"
fi

CHANGED=$($DIFF_CMD 2>/dev/null | grep -E '^([^/]+/skills/[^/]+/SKILL\.md|\.claude/skills/[^/]+/SKILL\.md)$' || true)

if [ -z "$CHANGED" ]; then
  echo "No skills changed, skipping skill design validation"
  exit 0
fi

echo "Validating changed skills:"
echo "$CHANGED" | sed 's/^/  - /'

# Run validator on changed skills only
uv run python scripts/validate_skill_design.py $(echo "$CHANGED" | tr '\n' ' ')
