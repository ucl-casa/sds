#!/usr/bin/env bash
# Must run as $NB_UID (not root) so that ~/.TinyTeX stays user-writable
# and Quarto/tlmgr can install missing LaTeX packages at render time.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

quarto install tinytex --no-prompt

TLMGR="$(ls -d "${HOME}"/.TinyTeX/bin/*/)tlmgr"

# The TinyTeX bundle can lag the package repository; tlmgr refuses
# to install anything until it has updated itself.
"${TLMGR}" update --self

# Pre-install packages Quarto's PDF output commonly needs but that
# TinyTeX doesn't ship. One package per line; '#' starts a comment.
PKGS="$(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "${SCRIPT_DIR}/tex-packages.txt")"
if [[ -n "${PKGS}" ]]; then
    # shellcheck disable=SC2086
    "${TLMGR}" install ${PKGS}
fi

# Drop downloaded package archives; they're not needed after install.
rm -rf "${HOME}/.TinyTeX/tlpkg/backups"/*
