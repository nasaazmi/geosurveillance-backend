from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.models.project import KategoriProject, Project, StatusProject

router = APIRouter()

TERBIT = StatusProject.terbit.value


def _hitung_merah():
    """Jumlah titik merah (dipakai di beberapa query)."""
    return func.coalesce(func.sum(case((Case.level_status == "merah", 1), else_=0)), 0)


@router.get("/publik")
def get_beranda_publik(db: Session = Depends(get_db)):
    """Data untuk 4 kartu statistik + kategori pemantauan di homepage. Hanya project terbit."""
    total_terpantau, titik_merah, titik_hijau = (
        db.query(
            func.count(Case.id),
            _hitung_merah(),
            func.coalesce(func.sum(case((Case.level_status == "hijau", 1), else_=0)), 0),
        )
        .join(Project, Case.project_id == Project.id)
        .filter(Project.status == TERBIT)
        .one()
    )

    area_siaga_bencana = (
        db.query(func.count(Project.id))
        .filter(Project.status == TERBIT, Project.kategori == KategoriProject.bencana)
        .scalar()
    )

    # Rincian per kategori (penyakit / bencana). Kategori tanpa project tetap tampil dengan nilai 0.
    per_kategori = {k.value: {"kategori": k.value, "jumlah_project": 0, "jumlah_titik": 0, "titik_waspada_tinggi": 0}
                    for k in KategoriProject}
    baris = (
        db.query(
            Project.kategori,
            func.count(func.distinct(Project.id)),
            func.count(Case.id),
            _hitung_merah(),
        )
        .outerjoin(Case, Case.project_id == Project.id)
        .filter(Project.status == TERBIT, Project.kategori.isnot(None))
        .group_by(Project.kategori)
        .all()
    )
    for kategori, jumlah_project, jumlah_titik, merah in baris:
        per_kategori[kategori.value] = {
            "kategori": kategori.value,
            "jumlah_project": int(jumlah_project),
            "jumlah_titik": int(jumlah_titik),
            "titik_waspada_tinggi": int(merah),
        }

    return {
        "total_terpantau": int(total_terpantau),
        "titik_waspada_tinggi": int(titik_merah),
        "area_siaga_bencana": int(area_siaga_bencana),
        "wilayah_status_aman": int(titik_hijau),
        "kategori": list(per_kategori.values()),
    }


@router.get("/filter")
def filter_beranda(
    provinsi: str | None = Query(default=None),
    kabupaten: str | None = Query(default=None),
    kategori: KategoriProject | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Daftar project terbit, bisa difilter provinsi, kabupaten, dan kategori (penyakit/bencana)."""
    query = (
        db.query(
            Project.id,
            Project.nama,
            Project.kategori,
            Project.provinsi,
            Project.kabupaten,
            func.count(Case.id),
            func.coalesce(func.sum(Case.jumlah_kasus), 0),
            _hitung_merah(),
        )
        .outerjoin(Case, Case.project_id == Project.id)
        .filter(Project.status == TERBIT)
    )
    if provinsi:
        query = query.filter(func.lower(Project.provinsi) == provinsi.strip().lower())
    if kabupaten:
        query = query.filter(func.lower(Project.kabupaten) == kabupaten.strip().lower())
    if kategori:
        query = query.filter(Project.kategori == kategori)

    baris = query.group_by(Project.id).order_by(Project.created_at.desc()).all()
    return {
        "provinsi": provinsi,
        "kabupaten": kabupaten,
        "kategori": kategori.value if kategori else None,
        "results": [
            {
                "id": b[0],
                "nama": b[1],
                "kategori": b[2].value if b[2] else None,
                "provinsi": b[3],
                "kabupaten": b[4],
                "jumlah_titik": int(b[5]),
                "total_kasus": int(b[6]),
                "jumlah_merah": int(b[7]),
            }
            for b in baris
        ],
    }