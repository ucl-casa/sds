#!/usr/bin/env bash
set -euo pipefail

: "${env_nm:?}" "${NB_USER:?}"

# Rebuilds the font manager cache and warms the black/matplotlib
# import paths so they're not paid for on first notebook run. Bloats
# the image slightly but not by much.
source activate "${env_nm}"

mkdir -p "/home/${NB_USER}/.cache/black/$(black --version | head -n 1 | cut -d ' ' -f 2)"
black --code "print ( 'hello, world' )"
MPLBACKEND=Agg python -c "import matplotlib.pyplot"
python -c "import matplotlib.font_manager;"
python -c "import logging; logging.basicConfig(level='INFO'); import black"

conda deactivate
