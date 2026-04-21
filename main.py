"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from backend.database import init_db
from backend.routes import projects, datasets, generation


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="数据集生成与标注系统",
    description="A system for dataset generation and data annotation",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(generation.router)

# Serve static frontend files
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/", response_class=FileResponse)
async def serve_index():
    return str(frontend_dir / "index.html")


@app.get("/{path:path}", response_class=FileResponse)
async def serve_spa(path: str):
    """Serve SPA – fall back to index.html for client-side routes."""
    file_path = frontend_dir / path
    if file_path.exists() and file_path.is_file():
        return str(file_path)
    return str(frontend_dir / "index.html")
