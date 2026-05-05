#!/usr/bin/env bash
# Detect packs with changed files in CI (PRs and pushes to main)
# Outputs unique pack names (one per line) for security scanning
# Exits 0 if no packs changed
#
# Detects changes in ANY file within a pack directory (skills, mcps.json, docs, etc.)

set -e

if [ -n "$VALIDATE_INCLUDE_UNCOMMITTED" ]; then
  DIFF_CMD="git diff --name-only HEAD"
elif [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
  BASE_REF="${GITHUB_BASE_REF:-main}"
  git fetch origin "$BASE_REF" 2>/dev/null || true
  DIFF_CMD="git diff --name-only origin/$BASE_REF...HEAD"
elif [ "$GITHUB_EVENT_NAME" = "push" ]; then
  BEFORE="${GITHUB_EVENT_BEFORE:-}"
  if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
    exit 0
  fi
  DIFF_CMD="git diff --name-only $BEFORE HEAD"
else
  DIFF_CMD="git diff --name-only HEAD"
fi

CHANGED_FILES=$($DIFF_CMD 2>/dev/null || true)

if [ -z "$CHANGED_FILES" ]; then
  exit 0
fi

# Extract pack names: first path component of files that live inside a pack with a skills/ directory
# Exclude dotfiles (.github, .claude, etc.)
echo "$CHANGED_FILES" \
  | grep -v '^\.' \
  | cut -d'/' -f1 \
  | sort -u \
  | while read -r dir; do
      if [ -d "$dir/skills" ]; then
        echo "$dir"
      fi
    done
