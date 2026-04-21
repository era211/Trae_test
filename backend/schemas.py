"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from backend.database import TaskType, AnnotationStatus


# ──────────────────────────── Project ────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    task_type: TaskType
    labels: list[str] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[list[str]] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    task_type: TaskType
    labels: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── Dataset ────────────────────────────

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DatasetOut(BaseModel):
    id: int
    name: str
    description: str
    project_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0

    model_config = {"from_attributes": True}


# ──────────────────────────── DataItem ────────────────────────────

class DataItemCreate(BaseModel):
    content: dict[str, Any]


class DataItemAnnotate(BaseModel):
    annotation: dict[str, Any]
    annotator: str = "anonymous"


class DataItemOut(BaseModel):
    id: int
    dataset_id: int
    content: dict[str, Any]
    status: AnnotationStatus
    annotation: Optional[dict[str, Any]]
    annotator: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── Generation ────────────────────────────

class GenerationRequest(BaseModel):
    project_id: int
    dataset_name: str
    count: int = Field(default=10, ge=1, le=1000)
    generation_type: str = "auto"
    extra_params: dict[str, Any] = {}


class ImportRequest(BaseModel):
    project_id: int
    dataset_name: str
    items: list[dict[str, Any]]


# ──────────────────────────── Stats ────────────────────────────

class ProjectStats(BaseModel):
    project_id: int
    total_items: int
    pending: int
    annotated: int
    reviewed: int
    rejected: int
    progress_pct: float
