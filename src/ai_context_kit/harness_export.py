"""Versioned context exports for local AI development harnesses."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigError, load_config
from .discovery import discover_projects
from .facts import extract_facts
from .render import _automatic, _manual_content, slugify
from .state import classify_projects, load_state


SCHEMA_VERSION = "context-bundle/v1"


def _select_project(root: Path, selected: str):
    config = load_config(root)
    matches = [
        extract_facts(project, config)
        for project in discover_projects(config)
        if project.name == selected or slugify(project.name) == selected
    ]
    if not matches:
        raise ConfigError(f"unknown project: {selected}")
    return matches[0]


def _relative_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError("project path must be workspace-relative")
    return path.as_posix()


def build_harness_bundle(
    workspace: Path,
    project_name: str,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Build one immutable, portable context bundle from bounded observations."""

    root = workspace.resolve()
    facts = _select_project(root, project_name)
    memory_path = root / ".ai" / "projects" / f"{slugify(facts.project.name)}.md"
    global_path = root / ".ai" / "GLOBAL.md"
    project_memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else None
    global_context = global_path.read_text(encoding="utf-8") if global_path.exists() else ""
    freshness = classify_projects([facts], load_state(root))[facts.project.name]
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must include a timezone")

    return {
        "schema_version": SCHEMA_VERSION,
        "project": facts.project.name,
        "generated_at": timestamp.isoformat(),
        "freshness": freshness,
        "observed_scope": [path.as_posix() for path in facts.scanned_files],
        "repositories": [
            {
                "name": facts.project.name,
                "relative_path": _relative_path(facts.project.relative_path),
            }
        ],
        "context": {
            "automatic": _automatic(facts).strip(),
            "manual": _manual_content(project_memory).strip(),
            "global": global_context.strip(),
        },
    }
