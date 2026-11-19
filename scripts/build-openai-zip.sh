#!/usr/bin/env bash
# Builds the package for the ChatGPT and Codex plugin directory
# (platform.openai.com/plugins). It holds the Codex manifest, the LiveKit API MCP
# server config, the skills, the icon, the README, and the license. Bump "version"
# in .codex-plugin/plugin.json before each upload; the portal rejects a version it
# has already seen.
#
# The MCP config lives at .codex-plugin/mcp.json and goes into the ZIP as .mcp.json,
# where the manifest points. It isn't kept at the repo root because Claude Code reads
# a root .mcp.json as this plugin's MCP config too, in a different format.
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(python3 -c 'import json; print(json.load(open(".codex-plugin/plugin.json"))["version"])')
out="$PWD/dist/livekit-openai-${version}.zip"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir -p dist
rm -f "$out"
cp -R .codex-plugin skills assets README.md LICENSE "$stage/"
mv "$stage/.codex-plugin/mcp.json" "$stage/.mcp.json"
(cd "$stage" && zip -qrX "$out" .codex-plugin .mcp.json skills assets README.md LICENSE -x '*.DS_Store')
echo "dist/livekit-openai-${version}.zip"
