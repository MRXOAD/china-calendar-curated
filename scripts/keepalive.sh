#!/usr/bin/env bash
set -euo pipefail

# A weekly check keeps the largest normal gap below GitHub's 60-day limit.
last_commit=$(git log -1 --format=%ct)
now=$(date +%s)
if (( now - last_commit < 30 * 24 * 60 * 60 )); then
  echo "Repository activity is recent; no keepalive commit needed."
  exit 0
fi

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git commit --allow-empty -m 'chore: keep calendar publishing active [skip ci]'
# GITHUB_TOKEN pushes do not trigger another workflow run or Pages deployment.
# A concurrent main update rejects this push; report the failure without force.
git push origin HEAD:main
