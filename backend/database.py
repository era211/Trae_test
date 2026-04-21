"""Database configuration and session management."""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SAEnum, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from datetime import datetime
import enum

DATABASE_URL = "sqlite:///./dataset_annotation.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class EventCategory(Base):
    __tablename__ = "event_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    subcategories = relationship("EventSubcategory", back_populates="category", cascade="all, delete-orphan")


class EventSubcategory(Base):
    __tablename__ = "event_subcategories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("event_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    attributes_definition = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    category = relationship("EventCategory", back_populates="subcategories")
    templates = relationship("SentenceTemplate", back_populates="subcategory", cascade="all, delete-orphan")


class SentenceTemplate(Base):
    __tablename__ = "sentence_templates"

    id = Column(Integer, primary_key=True, index=True)
    subcategory_id = Column(Integer, ForeignKey("event_subcategories.id"), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)
    is_cleaned = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    subcategory = relationship("EventSubcategory", back_populates="templates")


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    source_name = Column(String(100), default="新疆日报")
    source_url = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")
    total_pages = Column(Integer, default=0)
    crawled_pages = Column(Integer, default=0)
    extracted_sentences = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class TaskType(str, enum.Enum):
    text_classification = "text_classification"
    ner = "ner"
    text_generation = "text_generation"
    qa = "qa"
    instruction_tuning = "instruction_tuning"


class AnnotationStatus(str, enum.Enum):
    pending = "pending"
    annotated = "annotated"
    reviewed = "reviewed"
    rejected = "rejected"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    task_type = Column(SAEnum(TaskType), nullable=False)
    labels = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    project = relationship("Project", back_populates="datasets")
    items = relationship("DataItem", back_populates="dataset", cascade="all, delete-orphan")


class DataItem(Base):
    __tablename__ = "data_items"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    content = Column(JSON, nullable=False)
    status = Column(SAEnum(AnnotationStatus), default=AnnotationStatus.pending)
    annotation = Column(JSON, nullable=True)
    annotator = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    dataset = relationship("Dataset", back_populates="items")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
