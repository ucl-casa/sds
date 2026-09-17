#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
. "$SCRIPT_DIR/_lib.sh"

ARCH="${1:?Usage: quarto.sh <TARGETARCH>}"

if [[ "$ARCH" == "arm64" ]]; then
    QUARTO_DEB="quarto-linux-arm64.deb"
else
    QUARTO_DEB="quarto-linux-amd64.deb"
fi

curl -LO "https://quarto.org/download/latest/${QUARTO_DEB}"
gdebi --non-interactive "${QUARTO_DEB}"
rm "${QUARTO_DEB}"

quarto update tool tinytex --no-prompt

apt_cleanup
