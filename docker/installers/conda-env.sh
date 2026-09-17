#!/usr/bin/env bash
set -euo pipefail

: "${env_nm:?}" "${yaml_nm:?}"

mamba env update -n "${env_nm}" --file "${yaml_nm}"
mamba clean --all --yes --force-pkgs-dirs
rm "${yaml_nm}"
conda clean --all --yes --force-pkgs-dirs
find "${CONDA_DIR:-/opt/conda}" -follow -type f -name '*.a' -delete
find "${CONDA_DIR:-/opt/conda}" -follow -type f -name '*.pyc' -delete
find "${CONDA_DIR:-/opt/conda}" -follow -type f -name '*.js.map' -delete
pip cache purge
