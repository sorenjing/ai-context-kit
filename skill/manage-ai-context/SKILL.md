---
name: manage-ai-context
description: Use when Codex needs to initialize, load, refresh, validate, or compact offline shared project memory across nested repositories, especially with AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, `.ai` workspaces, repeated repository analysis, stale context, or project switching.
---

# Manage AI Context

Use `aictx` as the deterministic source of project discovery, metadata facts, and freshness. Keep one `.ai/` context store per workspace; keep AI-specific entry files thin.

## Choose the operation

| Situation | Action |
|---|---|
| No `.aictx.toml` exists | Run `aictx init --workspace <root> --dry-run`, review, then run without `--dry-run` |
| Starting or switching work | Read `.ai/GLOBAL.md`, `.ai/WORKSPACE.md`, then only the selected project memory; run `aictx status` |
| A project is new or stale | Run `aictx update <project> --dry-run`, review, then apply |
| Markers or entry files seem damaged | Run `aictx check`; do not repair by overwriting |
| Memory is verbose or outdated | Compact only the manual block; preserve decisions, constraints, commands, current state, and known issues |

## Maintain semantic memory

Edit only content between `<!-- aictx:manual:start -->` and `<!-- aictx:manual:end -->`. Record conclusions and their reasons, not source code, full conversations, command logs, or failed-step narratives.

After material architecture, dependency, build, test, or workflow changes:

1. Run `aictx status`.
2. Run `aictx update <project>` when stale.
3. Update the manual block only when the change adds semantic knowledge not present in detected facts.
4. Run `aictx check`.

## Safety contract

- Never create a separate memory hierarchy inside every project.
- Never scan source bodies to manufacture summaries; inspect source only when the user's actual task requires it.
- Never copy the same project facts into AGENTS.md, CLAUDE.md, GEMINI.md, or Cursor rules.
- Never overwrite an unrecognized existing entry file or malformed managed block.
- Use `--dry-run` before initializing or changing multiple files.
- Keep the workflow offline; do not add model APIs, network services, databases, or background daemons.

If `aictx` is unavailable, report that dependency and provide the repository installation command. Do not recreate its update logic ad hoc.
