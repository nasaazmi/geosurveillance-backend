from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    nama: str
    deskripsi: str | None = None
    kategori: str  # "penyakit" atau "bencana"


class ProjectResponse(BaseModel):
    id: int
    nama: str
    deskripsi: str | None
    kategori: str
    created_at: datetime

    class Config:
        from_attributes = True
