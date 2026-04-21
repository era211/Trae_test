"""Event attribute system routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import (
    get_db, EventCategory, EventSubcategory, SentenceTemplate, CrawlTask
)
from backend.schemas import (
    EventCategoryCreate, EventCategoryUpdate, EventCategoryOut,
    EventSubcategoryCreate, EventSubcategoryUpdate, EventSubcategoryOut,
    SentenceTemplateCreate, SentenceTemplateUpdate, SentenceTemplateOut,
    CrawlTaskCreate, CrawlTaskOut, EventSystemStats
)

router = APIRouter(prefix="/api/events", tags=["events"])


def _category_out(cat: EventCategory, db: Session) -> dict:
    count = db.query(func.count(EventSubcategory.id)).filter(
        EventSubcategory.category_id == cat.id
    ).scalar() or 0
    out = EventCategoryOut.model_validate(cat)
    return {**out.model_dump(), "subcategory_count": count}


def _subcategory_out(sub: EventSubcategory, db: Session) -> dict:
    count = db.query(func.count(SentenceTemplate.id)).filter(
        SentenceTemplate.subcategory_id == sub.id
    ).scalar() or 0
    out = EventSubcategoryOut.model_validate(sub)
    return {**out.model_dump(), "template_count": count}


@router.get("/categories", response_model=list[EventCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(EventCategory).order_by(EventCategory.sort_order).all()
    return [_category_out(cat, db) for cat in categories]


@router.post("/categories", response_model=EventCategoryOut, status_code=201)
def create_category(data: EventCategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(EventCategory).filter(
        (EventCategory.code == data.code) | (EventCategory.name == data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this code or name already exists")
    cat = EventCategory(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _category_out(cat, db)


@router.get("/categories/{category_id}", response_model=EventCategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return _category_out(cat, db)


@router.put("/categories/{category_id}", response_model=EventCategoryOut)
def update_category(category_id: int, data: EventCategoryUpdate, db: Session = Depends(get_db)):
    cat = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return _category_out(cat, db)


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()


@router.get("/categories/{category_id}/subcategories", response_model=list[EventSubcategoryOut])
def list_subcategories(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    subs = db.query(EventSubcategory).filter(
        EventSubcategory.category_id == category_id
    ).order_by(EventSubcategory.sort_order).all()
    return [_subcategory_out(sub, db) for sub in subs]


@router.post("/subcategories", response_model=EventSubcategoryOut, status_code=201)
def create_subcategory(data: EventSubcategoryCreate, db: Session = Depends(get_db)):
    cat = db.query(EventCategory).filter(EventCategory.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    existing = db.query(EventSubcategory).filter(
        EventSubcategory.category_id == data.category_id,
        EventSubcategory.code == data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subcategory with this code already exists in the category")
    sub = EventSubcategory(**data.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return _subcategory_out(sub, db)


@router.get("/subcategories/{subcategory_id}", response_model=EventSubcategoryOut)
def get_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    sub = db.query(EventSubcategory).filter(EventSubcategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return _subcategory_out(sub, db)


@router.put("/subcategories/{subcategory_id}", response_model=EventSubcategoryOut)
def update_subcategory(subcategory_id: int, data: EventSubcategoryUpdate, db: Session = Depends(get_db)):
    sub = db.query(EventSubcategory).filter(EventSubcategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(sub, field, value)
    db.commit()
    db.refresh(sub)
    return _subcategory_out(sub, db)


@router.delete("/subcategories/{subcategory_id}", status_code=204)
def delete_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    sub = db.query(EventSubcategory).filter(EventSubcategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    db.delete(sub)
    db.commit()


@router.get("/subcategories/{subcategory_id}/templates", response_model=list[SentenceTemplateOut])
def list_templates(
    subcategory_id: int,
    is_cleaned: bool = None,
    is_verified: bool = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    sub = db.query(EventSubcategory).filter(EventSubcategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    q = db.query(SentenceTemplate).filter(SentenceTemplate.subcategory_id == subcategory_id)
    if is_cleaned is not None:
        q = q.filter(SentenceTemplate.is_cleaned == is_cleaned)
    if is_verified is not None:
        q = q.filter(SentenceTemplate.is_verified == is_verified)
    templates = q.order_by(SentenceTemplate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return templates


@router.post("/templates", response_model=SentenceTemplateOut, status_code=201)
def create_template(data: SentenceTemplateCreate, db: Session = Depends(get_db)):
    sub = db.query(EventSubcategory).filter(EventSubcategory.id == data.subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    template = SentenceTemplate(**data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=SentenceTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(SentenceTemplate).filter(SentenceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=SentenceTemplateOut)
def update_template(template_id: int, data: SentenceTemplateUpdate, db: Session = Depends(get_db)):
    template = db.query(SentenceTemplate).filter(SentenceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(SentenceTemplate).filter(SentenceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()


@router.post("/templates/bulk", status_code=201)
def create_templates_bulk(templates: list[SentenceTemplateCreate], db: Session = Depends(get_db)):
    db_templates = [SentenceTemplate(**t.model_dump()) for t in templates]
    db.add_all(db_templates)
    db.commit()
    return {"inserted": len(db_templates)}


@router.get("/crawl-tasks", response_model=list[CrawlTaskOut])
def list_crawl_tasks(db: Session = Depends(get_db)):
    return db.query(CrawlTask).order_by(CrawlTask.created_at.desc()).all()


@router.post("/crawl-tasks", response_model=CrawlTaskOut, status_code=201)
def create_crawl_task(data: CrawlTaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = CrawlTask(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/crawl-tasks/{task_id}", response_model=CrawlTaskOut)
def get_crawl_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Crawl task not found")
    return task


@router.get("/stats", response_model=EventSystemStats)
def get_event_stats(db: Session = Depends(get_db)):
    total_categories = db.query(func.count(EventCategory.id)).scalar() or 0
    total_subcategories = db.query(func.count(EventSubcategory.id)).scalar() or 0
    total_templates = db.query(func.count(SentenceTemplate.id)).scalar() or 0
    cleaned_templates = db.query(func.count(SentenceTemplate.id)).filter(
        SentenceTemplate.is_cleaned == True
    ).scalar() or 0
    verified_templates = db.query(func.count(SentenceTemplate.id)).filter(
        SentenceTemplate.is_verified == True
    ).scalar() or 0
    return EventSystemStats(
        total_categories=total_categories,
        total_subcategories=total_subcategories,
        total_templates=total_templates,
        cleaned_templates=cleaned_templates,
        verified_templates=verified_templates,
    )
