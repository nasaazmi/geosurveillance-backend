from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    username = Column(String, nullable=True)
    phone = Column(String(20), nullable=True)         # No. Telp di halaman profil
    avatar_path = Column(String(500), nullable=True)  # path file foto profil, bukan isi gambarnya
    bio = Column(String(100), nullable=True)          # teks kecil di bawah nama (opsional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())