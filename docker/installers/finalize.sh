#!/usr/bin/env bash
set -euo pipefail

: "${NB_USER:?}" "${CONDA_DIR:?}"

jupyter labextension disable "@jupyterlab/apputils-extension:announcements"
jupyter lab clean -y
conda clean --all -f -y

rm -rf "${CONDA_DIR}/share/jupyter/lab/staging"
rm -rf "/home/${NB_USER}/.node-gyp"/*
rm -rf "/home/${NB_USER}/.local"/*
rm -rf "/home/${NB_USER}/.cache/rosetta"
rm -rf "/home/${NB_USER}/.cache/yarn"
rm -rf "/home/${NB_USER}/.cache/pip"

luaotfload-tool -v -vvv -u

perl -i -p -e 's|from scipy import inf|from numpy import inf|' \
    "${CONDA_DIR}/lib/python3.13/site-packages/libpysal/cg/kdtree.py"

rm -rf /tmp/installers
