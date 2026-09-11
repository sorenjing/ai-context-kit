# AI Context Kit

[![CI](https://github.com/sorenjing/ai-context-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/sorenjing/ai-context-kit/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Auditable project context shared across AI coding tools.**

AI Context Kit maintains compact project observations that Codex, Claude, Gemini, and Cursor can read from the same workspace. It discovers nested projects, records facts from a bounded set of metadata, and detects when those observed inputs change.

No model API, cloud service, or vector database is required. The result is a small, reviewable `.ai/` directory that can be version-controlled and shared.

The repository and its current files remain authoritative. AI Context Kit provides a reusable observation and memory layer; it does not replace source inspection or project rules.

## Why this exists

AI assistants usually keep instructions at the project level, while related projects often live in a larger workspace. That creates two kinds of waste:

- every tool repeats the same repository discovery;
- useful decisions stay trapped in one project folder or one assistant session.

AI Context Kit gives the workspace one shared context entry point. The CLI owns deterministic observations and change detection; people and their assistants own the short semantic memory that explains goals, decisions, constraints, and current state.

## What you get

- **One context store** shared by four AI tools through thin `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and Cursor entries.
- **Incremental refresh** based on metadata fingerprints instead of a full re-analysis every time.
- **Auditable scope** recorded beside generated facts, so readers can see which bounded inputs were observed.
- **Human-safe memory** with protected manual blocks that the CLI will not overwrite.
- **Offline by default**: recognized manifests, bounded README text, Git metadata, and directory names only.
- **Safe failure modes** for malformed markers, symlinked discovery roots, secret files, and project-name collisions.

## How it fits with agent skills

AI Context Kit is the **shared context layer**. It can be used alongside reusable Agent Skills and repository-local rules without depending on either one. See [Agent Skills integration](docs/integrations/agent-skills.md) for the runtime composition and responsibility boundaries.

## Plugin and web access

The standard plugin package exposes `manage-ai-context` from the canonical `skills/` directory and delegates deterministic local work to the `aictx` CLI.

For ChatGPT web access, the repository includes a read-only GitHub-backed MCP server and container deployment. Exported context becomes available after the reviewed publication tree is committed to GitHub and the MCP server is deployed at a stable HTTPS URL. See [GitHub-backed web MVP](docs/github-web-mvp.md) for setup and [Plugin architecture](docs/plugin-architecture.md) for the wider design.

## Install

AI Context Kit requires Python 3.11 or newer.

Before the first PyPI release, install directly from the repository:

```bash
pipx install git+https://github.com/sorenjing/ai-context-kit.git
```

After the first PyPI release, `pipx install ai-context-kit` will become the preferred command. The current version is installed directly from GitHub.

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
- `aictx status`: report `new`, `stale`, `current`, or `missing` projects. `current` means the observed inputs match the last render; it does not guarantee that every project fact is complete or correct.
- `aictx update [project]`: refresh all projects or one selected project.
- `aictx check`: validate project-memory markers and adapter presence.
- `aictx export chatgpt-project <project>`: render a portable context file for upload to a matching ChatGPT Project.
- `aictx export harness <project> --format json --output -`: print a versioned, local `ContextBundle v1` for an AI development harness.
- `aictx publish github <project>`: write a deterministic, commit-ready bundle and index to `.ai/published` for explicit review.

Use `--workspace PATH` from outside the workspace. Mutating commands support `--dry-run`.

## Use with ChatGPT Projects

AI Context Kit can generate a compact project handoff for ChatGPT Projects:

```bash
aictx export chatgpt-project my-project
```

The command writes `.ai/exports/my-project-chatgpt-project.md`. Upload that file to the matching ChatGPT Project as a source, then start task-specific chats inside the Project. Regenerate and replace the upload after meaningful project changes.

The export combines bounded automatic facts, the selected project's managed semantic memory, and `GLOBAL.md`. It is a portable context file, not a way to read, write, or synchronize ChatGPT saved memory. Keep the workspace and its repository files as the source of truth, and do not upload secrets or private material that should stay outside ChatGPT.

ChatGPT Projects organize shared chats, files, instructions, and sources; ChatGPT saved memory is a separate recall layer. See the official documentation for [Projects](https://learn.chatgpt.com/docs/projects) and [Memories](https://learn.chatgpt.com/docs/customization/memories).

## Use with EvolveTrace

EvolveTrace consumes a stable JSON handoff rather than AI Context Kit internals or human-facing Markdown:

```bash
aictx export harness my-project --format json --output -
```

The command emits `context-bundle/v1` with the selected project, generation time, freshness state, bounded observation scope, workspace-relative repository identifier, and automatic/manual/shared context. It performs no network requests and does not mutate the workspace when `--output -` is used.

## Context ownership

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

The CLI has no networking code and needs no API key. It reads recognized manifests, a bounded README excerpt, Git metadata, and directory names. Each generated project file records this observation scope. The CLI does not read ordinary source bodies, follow directory symlinks, or scan common secret files.

A `current` freshness label means the recorded observation inputs have not changed since the last render. Source code and behavior outside that scope still require direct inspection.

The local workflow remains deterministic and offline. Optional network access is isolated to the read-only MCP server, while model integration, vector search, background synchronization, and automatic business-level summaries remain outside the current release. The included Skill maintains the manual block and requires review before publication.

## Install the Codex Skill

Install the repository as a plugin, or copy/link `skills/manage-ai-context` into your Codex skills directory, then invoke `$manage-ai-context`. The Skill delegates deterministic work to the installed `aictx` command. The `aictx` Python package remains a separate runtime dependency.

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
