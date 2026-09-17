from datetime import datetime, timezone

import pytest

from ai_context_kit.task_contracts import (
    ContextReceipt,
    TaskEnvelope,
    canonical_digest,
)


def test_task_envelope_serializes_without_provider_prompt_fields() -> None:
    envelope = TaskEnvelope.create(
        task_id="task-123",
        target_project="content-workbench",
        intent="Refresh the current interview project view",
        requested_by="human",
        platform="codex",
        created_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )

    assert envelope.to_dict() == {
        "schema": "task-envelope/v1",
        "task_id": "task-123",
        "target_project": "content-workbench",
        "intent": "Refresh the current interview project view",
        "requested_by": "human",
        "platform": "codex",
        "created_at": "2026-09-16T00:00:00+00:00",
    }


def test_task_envelope_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone"):
        TaskEnvelope.create(
            task_id="task-123",
            target_project="content-workbench",
            intent="Refresh project view",
            requested_by="human",
            platform="codex",
            created_at=datetime(2026, 9, 16),
        )


def test_receipt_rejects_initial_claim_jump() -> None:
    with pytest.raises(ValueError, match="initial status"):
        ContextReceipt.create(
            receipt_id="receipt-123",
            task_id="task-123",
            attempt_id="attempt-1",
            bundle_id="bundle-123",
            platform="codex",
            adapter="codex-hooks",
            status="effective",
            delivered_source_ids=("source-1",),
            loaded_skill_ids=(),
        )


def test_delivered_receipt_requires_a_source_identifier() -> None:
    with pytest.raises(ValueError, match="source"):
        ContextReceipt.create(
            receipt_id="receipt-123",
            task_id="task-123",
            attempt_id="attempt-1",
            bundle_id="bundle-123",
            platform="codex",
            adapter="codex-hooks",
            status="delivered",
            delivered_source_ids=(),
            loaded_skill_ids=(),
        )


def test_receipt_advances_one_observable_claim_at_a_time() -> None:
    receipt = ContextReceipt.create(
        receipt_id="receipt-123",
        task_id="task-123",
        attempt_id="attempt-1",
        bundle_id="bundle-123",
        platform="codex",
        adapter="codex-hooks",
        status="delivered",
        delivered_source_ids=("source-1",),
        loaded_skill_ids=("skill-1",),
    )

    acknowledged = receipt.advance("acknowledged")
    assert acknowledged.status == "acknowledged"
    assert acknowledged.delivered_source_ids == ("source-1",)
    with pytest.raises(ValueError, match="one level"):
        acknowledged.advance("effective")


def test_canonical_digest_is_key_order_independent() -> None:
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
