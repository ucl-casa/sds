# `frontend_agent/skills/`

Skills authored in this repo, as opposed to `notebook-cli`, which
`frontend_agent/Dockerfile` fetches from upstream `jupyter-ai-contrib/nb-cli`
at build time instead of being vendored here.

Each subdirectory is a normal `SKILL.md` skill (YAML frontmatter with
`name`/`description`, then the instructions body) — the same format both
Claude Code and opencode read.

## How a skill here reaches each harness

Adding a directory here does not by itself make every harness pick it
up — wiring is per-skill, not automatic:

- **opencode**: add a `COPY skills/<name> /home/${NB_USER}/.config/opencode/skills/<name>`
  line in `frontend_agent/Dockerfile`'s "baked opencode config" block.
  opencode reads a real, discoverable `skills/` directory there.
- **Claude Code, inside the built image**: there's no discoverable
  `skills/` dir wired up for it, so instead the Dockerfile's `notebook-cli
  skill` step concatenates a skill's body (frontmatter stripped) onto the
  single, always-loaded `~/CLAUDE.md`. That means it's loaded into every
  Claude Code session in the container regardless of what the user is
  doing — fine for a couple of small skills, don't fold large or
  rarely-needed ones in this way without reconsidering.

## Adding a new skill

1. `mkdir -p frontend_agent/skills/<name>` and write `SKILL.md`.
2. Add the Dockerfile `COPY` line for opencode if it should ship in the
   image.
3. If it should also reach Claude Code inside the image, add another
   `awk ... >> /home/${NB_USER}/CLAUDE.md` line to the `notebook-cli
   skill` Dockerfile step (after the `COPY` from step 2, since it reads
   from the copied-in file) — mind the always-loaded cost noted above.

Adapted from [darribas/gds_env](https://github.com/darribas/gds_env)'s
`frontend_agent/` (BSD-3-Clause).
