from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.project import Project
from app.services.csv_import import AMBANG_MERAH_DEFAULT

AMBANG_MERAH = AMBANG_MERAH_DEFAULT


def hitung_ringkasan_data(db: Session, project_id: int) -> dict:
    """Hitung jumlah titik, total kasus, jumlah merah dan hijau langsung dari tabel cases."""
    jumlah_titik, total_kasus, jumlah_merah = (
        db.query(
            func.count(Case.id),
            func.coalesce(func.sum(Case.jumlah_kasus), 0),
            func.coalesce(func.sum(case((Case.level_status == "merah", 1), else_=0)), 0),
        )
        .filter(Case.project_id == project_id)
        .one()
    )
    jumlah_titik, total_kasus, jumlah_merah = int(jumlah_titik), int(total_kasus), int(jumlah_merah)
    return {
        "jumlah_titik": jumlah_titik,
        "total_kasus": total_kasus,
        "jumlah_merah": jumlah_merah,
        "jumlah_hijau": jumlah_titik - jumlah_merah,
    }


def cek_kesiapan(project: Project, jumlah_titik: int) -> list[str]:
    """Daftar hal yang belum lengkap. Kosong berarti project siap diterbitkan."""
    belum_lengkap: list[str] = []

    lokasi_lengkap = all(
        nilai is not None
        for nilai in (
            project.kategori,
            project.provinsi,
            project.kabupaten,
            project.latitude,
            project.longitude,
            project.radius_km,
        )
    )
    if not lokasi_lengkap:
        belum_lengkap.append("Lokasi belum lengkap (langkah 2: Design Lokasi).")
    if jumlah_titik < 1:
        belum_lengkap.append("Belum ada data titik (langkah 3: upload CSV).")
    return belum_lengkap