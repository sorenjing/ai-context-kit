"""Provider-neutral contracts for context-aware tasks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Literal


DeliveryStatus = Literal[
    "generated", "delivered", "acknowledged", "evidenced", "effective"
]
DELIVERY_LEVELS: tuple[DeliveryStatus, ...] = (
    "generated",
    "delivered",
    "acknowledged",
    "evidenced",
    "effective",
)


def canonical_digest(value: Any) -> str:
    """Return a stable SHA-256 digest for a JSON-compatible value."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _required(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    return normalized


@dataclass(frozen=True)
class TaskEnvelope:
    schema: str
    task_id: str
    target_project: str
    intent: str
    requested_by: str
    platform: str
    created_at: str

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        target_project: str,
        intent: str,
        requested_by: str,
        platform: str,
        created_at: datetime | None = None,
    ) -> TaskEnvelope:
        normalized_intent = _required(intent, "intent")
        if len(normalized_intent) > 500:
            raise ValueError("intent must be at most 500 characters")
        stamp = created_at or datetime.now(timezone.utc)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        return cls(
            schema="task-envelope/v1",
            task_id=_required(task_id, "task_id"),
            target_project=_required(target_project, "target_project"),
            intent=normalized_intent,
            requested_by=_required(requested_by, "requested_by"),
            platform=_required(platform, "platform"),
            created_at=stamp.isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ContextReceipt:
    schema: str
    receipt_id: str
    task_id: str
    attempt_id: str
    bundle_id: str
    platform: str
    adapter: str
    status: DeliveryStatus
    delivered_source_ids: tuple[str, ...]
    loaded_skill_ids: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        receipt_id: str,
        task_id: str,
        attempt_id: str,
        bundle_id: str,
        platform: str,
        adapter: str,
        status: DeliveryStatus,
        delivered_source_ids: tuple[str, ...] | list[str],
        loaded_skill_ids: tuple[str, ...] | list[str],
    ) -> ContextReceipt:
        if status not in ("generated", "delivered"):
            raise ValueError("initial status must be generated or delivered")
        sources = tuple(_required(value, "source identifier") for value in delivered_source_ids)
        if status == "delivered" and not sources:
            raise ValueError("a delivered receipt requires at least one source identifier")
        skills = tuple(_required(value, "skill identifier") for value in loaded_skill_ids)
        return cls(
            schema="context-receipt/v1",
            receipt_id=_required(receipt_id, "receipt_id"),
            task_id=_required(task_id, "task_id"),
            attempt_id=_required(attempt_id, "attempt_id"),
            bundle_id=_required(bundle_id, "bundle_id"),
            platform=_required(platform, "platform"),
            adapter=_required(adapter, "adapter"),
            status=status,
            delivered_source_ids=sources,
            loaded_skill_ids=skills,
        )

    def advance(self, next_status: DeliveryStatus) -> ContextReceipt:
        try:
            current_index = DELIVERY_LEVELS.index(self.status)
            next_index = DELIVERY_LEVELS.index(next_status)
        except ValueError as exc:
            raise ValueError("unknown delivery status") from exc
        if next_index != current_index + 1:
            raise ValueError("receipt must advance exactly one level")
        return replace(self, status=next_status)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["delivered_source_ids"] = list(self.delivered_source_ids)
        payload["loaded_skill_ids"] = list(self.loaded_skill_ids)
        return payload
