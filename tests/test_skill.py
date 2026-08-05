from pathlib import Path


SKILL = Path(__file__).parents[1] / "skill" / "manage-ai-context"


def test_skill_has_valid_trigger_and_cli_workflow() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert text.startswith("---\nname: manage-ai-context\ndescription: Use when")
    for command in ("aictx init", "aictx status", "aictx update", "aictx check"):
        assert command in text
    assert "TODO" not in text


def test_skill_has_codex_interface_metadata() -> None:
    metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert 'display_name: "Manage AI Context"' in metadata
    assert "$manage-ai-context" in metadata
