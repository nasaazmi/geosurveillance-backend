from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base


class KategoriProject(str, enum.Enum):
    penyakit = "penyakit"
    bencana = "bencana"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nama = Column(String, nullable=False)
    deskripsi = Column(String, nullable=True)
    kategori = Column(Enum(KategoriProject), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
