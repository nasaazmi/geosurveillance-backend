from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/publik")
def get_beranda_publik(db: Session = Depends(get_db)):
    """Data untuk 4 kartu statistik + kategori pemantauan di homepage."""
    # TODO: hitung total wilayah terpantau, titik waspada tinggi, area siaga, wilayah aman
    return {
        "total_terpantau": 0,
        "titik_waspada_tinggi": 0,
        "area_siaga_bencana": 0,
        "wilayah_status_aman": 0,
        "kategori": [],
    }


@router.get("/filter")
def filter_beranda(
    provinsi: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Filter data publik berdasarkan wilayah (provinsi/kabupaten) dan kategori (penyakit/bencana)."""
    # TODO: query Case join Project, filter sesuai parameter
    return {"provinsi": provinsi, "kategori": kategori, "results": []}
