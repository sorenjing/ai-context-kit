from pathlib import Path
import shutil

import pytest

from ai_context_kit.cli import main


def make_workspace(root: Path) -> None:
    project = root / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname="demo"\n[project.scripts]\ntest="pytest"\n', encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo\n\nExample project.\n", encoding="utf-8")


def test_init_creates_shared_context_and_is_idempotent(tmp_path: Path) -> None:
    make_workspace(tmp_path)

    assert main(["init", "--workspace", str(tmp_path)]) == 0
    first = (tmp_path / ".ai/projects/demo.md").read_bytes()
    assert main(["update", "--workspace", str(tmp_path)]) == 0

    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "GEMINI.md").exists()
    assert (tmp_path / ".cursor/rules/ai-context.mdc").exists()
    assert first == (tmp_path / ".ai/projects/demo.md").read_bytes()


def test_status_reports_stale_after_manifest_change(tmp_path: Path, capsys) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    manifest = tmp_path / "projects/demo/pyproject.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "version='2'\n", encoding="utf-8")

    assert main(["status", "--workspace", str(tmp_path)]) == 1

    assert "stale" in capsys.readouterr().out


def test_update_prunes_projects_removed_from_discovery(tmp_path: Path, capsys) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0

    shutil.rmtree(tmp_path / "projects" / "demo")

    assert main(["update", "--workspace", str(tmp_path)]) == 0
    assert main(["status", "--workspace", str(tmp_path)]) == 0
    assert "missing" not in capsys.readouterr().out


def test_dry_run_init_writes_nothing(tmp_path: Path) -> None:
    make_workspace(tmp_path)

    assert main(["init", "--workspace", str(tmp_path), "--dry-run"]) == 0

    assert not (tmp_path / ".aictx.toml").exists()
    assert not (tmp_path / ".ai").exists()


def test_check_rejects_damaged_project_markers(tmp_path: Path, capsys) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    memory = tmp_path / ".ai/projects/demo.md"
    memory.write_text(memory.read_text(encoding="utf-8").replace("<!-- aictx:manual:end -->", ""), encoding="utf-8")

    assert main(["check", "--workspace", str(tmp_path)]) == 1

    assert "marker" in capsys.readouterr().out.lower()


def test_scan_does_not_create_context_files(tmp_path: Path, capsys) -> None:
    make_workspace(tmp_path)
    (tmp_path / ".aictx.toml").write_text("version = 1\n", encoding="utf-8")

    assert main(["scan", "--workspace", str(tmp_path)]) == 0

    assert "demo" in capsys.readouterr().out
    assert not (tmp_path / ".ai").exists()


def test_update_preserves_manual_block_bytes_with_crlf(tmp_path: Path) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    memory = tmp_path / ".ai/projects/demo.md"
    contents = memory.read_bytes()
    start = contents.index(b"<!-- aictx:manual:start -->") + len(b"<!-- aictx:manual:start -->")
    end = contents.index(b"<!-- aictx:manual:end -->")
    manual = b"\r\n## Decisions\r\n\r\nKeep mixed newlines.\n\xe4\xb8\xad\xe6\x96\x87\r\n"
    memory.write_bytes(contents[:start] + manual + contents[end:])
    manifest = tmp_path / "projects/demo/pyproject.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "version='2'\n", encoding="utf-8")

    assert main(["update", "--workspace", str(tmp_path)]) == 0

    updated = memory.read_bytes()
    new_start = updated.index(b"<!-- aictx:manual:start -->") + len(b"<!-- aictx:manual:start -->")
    new_end = updated.index(b"<!-- aictx:manual:end -->")
    assert updated[new_start:new_end] == manual


@pytest.mark.parametrize("first,second", [("Same", "Same"), ("Foo Bar", "foo-bar")])
def test_init_rejects_project_name_or_slug_collisions_before_memory_writes(
    tmp_path: Path, first: str, second: str
) -> None:
    for path in ("projects/one", "projects/two"):
        project = tmp_path / path
        project.mkdir(parents=True)
        (project / ".git").mkdir()
    (tmp_path / ".aictx.toml").write_text(
        f'''version = 1
[projects]
"projects/one" = "{first}"
"projects/two" = "{second}"
''',
        encoding="utf-8",
    )

    assert main(["init", "--workspace", str(tmp_path)]) == 2

    assert not list((tmp_path / ".ai/projects").glob("*.md"))


@pytest.mark.parametrize("state", ["not json", '{"version": 99, "projects": {}}'])
def test_check_reports_invalid_state_schema(tmp_path: Path, state: str, capsys) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    (tmp_path / ".ai/state.json").write_text(state, encoding="utf-8")

    assert main(["check", "--workspace", str(tmp_path)]) == 1

    assert "state" in capsys.readouterr().out.lower()


def test_check_reports_modified_adapter_contents(tmp_path: Path, capsys) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(".ai/WORKSPACE.md", ".ai/MISSING.md"),
        encoding="utf-8",
    )

    assert main(["check", "--workspace", str(tmp_path)]) == 1

    assert "adapter" in capsys.readouterr().out.lower()
