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

# TinyTeX is installed separately by tinytex.sh as $NB_UID: running it
# here (as root, with HOME=/home/jovyan) leaves ~/.TinyTeX root-owned
# and tlmgr unable to install missing packages at render time.

apt_cleanup
