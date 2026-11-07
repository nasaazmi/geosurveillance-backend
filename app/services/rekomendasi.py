from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.peta import buat_rekomendasi


def rekomendasi_titik(db: Session, titik: Case, kategori: str, tingkat: str) -> dict:
    """Rekomendasi satu titik. Urutan: butir di tabel recommendations, lalu teks kustom, lalu template."""
    baris = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == titik.id)
        .order_by(Recommendation.id)
        .all()
    )
    if baris:
        return {
            "sumber": "manual" if any(b.sumber == "manual" for b in baris) else "otomatis",
            "peringatan": next((b.recommendation_text for b in baris if b.tipe == "peringatan"), None),
            "tindakan": [b.recommendation_text for b in baris if b.tipe == "tindakan"],
        }
    return buat_rekomendasi(kategori, tingkat, titik.wilayah, titik.jumlah_kasus, titik.rekomendasi)