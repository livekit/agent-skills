#!/usr/bin/env bash
# Builds the skills-only package for the ChatGPT and Codex plugin directory
# (platform.openai.com/plugins). It holds the Codex manifest, the skills, the icon,
# the README, and the license. Bump "version" in .codex-plugin/plugin.json before
# each upload; the portal rejects a version it has already seen.
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(python3 -c 'import json; print(json.load(open(".codex-plugin/plugin.json"))["version"])')
out="dist/livekit-openai-${version}.zip"
mkdir -p dist
rm -f "$out"
zip -qrX "$out" .codex-plugin skills assets README.md LICENSE -x '*.DS_Store'
echo "$out"
