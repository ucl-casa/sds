#!/usr/bin/env bash
set -euo pipefail

: "${FONTCONF:?}" "${FONTPATH:?}"

mkdir -p "${FONTCONF}" "${FONTPATH}"

tlmgr init-usertree
fc-cache -f -v
