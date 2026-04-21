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


# ──────────────────────────── Event Attribute System ────────────────────────────

class EventCategoryCreate(BaseModel):
    name: str
    code: str
    description: str = ""
    sort_order: int = 0


class EventCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class EventCategoryOut(BaseModel):
    id: int
    name: str
    code: str
    description: str
    sort_order: int
    is_active: bool
    subcategory_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventSubcategoryCreate(BaseModel):
    category_id: int
    name: str
    code: str
    description: str = ""
    sort_order: int = 0
    attributes_definition: list[dict] = []


class EventSubcategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    attributes_definition: list[dict] | None = None


class EventSubcategoryOut(BaseModel):
    id: int
    category_id: int
    name: str
    code: str
    description: str
    sort_order: int
    is_active: bool
    attributes_definition: list[dict]
    template_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SentenceTemplateCreate(BaseModel):
    subcategory_id: int
    content: str
    source: str | None = None
    source_url: str | None = None
    metadata: dict = {}


class SentenceTemplateUpdate(BaseModel):
    content: str | None = None
    is_cleaned: bool | None = None
    is_verified: bool | None = None
    metadata: dict | None = None


class SentenceTemplateOut(BaseModel):
    id: int
    subcategory_id: int
    content: str
    source: str | None
    source_url: str | None
    is_cleaned: bool
    is_verified: bool
    metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CrawlTaskCreate(BaseModel):
    name: str
    source_url: str
    source_name: str = "新疆日报"
    config: dict = {}


class CrawlTaskOut(BaseModel):
    id: int
    name: str
    source_name: str
    source_url: str
    status: str
    total_pages: int
    crawled_pages: int
    extracted_sentences: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class EventSystemStats(BaseModel):
    total_categories: int
    total_subcategories: int
    total_templates: int
    cleaned_templates: int
    verified_templates: int
