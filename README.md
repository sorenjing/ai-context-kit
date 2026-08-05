# AI Context Kit

AI Context Kit is an offline CLI for sharing compact project context across Codex, Claude, Gemini, and Cursor. It discovers nested projects, extracts bounded metadata, detects stale context, and preserves human-written memory without calling a model API.

## Why

Opening the same repository in different AI tools often triggers the same expensive analysis. AI Context Kit keeps one version-controlled `.ai/` workspace with deterministic facts and small human-maintained summaries. Tool-specific instruction files remain thin pointers to that shared context.

## Install

AI Context Kit requires Python 3.11 or newer.

```bash
pipx install ai-context-kit
```

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
pipx install ai-context-kit
aictx init --dry-run
aictx init
aictx status
```

项目变化后先运行 `aictx status`，再用 `aictx update <项目名> --dry-run` 审阅更新，确认后去掉 `--dry-run`。人工记忆只能写在 `manual` 标记区内，CLI 不会覆盖该区域。

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## License

MIT

