#!/usr/bin/env bash
# Shared helpers for docker/installers/*.sh
#
# Cleanup must happen inside the SAME RUN (and therefore the same
# image layer) as the install it follows. Container layers are
# immutable, so running `apt-get clean` or `rm -rf` in a later RUN
# does not shrink the layer that already committed the cache files —
# it only hides them behind a whiteout while the bytes stay in the
# image. Every installer script below is invoked as a single RUN and
# is responsible for cleaning up after itself before it exits.
#
# Ownership: the base image keeps HOME=/home/jovyan even under
# `USER root`, so anything run as root that touches $HOME (or
# $CONDA_DIR) leaves root-owned files the notebook user can't modify.
# This has broken Quarto/TinyTeX (tlmgr can't install packages),
# luaotfload and matplotlib before. Only run as root what genuinely
# needs it (apt, .deb installs); everything else runs as $NB_UID.
# In Podman.master, COPY/ADD into user space needs
# --chown=${NB_UID}:${NB_GID} (COPY ignores USER). Don't fix this with
# a recursive chown -- it duplicates the whole tree into a new layer.
# `make check` verifies ownership in a built image.
set -euo pipefail

apt_install() {
    apt-get update
    apt-get install --no-install-recommends -y "$@"
}

apt_cleanup() {
    apt-get clean
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
}
