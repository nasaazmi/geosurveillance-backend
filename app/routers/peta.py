import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case
from app.models.project import KategoriProject, Project, StatusProject
from app.services.peta import LABEL_TINGKAT, buat_rekomendasi, jarak_km, satuan_kasus, tingkat_titik

router = APIRouter()

TERBIT = StatusProject.terbit.value


def _filter_project(query, kategori, provinsi, kabupaten, q):
    """Filter yang dipakai bersama oleh semua endpoint peta. Selalu hanya project terbit."""
    query = query.filter(Project.status == TERBIT)
    if kategori:
        query = query.filter(Project.kategori == kategori)
    if provinsi:
        query = query.filter(func.lower(Project.provinsi) == provinsi.strip().lower())
    if kabupaten:
        query = query.filter(func.lower(Project.kabupaten) == kabupaten.strip().lower())
    if q and q.strip():
        kata = q.strip().lower()
        query = query.filter(
            or_(
                func.lower(Project.provinsi).contains(kata, autoescape=True),
                func.lower(Project.kabupaten).contains(kata, autoescape=True),
            )
        )
    return query


def _query_titik(db, kolom, kategori, provinsi, kabupaten, q, tingkat=None):
    dasar = db.query(*kolom).select_from(Case).join(Project, Case.project_id == Project.id)
    dasar = _filter_project(dasar, kategori, provinsi, kabupaten, q)
    if tingkat == "tinggi":
        dasar = dasar.filter(Case.level_status == "merah")
    elif tingkat == "rendah":
        dasar = dasar.filter(Case.level_status != "merah")
    return dasar


@router.get("/opsi")
def get_opsi_filter(provinsi: str | None = Query(default=None), db: Session = Depends(get_db)):
    """Isi dropdown filter: kategori, provinsi, dan kabupaten (ikut terfilter kalau provinsi dipilih)."""
    pasangan = (
        db.query(Project.provinsi, Project.kabupaten)
        .filter(Project.status == TERBIT, Project.provinsi.isnot(None), Project.kabupaten.isnot(None))
        .distinct()
        .all()
    )
    pilih = provinsi.strip().lower() if provinsi else None
    return {
        "kategori": [k.value for k in KategoriProject],
        "tingkat": list(LABEL_TINGKAT),
        "provinsi": sorted({p for p, _ in pasangan}),
        "kabupaten": sorted({k for p, k in pasangan if pilih is None or p.lower() == pilih}),
    }


