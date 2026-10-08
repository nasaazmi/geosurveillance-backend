from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Ringkasan project milik owner yang sedang login (perlu auth)."""
    # TODO: ambil user dari token, query semua project miliknya
    return {"total_project": 0, "projects": []}


@router.post("/project", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Buat project baru (penyakit/bencana) — langsung publish tanpa approval."""
    # TODO: simpan ke tabel projects, owner_id dari user yang login
    ...
