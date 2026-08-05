"""Bounded, offline extraction of project metadata."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tomllib

from .config import Config
from .models import Project, ProjectFacts


MANIFEST_TECHNOLOGIES = {
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "requirements.txt": "Python",
    "package.json": "Node.js",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java",
    "build.gradle": "Java",
}
SECRET_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}


def _safe_metadata(path: Path, config: Config) -> bool:
    try:
        return (
            path.is_file()
            and not path.is_symlink()
            and path.name not in SECRET_NAMES
            and path.stat().st_size <= config.max_file_bytes
            and path.resolve().is_relative_to(config.root)
        )
    except OSError:
        return False


def _read_text(path: Path, config: Config) -> str | None:
    if not _safe_metadata(path, config):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _readme_description(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return None


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def extract_facts(project: Project, config: Config) -> ProjectFacts:
    """Extract deterministic facts from recognized metadata only."""
    technologies: set[str] = set()
    commands: set[tuple[str, str]] = set()
    scanned: list[Path] = []
    description = None

    for marker, technology in MANIFEST_TECHNOLOGIES.items():
        path = project.path / marker
        text = _read_text(path, config)
        if text is None:
            continue
        technologies.add(technology)
        scanned.append(path.relative_to(project.path))
        try:
            if marker == "pyproject.toml":
                data = tomllib.loads(text)
                for name, target in data.get("project", {}).get("scripts", {}).items():
                    commands.add((str(name), str(target)))
            elif marker == "package.json":
                data = json.loads(text)
                for name, command in data.get("scripts", {}).items():
                    commands.add((f"npm run {name}", str(command)))
        except (tomllib.TOMLDecodeError, json.JSONDecodeError, AttributeError):
            pass

    for name in ("README.md", "README.rst", "README.txt"):
        path = project.path / name
        text = _read_text(path, config)
        if text is not None:
            description = _readme_description(text)
            scanned.append(path.relative_to(project.path))
            break

    directories = tuple(
        sorted(
            child.name
            for child in project.path.iterdir()
            if child.is_dir()
            and not child.is_symlink()
            and child.name not in config.exclude
            and child.name != ".git"
        )
    )
    branch = _git(project.path, "branch", "--show-current")
    head = _git(project.path, "rev-parse", "HEAD")
    status = _git(project.path, "status", "--porcelain")
    dirty = None if status is None else bool(status)

    return ProjectFacts(
        project=project,
        description=description,
        technologies=tuple(sorted(technologies)),
        commands=tuple(sorted(commands)),
        directories=directories,
        git_branch=branch or None,
        git_head=head or None,
        git_dirty=dirty,
        scanned_files=tuple(sorted(scanned, key=lambda path: path.as_posix())),
    )
