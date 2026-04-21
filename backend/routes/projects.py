"""Project management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db, Project, Dataset, DataItem, AnnotationStatus
from backend.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectStats

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


@router.get("/{project_id}/stats", response_model=ProjectStats)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    dataset_ids = [d.id for d in project.datasets]
    if not dataset_ids:
        return ProjectStats(
            project_id=project_id,
            total_items=0, pending=0, annotated=0, reviewed=0, rejected=0,
            progress_pct=0.0,
        )

    counts = (
        db.query(DataItem.status, func.count(DataItem.id))
        .filter(DataItem.dataset_id.in_(dataset_ids))
        .group_by(DataItem.status)
        .all()
    )
    status_map = {s: c for s, c in counts}
    total = sum(status_map.values())
    annotated = status_map.get(AnnotationStatus.annotated, 0)
    reviewed = status_map.get(AnnotationStatus.reviewed, 0)
    rejected = status_map.get(AnnotationStatus.rejected, 0)
    pending = status_map.get(AnnotationStatus.pending, 0)
    done = annotated + reviewed + rejected
    return ProjectStats(
        project_id=project_id,
        total_items=total,
        pending=pending,
        annotated=annotated,
        reviewed=reviewed,
        rejected=rejected,
        progress_pct=round(done / total * 100, 1) if total else 0.0,
    )
