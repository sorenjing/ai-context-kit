---
name: manage-ai-context
description: Use when Codex needs to initialize, load, refresh, validate, compact, or explicitly publish shared project memory across nested repositories, especially with AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, `.ai` workspaces, repeated repository analysis, stale context, project switching, or GitHub-backed ChatGPT access.
---

# Manage AI Context

Use `aictx` for deterministic project discovery, bounded metadata observations, and observed-input change detection. Keep one `.ai/` context store per workspace and keep AI-specific entry files thin. Treat current repository files as authoritative.

## Choose the operation

| Situation | Action |
|---|---|
| No `.aictx.toml` exists | Run `aictx init --workspace <root> --dry-run`, review, then run without `--dry-run` |
| Starting or switching work | Read `.ai/GLOBAL.md`, `.ai/WORKSPACE.md`, then only the selected project memory; run `aictx status` |
| A project is new or stale | Run `aictx update <project> --dry-run`, review, then apply |
| Markers or entry files seem damaged | Run `aictx check`; do not repair by overwriting |
| Memory is verbose or outdated | Compact only the manual block; preserve decisions, constraints, commands, current state, and known issues |
| The user requests remote or ChatGPT web access | Run `aictx publish github <project>`, have the user review the generated files, and publish only after explicit authorization |

## Maintain semantic memory

Edit only content between `<!-- aictx:manual:start -->` and `<!-- aictx:manual:end -->`. Record conclusions and their reasons, not source code, full conversations, command logs, or failed-step narratives.

After material architecture, dependency, build, test, or workflow changes:

1. Run `aictx status`.
2. Run `aictx update <project>` when stale.
3. Update the manual block only when the change adds semantic knowledge not present in detected facts.
4. Run `aictx check`.

## Interpret freshness precisely

`current` means only that the observed inputs recorded by AI Context Kit match the inputs used for the latest render. It is not a guarantee that the memory is complete or that unscanned source code has not changed.

- `new`: the project is discovered but has no recorded render.
- `stale`: one or more observed inputs changed.
- `current`: the observed inputs match the recorded render.
- `missing`: a previously recorded project is no longer discovered.

Read the generated observation scope before relying on an automatic fact. Inspect current source files whenever the task depends on behavior outside that scope.

## Safety contract

- Never create a separate memory hierarchy inside every project.
- Never scan source bodies to manufacture summaries; inspect source only when the user's actual task requires it.
- Never copy the same project facts into AGENTS.md, CLAUDE.md, GEMINI.md, or Cursor rules.
- Never overwrite an unrecognized existing entry file or malformed managed block.
- Never describe `current` as proof that the entire project or its behavior is up to date.
- Use `--dry-run` before initializing or changing multiple files.
- Keep collection and updates offline by default. `publish` writes a local review directory only; it never pushes to GitHub.
- Never publish implicitly. Treat the generated bundle as potentially sensitive, require review, and use a dedicated repository or branch with the narrowest suitable access.
- Remote MCP reads only bundle paths declared in the published index. Do not use it as a general repository browser.

If `aictx` is unavailable, report that dependency and provide the repository installation command. Do not recreate its update logic ad hoc.
