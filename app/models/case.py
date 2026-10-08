from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func

from app.database import Base


class Case(Base):
    """Satu baris data = satu titik lokasi di peta (hasil upload dataset)."""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    wilayah = Column(String, nullable=False)       # nama kabupaten/kota
    provinsi = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    jumlah_kasus = Column(Integer, nullable=False, default=0)
    level_status = Column(String, nullable=False, default="hijau")  # hijau/kuning/merah
    rekomendasi = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
