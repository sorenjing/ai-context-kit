"""Command-line workflows for AI Context Kit."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .adapters import ManagedFileError, render_adapters, write_managed_file
from .config import ConfigError, find_workspace, load_config
from .discovery import discover_projects
from .facts import extract_facts
from .render import MarkerError, render_project_memory, render_workspace, slugify
from .state import (
    ProjectState,
    StateError,
    WorkspaceState,
    _atomic_text,
    classify_projects,
    fingerprint_facts,
    load_state,
    write_state,
)


CONFIG_TEMPLATE = """version = 1
max_file_bytes = 1048576

[discovery]
include = ["."]
exclude = [".git", ".ai", "node_modules", ".venv", "venv", "dist", "build", "target", "coverage"]

[projects]
"""
GLOBAL_TEMPLATE = """# Global context

Record stable preferences, environment constraints, and conventions shared by every project.
"""
CURRENT_TEMPLATE = """# Current work

Record only short-lived cross-session state here. Clear it when the work is complete.
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aictx", description="Offline shared context for AI coding tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "scan", "status", "check"):
        command = subparsers.add_parser(name)
        command.add_argument("--workspace", type=Path)
        if name == "init":
            command.add_argument("--dry-run", action="store_true")
    update = subparsers.add_parser("update")
    update.add_argument("project", nargs="?")
    update.add_argument("--workspace", type=Path)
    update.add_argument("--dry-run", action="store_true")
    return parser


def _root(value: Path | None, *, initializing: bool) -> Path:
    start = (value or Path.cwd()).resolve()
    if initializing:
        return start
    return find_workspace(start)


def _facts(root: Path):
    config = load_config(root)
    facts = [extract_facts(project, config) for project in discover_projects(config)]
    identities: dict[str, str] = {}
    for item in facts:
        identity = slugify(item.project.name)
        previous = identities.get(identity)
        if previous is not None:
            raise ConfigError(
                f"project name collision: {previous} and {item.project.relative_path} both use {identity}.md"
            )
        identities[identity] = item.project.relative_path
    return facts


def _read_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _write_if_changed(path: Path, contents: str, *, dry_run: bool) -> bool:
    existing = _read_exact(path) if path.exists() else None
    if existing == contents:
        return False
    if not dry_run:
        _atomic_text(path, contents)
    return True


def _initialize(root: Path, *, dry_run: bool) -> None:
    if not (root / ".aictx.toml").exists():
        _write_if_changed(root / ".aictx.toml", CONFIG_TEMPLATE, dry_run=dry_run)
    for path, contents in (
        (root / ".ai/GLOBAL.md", GLOBAL_TEMPLATE),
        (root / ".ai/CURRENT.md", CURRENT_TEMPLATE),
    ):
        if not path.exists():
            _write_if_changed(path, contents, dry_run=dry_run)
    for relative, contents in render_adapters().items():
        write_managed_file(root / relative, contents, dry_run=dry_run)


def _update(root: Path, selected: str | None, *, dry_run: bool) -> None:
    facts = _facts(root)
    if selected:
        matching = [item for item in facts if item.project.name == selected or slugify(item.project.name) == selected]
        if not matching:
            raise ConfigError(f"unknown project: {selected}")
        update_names = {item.project.name for item in matching}
    else:
        update_names = {item.project.name for item in facts}

    old_state = load_state(root)
    current_names = {item.project.name for item in facts}
    new_projects = {
        name: state for name, state in old_state.projects.items() if name in current_names
    }
    for item in facts:
        if item.project.name not in update_names:
            continue
        target = root / ".ai" / "projects" / f"{slugify(item.project.name)}.md"
        existing = _read_exact(target) if target.exists() else None
        rendered = render_project_memory(item, existing)
        _write_if_changed(target, rendered, dry_run=dry_run)
        fingerprint = fingerprint_facts(item)
        new_projects[item.project.name] = ProjectState(
            item.project.relative_path, fingerprint, fingerprint
        )
    _write_if_changed(root / ".ai/WORKSPACE.md", render_workspace(facts), dry_run=dry_run)
    if not dry_run:
        write_state(root, WorkspaceState(new_projects))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = _root(args.workspace, initializing=args.command == "init")
        if args.command == "init":
            _initialize(root, dry_run=args.dry_run)
            if not args.dry_run:
                _update(root, None, dry_run=False)
            print(f"initialized {root}")
            return 0
        if args.command == "scan":
            for item in _facts(root):
                print(f"{item.project.name}\t{item.project.relative_path}\t{', '.join(item.technologies)}")
            return 0
        if args.command == "status":
            statuses = classify_projects(_facts(root), load_state(root))
            for name, status in statuses.items():
                print(f"{status}\t{name}")
            return 1 if any(status != "current" for status in statuses.values()) else 0
        if args.command == "update":
            _update(root, args.project, dry_run=args.dry_run)
            print("dry run complete" if args.dry_run else "context updated")
            return 0
        if args.command == "check":
            findings: list[str] = []
            facts = _facts(root)
            try:
                load_state(root, strict=True)
            except StateError as exc:
                findings.append(str(exc))
            for item in facts:
                target = root / ".ai/projects" / f"{slugify(item.project.name)}.md"
                if not target.exists():
                    findings.append(f"missing project memory: {target}")
                    continue
                try:
                    render_project_memory(item, _read_exact(target))
                except MarkerError as exc:
                    findings.append(f"marker error in {target}: {exc}")
            for relative, expected in render_adapters().items():
                target = root / relative
                if not target.exists():
                    findings.append(f"missing adapter: {relative}")
                elif _read_exact(target) != expected:
                    findings.append(f"adapter content mismatch: {relative}")
            if findings:
                print("\n".join(findings))
                return 1
            print("context is valid")
            return 0
    except (ConfigError, MarkerError, ManagedFileError, OSError) as exc:
        print(f"error: {exc}")
        return 2
    return 2


def entrypoint() -> None:
    raise SystemExit(main())
