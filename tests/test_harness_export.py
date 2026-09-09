from datetime import datetime, timezone
import json
from pathlib import Path

from ai_context_kit.cli import main
from ai_context_kit.harness_export import build_harness_bundle

from test_cli import make_workspace


def test_build_harness_bundle_uses_v1_schema_and_workspace_relative_paths(tmp_path: Path) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0

    bundle = build_harness_bundle(
        tmp_path,
        "demo",
        generated_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )

    assert bundle["schema_version"] == "context-bundle/v1"
    assert bundle["project"] == "demo"
    assert bundle["generated_at"] == "2026-09-09T00:00:00+00:00"
    assert bundle["freshness"] == "current"
    assert bundle["repositories"] == [{"name": "demo", "relative_path": "projects/demo"}]
    assert str(tmp_path) not in json.dumps(bundle)


def test_export_harness_writes_json_to_stdout_without_mutating_workspace(
    tmp_path: Path, capsys
) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0
    capsys.readouterr()
    before = (tmp_path / ".ai/state.json").read_bytes()

    assert (
        main(
            [
                "export",
                "harness",
                "demo",
                "--format",
                "json",
                "--output",
                "-",
                "--workspace",
                str(tmp_path),
            ]
        )
        == 0
    )

    bundle = json.loads(capsys.readouterr().out)
    assert bundle["schema_version"] == "context-bundle/v1"
    assert bundle["project"] == "demo"
    assert (tmp_path / ".ai/state.json").read_bytes() == before
