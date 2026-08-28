# Changelog

All notable changes to AI Context Kit are documented here. The project follows semantic versioning after the first published release.

## 0.1.0 - Unreleased

### Added

- Offline discovery of nested projects from recognized repository markers.
- Deterministic project facts and metadata fingerprints for `current`, `stale`, `new`, and `missing` status.
- Managed context adapters for Codex, Claude, Gemini, and Cursor.
- Byte-preserved manual memory blocks and validation for damaged markers.
- `init`, `scan`, `status`, `update`, and `check` commands with dry-run support for mutations.
- `aictx --version` and a Codex context-management Skill.
- Cross-platform CI for Python 3.11–3.13 on Windows, macOS, and Linux.

### Security boundaries

- No networking, model API, daemon, database, or vector store at runtime.
- No traversal through directory symlinks.
- No reads from common secret files and no writes outside the resolved workspace.

### Known limitations

- Human-readable CLI output only; JSON output is not part of version 0.1.
- PyPI publication and external adoption evidence have not been completed.

