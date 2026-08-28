# AI Context Kit

[![CI](https://github.com/sorenjing/ai-context-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/sorenjing/ai-context-kit/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**One shared memory layer for every AI coding tool.**

AI Context Kit keeps Codex, Claude, Gemini, and Cursor aligned when they work on the same workspace. It discovers nested projects, records only useful project facts, and tells you when context is stale—so switching tools does not mean analyzing the same codebase again.

No model API. No cloud service. No vector database. Just a small, version-controlled `.ai/` directory that your tools can share.

> If you use more than one AI coding assistant, this is the missing workspace layer between your projects and your prompts.

## Why this exists

AI assistants usually remember instructions at the project level, but your projects often live inside a larger workspace. That creates two kinds of waste:

- every tool repeats the same repository discovery;
- useful decisions stay trapped in one project folder or one assistant.

AI Context Kit gives the whole workspace one source of truth. The CLI owns deterministic facts and freshness checks; you or your AI assistant own the short semantic memory that explains goals, decisions, constraints, and current state.

## What you get

- **One context store** shared by four AI tools through thin `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and Cursor entries.
- **Incremental refresh** based on metadata fingerprints instead of a full re-analysis every time.
- **Human-safe memory** with protected manual blocks that the CLI will not overwrite.
- **Offline by default**: recognized manifests, bounded README text, Git metadata, and directory names only.
- **Safe failure modes** for malformed markers, symlinked discovery roots, secret files, and project-name collisions.

## Install

AI Context Kit requires Python 3.11 or newer.

Before the first PyPI release, install directly from the repository:

```bash
pipx install git+https://github.com/sorenjing/ai-context-kit.git
```

After a release is visible on PyPI, `pipx install ai-context-kit` becomes the preferred command. The repository currently prepares version 0.1.0 but does not claim it has already been published.

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

From the directory containing your projects:

```bash
aictx init --dry-run
aictx init
aictx status
```

The workspace will contain:

```text
.aictx.toml
.ai/
  GLOBAL.md
  WORKSPACE.md
  CURRENT.md
  state.json
  projects/
AGENTS.md
CLAUDE.md
GEMINI.md
.cursor/rules/ai-context.mdc
```

When a manifest or README changes:

```bash
aictx status
aictx update my-project --dry-run
aictx update my-project
aictx check
```

Commands:

- `aictx init`: create the workspace, adapters, and first project facts.
- `aictx scan`: print discovered projects without writing context.
- `aictx status`: report `new`, `stale`, `current`, or `missing` projects.
- `aictx update [project]`: refresh all projects or one selected project.
- `aictx check`: validate project-memory markers and adapter presence.

Use `--workspace PATH` from outside the workspace. Mutating commands support `--dry-run`.

## Memory ownership

Project files have two marked blocks. The CLI replaces only the automatic block:

```markdown
<!-- aictx:auto:start -->
Detected facts
<!-- aictx:auto:end -->

<!-- aictx:manual:start -->
Human or AI-maintained semantic memory
<!-- aictx:manual:end -->
```

Malformed markers are an error. An existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or Cursor rule without the AI Context Kit marker is never overwritten.

## Privacy and limitations

The CLI has no networking code and needs no API key. It reads recognized manifests, a bounded README excerpt, Git metadata, and directory names. It does not read ordinary source bodies, follow directory symlinks, or scan common secret files.

Version 0.1 deliberately has no model integration, vector database, daemon, hooks, JSON output, or automatic business-level summaries. The included Codex Skill teaches Codex to maintain the manual memory block after meaningful work.

## Install the Codex Skill

Copy or link `skill/manage-ai-context` into your Codex skills directory, then invoke `$manage-ai-context`. The Skill delegates deterministic work to the installed `aictx` command.

## 中文快速开始

AI Context Kit 在本地维护一套 `.ai/` 共享上下文，让 Codex、Claude、Gemini 和 Cursor 不必反复分析同一批项目。它不会调用模型 API，也不会读取普通源代码正文。

```powershell
pipx install git+https://github.com/sorenjing/ai-context-kit.git
aictx init --dry-run
aictx init
aictx status
```

项目变化后先运行 `aictx status`，再用 `aictx update <项目名> --dry-run` 审阅更新，确认后去掉 `--dry-run`。人工记忆只能写在 `manual` 标记区内，CLI 不会覆盖该区域。

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## License

MIT

