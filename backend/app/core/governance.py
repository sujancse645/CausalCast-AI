from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class LineageEvent(BaseModel):
    event_id: str
    timestamp: str
    action: str
    actor_id: str
    details: dict[str, Any]


class DatasetGovernanceRecord(BaseModel):
    dataset_id: str
    classification: str = "internal"  # public, internal, confidential, restricted
    owner_id: str
    created_at: str
    lineage: list[LineageEvent] = Field(default_factory=list)
    compliance_tags: list[str] = Field(default_factory=list)


class ModelCard(BaseModel):
    model_id: str
    name: str
    version: str
    description: str
    intended_use: str
    limitations: str
    ethical_considerations: str
    metrics: dict[str, float]
    training_data_reference: str
    approved_by: str = ""
    approved_at: str = ""
    status: str = "draft"  # draft, approved, deprecated


def create_dataset_governance_record(
    dataset_id: str, owner_id: str, classification: str = "internal"
) -> DatasetGovernanceRecord:
    return DatasetGovernanceRecord(
        dataset_id=dataset_id,
        classification=classification,
        owner_id=owner_id,
        created_at=datetime.now(UTC).isoformat(),
    )


def add_lineage_event(
    record: DatasetGovernanceRecord, action: str, actor_id: str, details: dict[str, Any], event_id: str
) -> None:
    event = LineageEvent(
        event_id=event_id, timestamp=datetime.now(UTC).isoformat(), action=action, actor_id=actor_id, details=details
    )
    record.lineage.append(event)


def create_model_card(
    model_id: str,
    name: str,
    version: str,
    description: str,
    intended_use: str,
    limitations: str,
    ethical_considerations: str,
    metrics: dict[str, float],
    training_data_reference: str,
) -> ModelCard:
    return ModelCard(
        model_id=model_id,
        name=name,
        version=version,
        description=description,
        intended_use=intended_use,
        limitations=limitations,
        ethical_considerations=ethical_considerations,
        metrics=metrics,
        training_data_reference=training_data_reference,
    )
