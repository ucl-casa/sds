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
set -euo pipefail

apt_install() {
    apt-get update
    apt-get install --no-install-recommends -y "$@"
}

apt_cleanup() {
    apt-get clean
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
}