@router.get("/ringkasan")
def get_ringkasan(
    kategori: KategoriProject | None = Query(default=None),
    provinsi: str | None = Query(default=None),
    kabupaten: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Angka ringkas untuk header halaman peta (pakai kategori=bencana untuk peta bencana)."""
    jumlah_titik, total_kasus, jumlah_tinggi = _query_titik(
        db,
        (
            func.count(Case.id),
            func.coalesce(func.sum(Case.jumlah_kasus), 0),
            func.coalesce(func.sum(case((Case.level_status == "merah", 1), else_=0)), 0),
        ),
        kategori, provinsi, kabupaten, q,
    ).one()
    jumlah_project = _filter_project(db.query(func.count(Project.id)), kategori, provinsi, kabupaten, q).scalar()
    jumlah_titik, total_kasus, jumlah_tinggi = int(jumlah_titik), int(total_kasus), int(jumlah_tinggi)
    return {
        "kategori": kategori.value if kategori else None,
        "satuan": satuan_kasus(kategori.value) if kategori else "kasus",
        "jumlah_project": int(jumlah_project),
        "total_titik": jumlah_titik,
        "total_kasus": total_kasus,
        "legenda": {"rendah": jumlah_titik - jumlah_tinggi, "tinggi": jumlah_tinggi},
    }


@router.get("/titik")
def get_titik_peta(
    kategori: KategoriProject | None = Query(default=None),
    provinsi: str | None = Query(default=None),
    kabupaten: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Pencarian bebas provinsi atau kabupaten"),
    tingkat: Literal["rendah", "tinggi"] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Marker peta + legenda + pusat/radius tiap project. Hanya project terbit."""
    baris = (
        _query_titik(
            db,
            (Case.id, Case.project_id, Case.wilayah, Case.latitude, Case.longitude,
             Case.jumlah_kasus, Case.level_status),
            kategori, provinsi, kabupaten, q, tingkat,
        )
        .order_by(Case.id)
        .all()
    )
    legenda = {"rendah": 0, "tinggi": 0}
    titik = []
    for id_, project_id, wilayah, lat, lon, kasus, level in baris:
        tingkat_ini = tingkat_titik(level, kasus)
        legenda[tingkat_ini] += 1
        titik.append({
            "id": id_, "project_id": project_id, "wilayah": wilayah,
            "latitude": lat, "longitude": lon, "jumlah_kasus": kasus, "tingkat": tingkat_ini,
        })

    daftar_project = _filter_project(db.query(Project), kategori, provinsi, kabupaten, q).order_by(Project.id).all()
    return {
        "legenda": legenda,
        "total_titik": len(titik),
        "projects": [
            {
                "id": p.id, "nama": p.nama,
                "kategori": p.kategori.value if p.kategori else None,
                "provinsi": p.provinsi, "kabupaten": p.kabupaten,
                "pusat_latitude": p.latitude, "pusat_longitude": p.longitude,
                "radius_km": p.radius_km,
            }
            for p in daftar_project
        ],
        "titik": titik,
    }


@router.get("/hasil")
def get_hasil_pencarian(
    kategori: KategoriProject | None = Query(default=None),
    provinsi: str | None = Query(default=None),
    kabupaten: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tingkat: Literal["rendah", "tinggi"] | None = Query(default=None),
    halaman: int = Query(default=1, ge=1),
    per_halaman: int = Query(default=4, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Tabel 'Hasil Pencarian' di bawah peta, dengan pagination. Urut dari kasus terbanyak."""
    dasar = _query_titik(
        db,
        (Case.id, Case.project_id, Case.wilayah, Project.kabupaten, Project.provinsi,
         Project.kategori, Case.jumlah_kasus, Case.level_status),
        kategori, provinsi, kabupaten, q, tingkat,
    )
    total = dasar.count()
    baris = (
        dasar.order_by(Case.jumlah_kasus.desc(), Case.id)
        .offset((halaman - 1) * per_halaman)
        .limit(per_halaman)
        .all()
    )
    items = []
    for id_, project_id, wilayah, kab, prov, kat, kasus, level in baris:
        tingkat_ini = tingkat_titik(level, kasus)
        kat_nilai = kat.value if kat else None
        items.append({
            "id": id_, "project_id": project_id, "wilayah": wilayah,
            "kabupaten_kota": kab, "provinsi": prov,
            "kategori": kat_nilai, "satuan": satuan_kasus(kat_nilai or "penyakit"),
            "total_kasus": kasus, "tingkat": tingkat_ini, "status": LABEL_TINGKAT[tingkat_ini],
        })
    return {
        "total_kecamatan_terpantau": total,
        "halaman": halaman,
        "per_halaman": per_halaman,
        "total_halaman": math.ceil(total / per_halaman),
        "items": items,
    }


@router.get("/titik/{case_id}")
def get_detail_titik(case_id: int, db: Session = Depends(get_db)):
    """Detail satu titik kasus (saat marker atau baris tabel diklik). Hanya project terbit."""
    baris = (
        db.query(Case, Project)
        .join(Project, Case.project_id == Project.id)
        .filter(Case.id == case_id, Project.status == TERBIT)
        .first()
    )
    if baris is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Titik tidak ditemukan atau belum terbit.")
    titik, project = baris

    tingkat = tingkat_titik(titik.level_status, titik.jumlah_kasus)
    kategori = project.kategori.value if project.kategori else "penyakit"

    total_titik, total_kasus = (
        db.query(func.count(Case.id), func.coalesce(func.sum(Case.jumlah_kasus), 0))
        .filter(Case.project_id == project.id)
        .one()
    )
    total_titik, total_kasus = int(total_titik), int(total_kasus)
    lebih_banyak = (
        db.query(func.count(Case.id))
        .filter(Case.project_id == project.id, Case.jumlah_kasus > titik.jumlah_kasus)
        .scalar()
    )

    jarak = None
    di_dalam_radius = None
    if project.latitude is not None and project.longitude is not None:
        jarak = round(jarak_km(titik.latitude, titik.longitude, project.latitude, project.longitude), 2)
        if project.radius_km is not None:
            di_dalam_radius = jarak <= project.radius_km

    return {
        "id": titik.id,
        "wilayah": titik.wilayah,
        "kabupaten_kota": project.kabupaten,
        "provinsi": project.provinsi,
        "kategori": kategori,
        "satuan": satuan_kasus(kategori),
        "latitude": titik.latitude,
        "longitude": titik.longitude,
        "jumlah_kasus": titik.jumlah_kasus,
        "tingkat": tingkat,
        "status": LABEL_TINGKAT[tingkat],
        "peringkat": int(lebih_banyak) + 1,
        "total_titik_project": total_titik,
        "proporsi_kasus_persen": round(titik.jumlah_kasus / total_kasus * 100, 1) if total_kasus else 0.0,
        "jarak_dari_pusat_km": jarak,
        "di_dalam_radius": di_dalam_radius,
        "project": {
            "id": project.id,
            "nama": project.nama,
            "deskripsi": project.deskripsi,
            "pusat_latitude": project.latitude,
            "pusat_longitude": project.longitude,
            "radius_km": project.radius_km,
            "total_kasus": total_kasus,
            "data_diperbarui_pada": project.data_diperbarui_pada,
        },
        "rekomendasi": buat_rekomendasi(kategori, tingkat, titik.wilayah, titik.jumlah_kasus, titik.rekomendasi),
        "dicatat_pada": titik.created_at,
    }


@router.get("/titik/{case_id}/rekomendasi")
def get_rekomendasi_titik(case_id: int, db: Session = Depends(get_db)):
    """Isi popup 'Rekomendasi Tindakan Publik' saat sebuah titik diklik."""
    baris = (
        db.query(Case, Project.kategori)
        .join(Project, Case.project_id == Project.id)
        .filter(Case.id == case_id, Project.status == TERBIT)
        .first()
    )
    if baris is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Titik tidak ditemukan atau belum terbit.")
    titik, kategori = baris
    tingkat = tingkat_titik(titik.level_status, titik.jumlah_kasus)
    kat = kategori.value if kategori else "penyakit"
    return {
        "id": titik.id,
        "wilayah": titik.wilayah,
        "kategori": kat,
        "jumlah_kasus": titik.jumlah_kasus,
        "tingkat": tingkat,
        "status": LABEL_TINGKAT[tingkat],
        **buat_rekomendasi(kat, tingkat, titik.wilayah, titik.jumlah_kasus, titik.rekomendasi),
    }