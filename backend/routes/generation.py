"""Dataset generation routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, Project, Dataset, DataItem
from backend.schemas import GenerationRequest, ImportRequest
from backend.generators.data_generator import generate_samples

router = APIRouter(prefix="/api/generate", tags=["generation"])


@router.post("", status_code=201)
def generate_dataset(req: GenerationRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ds = Dataset(project_id=project.id, name=req.dataset_name, description=f"Auto-generated: {req.generation_type}")
    db.add(ds)
    db.flush()

    samples = generate_samples(
        task_type=project.task_type.value,
        count=req.count,
        labels=project.labels,
        **req.extra_params,
    )
    items = [DataItem(dataset_id=ds.id, content=s) for s in samples]
    db.add_all(items)
    db.commit()
    db.refresh(ds)
    return {"dataset_id": ds.id, "name": ds.name, "generated": len(items)}


@router.post("/import", status_code=201)
def import_dataset(req: ImportRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ds = Dataset(project_id=project.id, name=req.dataset_name, description="Imported dataset")
    db.add(ds)
    db.flush()

    items = [DataItem(dataset_id=ds.id, content=item) for item in req.items]
    db.add_all(items)
    db.commit()
    return {"dataset_id": ds.id, "name": ds.name, "imported": len(items)}
