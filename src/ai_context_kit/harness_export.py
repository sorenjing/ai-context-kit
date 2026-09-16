"""Versioned context exports for local AI development harnesses."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path

from .config import ConfigError, load_config
from .discovery import discover_projects
from .facts import extract_facts
from .render import _automatic, _manual_content, slugify
from .state import classify_projects, load_state
from .task_contracts import TaskEnvelope, canonical_digest


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
    task: TaskEnvelope | None = None,
    skill_ids: tuple[str, ...] = (),
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

    config = load_config(root)
    sources: list[dict[str, str]] = []
    for configured in config.context_sources.get(facts.project.name, ()):
        relative = _relative_path(configured)
        source_path = (root / relative).resolve()
        if not source_path.is_relative_to(root):
            raise ConfigError("context source path must be workspace-relative")
        try:
            source_bytes = source_path.read_bytes()
        except OSError as exc:
            raise ConfigError(f"cannot read context source: {relative}") from exc
        if len(source_bytes) > config.max_file_bytes:
            raise ConfigError(f"context source exceeds max_file_bytes: {relative}")
        sources.append(
            {
                "source_id": f"project:{facts.project.name}:{relative}",
                "relative_path": relative,
                "content_digest": hashlib.sha256(source_bytes).hexdigest(),
                "authority": "project",
            }
        )

    bundle: dict[str, object] = {
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
    if task is not None:
        rendered_context = bundle["context"]
        sources.insert(
            0,
            {
                "source_id": f"context:{facts.project.name}:rendered",
                "relative_path": f".ai/projects/{slugify(facts.project.name)}.md",
                "content_digest": canonical_digest(rendered_context),
                "authority": "project",
            },
        )
        bundle.update(
            {
                "task": {"task_id": task.task_id},
                "sources": sources,
                "skill_ids": list(dict.fromkeys(skill_ids)),
                "conflicts": [],
            }
        )
        digest = canonical_digest(bundle)
        bundle["content_digest"] = digest
        bundle["bundle_id"] = f"ctx_{digest[:24]}"
    return bundle
