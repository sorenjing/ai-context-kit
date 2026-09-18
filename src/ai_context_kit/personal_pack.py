"""Strict, provider-neutral contracts for installable personal AI packs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping


_SECRET_KEYS = {"authorization", "cookie", "password", "secret", "token"}


def _required(value: object, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    return normalized


def _reject_unsafe(value: object, *, key: str = "") -> None:
    if key.lower() in _SECRET_KEYS or key.lower().endswith(("_token", "_secret", "_password")):
        raise ValueError(f"secret field is not allowed: {key}")
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            _reject_unsafe(child, key=str(child_key))
    elif isinstance(value, list):
        for child in value:
            _reject_unsafe(child, key=key)
    elif isinstance(value, str):
        if value.startswith(("/", "~")) or PureWindowsPath(value).is_absolute():
            raise ValueError("local absolute paths are not allowed")


def _load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - packaging guarantees it
            raise ValueError("YAML manifests require PyYAML") from exc
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError("pack manifest must contain an object")
    return payload


@dataclass(frozen=True)
class PersonalAIPack:
    schema: str
    pack_id: str
    version: int
    profile: dict[str, Any]
    sources: dict[str, Any]
    platforms: dict[str, dict[str, Any]]
    policies: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "PersonalAIPack":
        payload = _load_document(path)
        allowed = {"schema", "id", "version", "profile", "sources", "platforms", "policies"}
        if set(payload) != allowed:
            raise ValueError("pack manifest fields are invalid")
        _reject_unsafe(payload)
        if payload["schema"] != "personal-ai-pack/v1" or payload["version"] != 1:
            raise ValueError("unsupported personal AI pack schema or version")
        for name in ("profile", "sources", "platforms", "policies"):
            if not isinstance(payload[name], dict):
                raise ValueError(f"{name} must be an object")
        policies = dict(payload["policies"])
        required_false = (
            "publish_private_sources",
            "capture_prompt_content",
            "accept_memory_automatically",
        )
        if any(policies.get(name) is not False for name in required_false):
            raise ValueError("safe pack policies must be explicitly disabled")
        platforms: dict[str, dict[str, Any]] = {}
        for name, config in payload["platforms"].items():
            if not isinstance(config, dict) or set(config) != {"enabled", "adapter"}:
                raise ValueError("platform config fields are invalid")
            platforms[_required(name, "platform")] = {
                "enabled": bool(config["enabled"]),
                "adapter": _required(config["adapter"], "adapter"),
            }
        return cls(
            "personal-ai-pack/v1",
            _required(payload["id"], "id"),
            1,
            dict(payload["profile"]),
            dict(payload["sources"]),
            platforms,
            policies,
        )

    @property
    def enabled_platforms(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, config in self.platforms.items() if config["enabled"]))

    def to_public_summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "id": self.pack_id,
            "version": self.version,
            "platforms": list(self.enabled_platforms),
        }


@dataclass(frozen=True)
class ExecutionProfile:
    schema: str
    profile_id: str
    platform: str
    harness: str
    adapter: str
    adapter_version: str
    provider: str | None
    model: str | None
    capabilities: tuple[str, ...]
    policy_profile: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExecutionProfile":
        allowed = {
            "schema", "profile_id", "platform", "harness", "adapter",
            "adapter_version", "provider", "model", "capabilities", "policy_profile",
        }
        if set(payload) != allowed:
            raise ValueError("execution profile contains unknown fields")
        _reject_unsafe(dict(payload))
        if payload["schema"] != "execution-profile/v1":
            raise ValueError("unsupported execution profile schema")
        capabilities = payload["capabilities"]
        if not isinstance(capabilities, list):
            raise ValueError("capabilities must be a list")
        return cls(
            "execution-profile/v1",
            _required(payload["profile_id"], "profile_id"),
            _required(payload["platform"], "platform"),
            _required(payload["harness"], "harness"),
            _required(payload["adapter"], "adapter"),
            _required(payload["adapter_version"], "adapter_version"),
            str(payload["provider"]).strip() if payload.get("provider") else None,
            str(payload["model"]).strip() if payload.get("model") else None,
            tuple(sorted({_required(item, "capability") for item in capabilities})),
            _required(payload["policy_profile"], "policy_profile"),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["capabilities"] = list(self.capabilities)
        return value

