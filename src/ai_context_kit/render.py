"""Deterministic shared-context Markdown rendering."""

from __future__ import annotations

from .models import ProjectFacts


AUTO_START = "<!-- aictx:auto:start -->"
AUTO_END = "<!-- aictx:auto:end -->"
MANUAL_START = "<!-- aictx:manual:start -->"
MANUAL_END = "<!-- aictx:manual:end -->"


class MarkerError(ValueError):
    """Raised when a managed Markdown file has unsafe markers."""


def _manual_content(existing: str | None) -> str:
    if existing is None:
        return "\n## Project memory\n\nRecord goals, architecture decisions, constraints, current state, and known issues here.\n"
    markers = (AUTO_START, AUTO_END, MANUAL_START, MANUAL_END)
    if any(existing.count(marker) != 1 for marker in markers):
        raise MarkerError("managed file must contain each marker exactly once")
    positions = [existing.index(marker) for marker in markers]
    if positions != sorted(positions):
        raise MarkerError("managed markers are out of order")
    start = positions[2] + len(MANUAL_START)
    end = positions[3]
    return existing[start:end]


def _automatic(facts: ProjectFacts) -> str:
    lines = [f"# {facts.project.name}", "", "## Detected facts", ""]
    lines.append(f"- Path: `{facts.project.relative_path}`")
    if facts.description:
        lines.append(f"- Description: {facts.description}")
    if facts.technologies:
        lines.append(f"- Technologies: {', '.join(facts.technologies)}")
    if facts.git_branch:
        status = "dirty" if facts.git_dirty else "clean"
        lines.append(f"- Git: `{facts.git_branch}` ({status})")
    if facts.directories:
        lines.append(f"- Directories: {', '.join(f'`{name}`' for name in facts.directories)}")
    if facts.commands:
        lines.extend(["", "### Commands", ""])
        lines.extend(f"- {name}: `{command}`" for name, command in facts.commands)
    return "\n".join(lines).rstrip() + "\n"


def render_project_memory(facts: ProjectFacts, existing: str | None = None) -> str:
    manual = _manual_content(existing)
    return (
        f"{AUTO_START}\n{_automatic(facts)}{AUTO_END}\n\n"
        f"{MANUAL_START}{manual}{MANUAL_END}\n"
    )


def render_workspace(facts: list[ProjectFacts]) -> str:
    lines = ["# Workspace", "", "Load only the memory file for the project currently being changed.", ""]
    for item in sorted(facts, key=lambda value: value.project.relative_path):
        slug = slugify(item.project.name)
        lines.append(
            f"- [{item.project.name}](projects/{slug}.md) — `{item.project.relative_path}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    return "-".join(part for part in slug.split("-") if part) or "project"

