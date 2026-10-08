#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
. "$SCRIPT_DIR/_lib.sh"

# gcc/g++ are needed on ARM builds because spacy compiles from source there.
# LaTeX comes from TinyTeX (tinytex.sh), not Debian's texlive packages.
apt_install \
    gcc \
    g++ \
    librsvg2-bin \
    fontconfig \
    gdebi-core \
    xz-utils

apt_cleanup
