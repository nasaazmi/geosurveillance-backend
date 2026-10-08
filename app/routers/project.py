from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.project import ProjectResponse
from app.schemas.case import CaseResponse

router = APIRouter()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """Detail satu project."""
    # TODO: query project by id, 404 jika tidak ada
    ...


@router.post("/{project_id}/upload")
async def upload_dataset(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload dataset spasial (CSV/GeoJSON/SHP), diproses lalu disimpan sebagai Case."""
    # TODO: baca file sesuai ekstensi, validasi kolom wajib (wilayah, lat, long, jumlah_kasus)
    # TODO: hitung level_status berdasarkan threshold, simpan tiap baris sebagai Case
    return {"filename": file.filename, "status": "processing"}


@router.get("/{project_id}/data", response_model=List[CaseResponse])
def get_project_data(project_id: int, db: Session = Depends(get_db)):
    """Data titik-titik untuk di-plot ke peta pada project ini."""
    # TODO: query semua Case milik project_id
    return []
