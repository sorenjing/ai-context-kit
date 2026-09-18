"""Managed, reversible Personal AI Pack installation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from . import __version__
from .personal_pack import PersonalAIPack
from .state import _atomic_text


def _digest(contents: str) -> str:
    return hashlib.sha256(contents.encode("utf-8")).hexdigest()


def _render(pack: PersonalAIPack) -> dict[str, str]:
    plugin = {
        "name": "ai-context-kit",
        "version": __version__,
        "description": "Load bounded, source-traceable context on demand",
        "skills": "./skills/",
        "platforms": list(pack.enabled_platforms),
        "mcp": {"server": "aictx-mcp", "readOnly": True},
    }
    skill = """---
name: manage-ai-context
description: Load the smallest source-traceable context bundle needed for a project task.
---

# Manage AI Context

Resolve the target project, request bounded context through AI Context Kit, and report the
bundle and source identifiers used. Never request the full private portfolio by default.
"""
    return {
        "generated/openai/plugin.json": json.dumps(plugin, indent=2, sort_keys=True) + "\n",
        "generated/openai/skills/manage-ai-context/SKILL.md": skill,
    }


class PackInstaller:
    def __init__(self, target: Path):
        self.target = target.resolve()
        self.root = self.target / ".aictx-pack"
        self.state_path = self.root / "state.json"

    def install(self, pack: PersonalAIPack, manifest_path: Path) -> dict[str, Any]:
        del manifest_path  # source location is intentionally never persisted
        rendered = _render(pack)
        for relative, contents in rendered.items():
            _atomic_text(self.root / relative, contents)
        state = {
            "schema": "personal-ai-pack-installation/v1",
            "pack": pack.to_public_summary(),
            "managed_files": {
                relative: _digest(contents) for relative, contents in sorted(rendered.items())
            },
        }
        _atomic_text(self.state_path, json.dumps(state, indent=2, sort_keys=True) + "\n")
        return state

    def _state(self) -> dict[str, Any]:
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if payload.get("schema") != "personal-ai-pack-installation/v1":
            raise ValueError("unsupported installation state")
        return payload

    def status(self) -> dict[str, Any]:
        return self._state()

    def doctor(self) -> list[str]:
        try:
            state = self._state()
        except (OSError, ValueError, json.JSONDecodeError):
            return ["installation state is missing or invalid"]
        findings: list[str] = []
        for relative, expected in state["managed_files"].items():
            path = self.root / relative
            if not path.exists():
                findings.append(f"missing managed file: {relative}")
            elif _digest(path.read_text(encoding="utf-8")) != expected:
                findings.append(f"digest mismatch: {relative}")
        return findings

    def uninstall(self) -> None:
        if not self.root.exists():
            return
        self._state()
        shutil.rmtree(self.root)
