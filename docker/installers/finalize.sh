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
rm -rf "/home/${NB_USER}/.cache/quarto"
rm -rf "/home/${NB_USER}/.cache/deno"

luaotfload-tool -v -vvv -u

for kdtree in "${CONDA_DIR}"/lib/python*/site-packages/libpysal/cg/kdtree.py; do
    if [ -f "$kdtree" ]; then
        perl -i -p -e 's|from scipy import inf|from numpy import inf|' "$kdtree"
    fi
done

# Ensure all student home directories and fonts are cleanly owned by jovyan:users
chown -R "${NB_UID:-1000}:${NB_GID:-100}" "/home/${NB_USER}"

rm -rf /tmp/installers
