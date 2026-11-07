from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Recommendation(Base):

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    tipe = Column(String(20), nullable=False, default="tindakan")    # peringatan | tindakan
    sumber = Column(String(10), nullable=False, default="otomatis")  # otomatis | manual
    recommendation_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())