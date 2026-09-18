# Build and verify the teaching image with Podman.
#
# Usage:
#   make build ARCH=arm64 TAG=2026
#   make build ARCH=amd64 TAG=2026
#   make test  ARCH=arm64 TAG=2026
#   make snapshot ARCH=arm64 TAG=2026   # updates the committed stack file
#   make build-agent ARCH=arm64 TAG=2026   # optional Claude Code/opencode/Copilot layer
#   make install-gdsa                       # symlink the gdsa launcher onto PATH
#
# ARCH must be one of: arm64, amd64
# TAG defaults to the current year.

ARCH       ?= arm64
TAG        ?= $(shell date +%Y)
IMG_NM     ?= jreades/sds:$(TAG)-$(ARCH)
AGENT_IMG_NM ?= jreades/sds-agent:$(TAG)-$(ARCH)
GDSA_BIN   ?= $(HOME)/.local/bin/gdsa
STACK_DIR  := docker/stacks
STACK_FILE := $(STACK_DIR)/conda-explicit-$(ARCH).txt

.PHONY: build test snapshot clean-stacks check-arch build-agent install-gdsa

check-arch:
	@case "$(ARCH)" in \
		arm64|amd64) ;; \
		*) echo "ARCH must be arm64 or amd64, got '$(ARCH)'"; exit 1 ;; \
	esac

build: check-arch
	podman build --arch $(ARCH) -t $(IMG_NM) --compress -f ./docker/Podman.master --format docker .

# Depends on build so the image under test always matches the current
# source and this invocation's ARCH/TAG -- otherwise a stale or
# differently-tagged image could be diffed silently and pass or fail
# for the wrong reason.
#
# Runs `conda list --explicit` inside that image and diffs it against
# the committed snapshot. Fails (non-zero exit) if they differ, which
# is the direct check for "every student gets the same image": if
# this passes, the image built here matches what was committed as
# the known-good environment.
test: build
	@test -f $(STACK_FILE) || { echo "No snapshot at $(STACK_FILE) yet -- run 'make snapshot' first."; exit 1; }
	@tmp=$$(mktemp); \
	trap 'rm -f "$$tmp"' EXIT; \
	podman run --rm $(IMG_NM) conda list --explicit > "$$tmp"; \
	diff -u $(STACK_FILE) "$$tmp"

# Regenerates the committed snapshot from a freshly built image. Run
# this deliberately after a build whose package changes are wanted,
# then commit the updated stack file.
snapshot: build
	mkdir -p $(STACK_DIR)
	podman run --rm $(IMG_NM) conda list --explicit > $(STACK_FILE)

clean-stacks:
	rm -rf $(STACK_DIR)

# Builds the optional agent-harness layer (Claude Code, opencode, GitHub
# Copilot CLI) on top of an already-built base image. Doesn't rebuild the
# base image -- run `make build` first if $(IMG_NM) doesn't exist. Harness
# versions are deliberately unpinned (see frontend_agent/README.md), so
# CACHEBUST is set fresh on every build to force reinstalling latest.
build-agent: check-arch
	@podman image exists $(IMG_NM) || { echo "Base image $(IMG_NM) not found -- run 'make build ARCH=$(ARCH) TAG=$(TAG)' first."; exit 1; }
	podman build -t $(AGENT_IMG_NM) \
		--build-arg base_image=$(IMG_NM) \
		--build-arg CACHEBUST=$(shell date +%s) \
		-f ./frontend_agent/Dockerfile \
		--format docker \
		./frontend_agent
	@echo "Built $(AGENT_IMG_NM). Run 'make install-gdsa' once, then 'gdsa help'."

# Symlinks utils/gdsa onto PATH (default ~/.local/bin/gdsa, override with
# GDSA_BIN) and seeds ~/.config/opencode with the baked defaults if missing.
# Idempotent.
install-gdsa:
	@mkdir -p "$(dir $(GDSA_BIN))"
	@ln -sf "$(CURDIR)/utils/gdsa" "$(GDSA_BIN)"
	@echo "Linked $(GDSA_BIN) -> $(CURDIR)/utils/gdsa"
	@mkdir -p "$(HOME)/.local/share/opencode" "$(HOME)/.config/opencode"
	@if [ ! -f "$(HOME)/.config/opencode/opencode.json" ]; then \
		cp "$(CURDIR)/frontend_agent/opencode.json" "$(HOME)/.config/opencode/opencode.json"; \
		echo "Seeded ~/.config/opencode/opencode.json"; \
	fi
	@if [ ! -f "$(HOME)/.config/opencode/tui.json" ]; then \
		cp "$(CURDIR)/frontend_agent/tui.json" "$(HOME)/.config/opencode/tui.json"; \
		echo "Seeded ~/.config/opencode/tui.json"; \
	fi
	@case ":$$PATH:" in \
		*":$(dir $(GDSA_BIN)):"*) echo "$(dir $(GDSA_BIN)) already on PATH." ;; \
		*) echo "Add to PATH: export PATH=\"$(dir $(GDSA_BIN)):\$$PATH\"" ;; \
	esac
