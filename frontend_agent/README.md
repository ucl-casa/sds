# `sds-agent`

A headless, agent-shaped extra layer on top of the `sds` teaching image.
Ported from [darribas/gds_env](https://github.com/darribas/gds_env)'s
`frontend_agent/` (BSD-3-Clause) and retargeted at this repo's own base
image and environment.

## What this is

A separate image (`sds-agent`) built `FROM` an already-built `sds` image,
adding the harnesses people actually use to drive coding agents — **Claude
Code CLI**, **opencode**, **GitHub Copilot CLI** — plus the tools those
agents reach for (ripgrep, fd, fzf, jq, gh) and a matching set of LSPs.
`utils/gdsa` is the host-side launcher: it runs `podman run -it` with your
terminal attached directly to the harness process inside a throwaway
container, so there's no server or socket involved — see the root
conversation history / commit messages for a longer explanation of the
mechanism if you need it.

## What this is not

- Not a Jupyter server or the default teaching image. Build and run it
  separately (`make build-agent`), don't bake it into `sds:2026-*`.
- Not an auth manager. Auth happens on your host; `gdsa` bind-mounts the
  relevant config dirs (`~/.claude`, `~/.copilot`, `~/.config/opencode`) so
  an ephemeral container doesn't ask you to log in every run.
- Not pinned. Like upstream, `frontend_agent/Dockerfile` takes a
  `CACHEBUST` build arg specifically so harness versions aren't frozen —
  a rebuild can change harness behaviour under you. That's a deliberate
  trade for always having the latest agent tooling, not an oversight.

## Differences from upstream `gds_env`

- `base_image` is your own `sds` image tag, not `gds:latest`.
- The R language server install step is dropped — this repo's conda
  environment has no R.
- `opencode.json`'s `ollama`/`openai` provider blocks ship with empty
  model lists and no default model: there's no Ollama/OpenAI-compatible
  endpoint configured for this course yet. Once one exists, use the
  `opencode-models` skill (`frontend_agent/skills/opencode-models/`) to
  wire it up.
- `gdsa` runs `podman` by default (`GDSA_RUNTIME=docker` to override),
  since this repo's build workflow is Podman-based.
- `gdsa update` doesn't self-fetch from a public raw URL (this repo isn't
  necessarily public) — it just tells you to `git pull`.

## Building

```bash
make build ARCH=arm64 TAG=2026        # base image first, if not already built
make build-agent ARCH=arm64 TAG=2026  # layers the agent tooling on top
make install-gdsa                     # symlinks utils/gdsa onto your PATH
```

Then: `gdsa claude`, `gdsa opencode`, `gdsa copilot`, or `gdsa shell` —
see `gdsa help` for options (`--with-git-creds` to allow pushing/PRs).

## Repo layout

```
frontend_agent/
  Dockerfile            # ARG base_image, layered on an sds image
  opencode.json          # baked default: LSPs + both providers (empty models)
  tui.json                # opencode TUI theme
  claude-settings.json     # baked Claude Code settings
  README.md                 # this file
  skills/                    # skills authored here; see skills/README.md
  # notebook-cli skill is fetched from upstream at build time
utils/
  gdsa                  # the launcher
```
