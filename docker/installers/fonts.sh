#!/usr/bin/env bash
set -euo pipefail

: "${FONTCONF:?}" "${FONTPATH:?}"

mkdir -p "${FONTCONF}" "${FONTPATH}"

tlmgr init-usertree
fc-cache -f -v

# Build the luaotfload font-name DB as the notebook user, after the
# fonts are in place, so lualatex doesn't rebuild it on first render.
luaotfload-tool -u -v
