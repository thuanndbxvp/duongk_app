"""
Pydantic schemas for batch — Phase 10.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class BatchCreateRequest(BaseModel):
    name: str = ""
    project_ids: list[UUID] = Field(..., min_length=1, max_length=50)
    task_type: str = "render_draft"

    model_config = {"extra": "forbid"}


class BatchResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    status: str
    total_items: int
    succeeded_items: int
    failed_items: int
    total_cost_estimate: int
    total_cost_actual: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchItemResponse(BaseModel):
    id: UUID
    batch_id: UUID
    project_id: UUID
    item_index: int
    task_type: str
    status: str
    provider: Optional[str] = None
    fallback_used: bool = False
    retry_count: int = 0
    error_message: Optional[str] = None
    cost_estimate: int = 0
    cost_actual: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CostEstimate(BaseModel):
    total: int
    per_item: int
    item_count: int
    model_version: str = "v1"
    captured_at: datetime = Field(default_factory=datetime.now)
