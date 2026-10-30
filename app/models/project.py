import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class KategoriProject(str, enum.Enum):
    penyakit = "penyakit"
    bencana = "bencana"


class StatusProject(str, enum.Enum):
    draft = "draft"
    terbit = "terbit"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Langkah 1: Profil Proyek
    nama = Column(String, nullable=False)
    deskripsi = Column(String, nullable=True)

    # Langkah 2: Design Lokasi (kosong dulu saat project masih draft awal)
    kategori = Column(Enum(KategoriProject), nullable=True)
    provinsi = Column(String, nullable=True)
    kabupaten = Column(String, nullable=True)
    jenis = Column(String, nullable=True)
    latitude = Column(Float, nullable=True) 
    longitude = Column(Float, nullable=True)   
    radius_km = Column(Float, nullable=True)  
    status = Column(
        String,
        nullable=False,
        default=StatusProject.draft.value,
        server_default=StatusProject.draft.value,
    )

    nama_file = Column(String, nullable=True)
    data_diperbarui_pada = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())