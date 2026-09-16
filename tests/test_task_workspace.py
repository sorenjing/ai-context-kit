import json
from pathlib import Path

from ai_context_kit.cli import main
from ai_context_kit.task_workspace import prepare_task

from test_cli import make_workspace


def test_prepare_task_writes_complete_relative_handoff_artifacts(tmp_path: Path) -> None:
    make_workspace(tmp_path)
    assert main(["init", "--workspace", str(tmp_path)]) == 0

    prepared = prepare_task(
        tmp_path,
        "demo",
        intent="Refresh the current project view",
        platform="codex",
        requested_by="human",
        skill_ids=("public-content-safety",),
        task_id="task-123",
    )

    task_dir = tmp_path / ".ai" / "tasks" / "task-123"
    assert sorted(path.name for path in task_dir.iterdir()) == [
        "bundle.json",
        "envelope.json",
        "handoff.md",
        "receipt.json",
    ]
    assert prepared.task_directory == Path(".ai/tasks/task-123")
    assert prepared.bundle["sources"][0]["source_id"] == "context:demo:rendered"
    assert json.loads((task_dir / "receipt.json").read_text(encoding="utf-8"))["status"] == "generated"
    handoff = (task_dir / "handoff.md").read_text(encoding="utf-8")
    assert "Task ID: task-123" in handoff
    assert str(tmp_path) not in handoff
