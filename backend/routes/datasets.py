"""Dataset management routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db, Project, Dataset, DataItem, AnnotationStatus
from backend.schemas import DatasetCreate, DatasetUpdate, DatasetOut, DataItemCreate, DataItemOut, DataItemAnnotate

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _dataset_out(ds: Dataset, db: Session) -> dict:
    count = db.query(func.count(DataItem.id)).filter(DataItem.dataset_id == ds.id).scalar() or 0
    out = DatasetOut.model_validate(ds)
    return {**out.model_dump(), "item_count": count}


@router.get("/project/{project_id}", response_model=list[DatasetOut])
def list_datasets(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    datasets = db.query(Dataset).filter(Dataset.project_id == project_id).order_by(Dataset.created_at.desc()).all()
    return [_dataset_out(ds, db) for ds in datasets]


@router.post("/project/{project_id}", response_model=DatasetOut, status_code=201)
def create_dataset(project_id: int, data: DatasetCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ds = Dataset(project_id=project_id, **data.model_dump())
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return _dataset_out(ds, db)


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _dataset_out(ds, db)


@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(dataset_id: int, data: DatasetUpdate, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ds, field, value)
    db.commit()
    db.refresh(ds)
    return _dataset_out(ds, db)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(ds)
    db.commit()


# ──────────────── Items ────────────────

@router.get("/{dataset_id}/items", response_model=list[DataItemOut])
def list_items(
    dataset_id: int,
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    q = db.query(DataItem).filter(DataItem.dataset_id == dataset_id)
    if status:
        q = q.filter(DataItem.status == status)
    items = q.order_by(DataItem.id).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.post("/{dataset_id}/items", response_model=DataItemOut, status_code=201)
def add_item(dataset_id: int, data: DataItemCreate, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    item = DataItem(dataset_id=dataset_id, content=data.content)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{dataset_id}/items/bulk", status_code=201)
def add_items_bulk(dataset_id: int, items: list[DataItemCreate], db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db_items = [DataItem(dataset_id=dataset_id, content=item.content) for item in items]
    db.add_all(db_items)
    db.commit()
    return {"inserted": len(db_items)}


@router.get("/{dataset_id}/items/{item_id}", response_model=DataItemOut)
def get_item(dataset_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(DataItem).filter(DataItem.id == item_id, DataItem.dataset_id == dataset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/{dataset_id}/items/{item_id}/annotate", response_model=DataItemOut)
def annotate_item(dataset_id: int, item_id: int, data: DataItemAnnotate, db: Session = Depends(get_db)):
    item = db.query(DataItem).filter(DataItem.id == item_id, DataItem.dataset_id == dataset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.annotation = data.annotation
    item.annotator = data.annotator
    item.status = AnnotationStatus.annotated
    db.commit()
    db.refresh(item)
    return item


@router.post("/{dataset_id}/items/{item_id}/review")
def review_item(dataset_id: int, item_id: int, approved: bool, db: Session = Depends(get_db)):
    item = db.query(DataItem).filter(DataItem.id == item_id, DataItem.dataset_id == dataset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.status = AnnotationStatus.reviewed if approved else AnnotationStatus.rejected
    db.commit()
    return {"status": item.status}


@router.get("/{dataset_id}/export")
def export_dataset(dataset_id: int, fmt: str = "jsonl", db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()
    if fmt == "jsonl":
        import json
        lines = []
        for item in items:
            record = {**item.content, "annotation": item.annotation, "status": item.status.value}
            lines.append(json.dumps(record, ensure_ascii=False))
        content = "\n".join(lines)
        return JSONResponse(content={"data": content, "filename": f"{ds.name}.jsonl"})
    # JSON array
    records = [{**item.content, "annotation": item.annotation, "status": item.status.value} for item in items]
    return JSONResponse(content={"data": records, "filename": f"{ds.name}.json"})
