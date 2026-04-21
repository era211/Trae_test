"""Main FastAPI application entry point."""
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, EventCategory, EventSubcategory
from backend.routes import projects, datasets, generation, events
from backend.generators.event_init_data import EVENT_CATEGORIES, EVENT_SUBCATEGORIES


def init_event_system(db: Session):
    """Initialize event attribute system with predefined data."""
    existing_count = db.query(EventCategory).count()
    if existing_count > 0:
        print(f"Event system already initialized with {existing_count} categories.")
        return

    print("Initializing event attribute system...")

    for cat_data in EVENT_CATEGORIES:
        cat = EventCategory(**cat_data)
        db.add(cat)
        db.flush()

        subcats = EVENT_SUBCATEGORIES.get(cat_data["code"], [])
        for sub_data in subcats:
            sub = EventSubcategory(category_id=cat.id, **sub_data)
            db.add(sub)

    db.commit()

    total_cats = db.query(EventCategory).count()
    total_subcats = db.query(EventSubcategory).count()
    print(f"Event system initialized: {total_cats} categories, {total_subcats} subcategories.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = next(get_db())
    try:
        init_event_system(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="数据集生成与标注系统",
    description="A system for dataset generation and data annotation with event attribute system",
    version="2.0.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(generation.router)
app.include_router(events.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/init-status")
async def init_status(db: Session = Depends(get_db)):
    """Check initialization status."""
    total_cats = db.query(EventCategory).count()
    total_subcats = db.query(EventSubcategory).count()
    return {
        "categories": total_cats,
        "subcategories": total_subcats,
        "is_initialized": total_cats > 0,
    }

# Serve static frontend files
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/", response_class=FileResponse)
async def serve_index():
    return str(frontend_dir / "index.html")


@app.get("/{path:path}", response_class=FileResponse)
async def serve_spa(path: str):
    """SPA fallback – always return index.html for unknown client-side routes.
    Static assets (CSS, JS, etc.) are served by the /static mount above."""
    return str(frontend_dir / "index.html")
