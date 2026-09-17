# Build and verify the teaching image with Podman.
#
# Usage:
#   make build ARCH=arm64 TAG=2026
#   make build ARCH=amd64 TAG=2026
#   make test  ARCH=arm64 TAG=2026
#   make snapshot ARCH=arm64 TAG=2026   # updates the committed stack file
#
# ARCH must be one of: arm64, amd64
# TAG defaults to the current year.

ARCH   ?= arm64
TAG    ?= $(shell date +%Y)
IMG_NM ?= jreades/sds:$(TAG)-$(ARCH)
STACK_DIR := docker/stacks
STACK_FILE := $(STACK_DIR)/conda-explicit-$(ARCH).txt

.PHONY: build test snapshot clean-stacks check-arch

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
