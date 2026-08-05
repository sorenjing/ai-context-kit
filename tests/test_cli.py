from pathlib import Path

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
