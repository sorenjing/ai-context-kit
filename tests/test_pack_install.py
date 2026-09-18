import json
from pathlib import Path

from ai_context_kit.pack_install import PackInstaller
from ai_context_kit.personal_pack import PersonalAIPack
from test_personal_pack import valid_pack, write_pack


def test_install_status_doctor_update_and_uninstall_are_managed(tmp_path: Path) -> None:
    source = write_pack(tmp_path / "pack.json", valid_pack())
    target = tmp_path / "installation"
    installer = PackInstaller(target)
    pack = PersonalAIPack.load(source)

    state = installer.install(pack, source)
    assert state["schema"] == "personal-ai-pack-installation/v1"
    assert sorted(state["managed_files"]) == [
        "generated/openai/plugin.json",
        "generated/openai/skills/manage-ai-context/SKILL.md",
    ]
    assert installer.status()["pack"]["id"] == "example-personal-ai"
    assert installer.doctor() == []

    plugin = target / ".aictx-pack/generated/openai/plugin.json"
    plugin.write_text("{}\n", encoding="utf-8")
    assert installer.doctor() == ["digest mismatch: generated/openai/plugin.json"]

    installer.install(pack, source)
    assert installer.doctor() == []
    unrelated = target / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")
    installer.uninstall()
    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert not (target / ".aictx-pack").exists()


def test_status_never_exposes_manifest_path_or_sources(tmp_path: Path) -> None:
    source = write_pack(tmp_path / "private-pack.json", valid_pack())
    installer = PackInstaller(tmp_path / "installation")
    installer.install(PersonalAIPack.load(source), source)
    rendered = json.dumps(installer.status())
    assert str(tmp_path) not in rendered
    assert "private-portfolio" not in rendered

