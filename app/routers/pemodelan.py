from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_owned_project
from app.database import get_db
from app.models.case import Case
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.schemas.pemodelan import ProsesResponse, RekomendasiInput, RekomendasiOwnerResponse
from app.services.pemodelan import JARAK_BAWAAN_KM, jalankan_pemodelan
from app.services.peta import tingkat_titik
from app.services.rekomendasi import rekomendasi_titik

router = APIRouter()


def _ambil_titik(db: Session, project: Project, case_id: int) -> Case:
    titik = db.query(Case).filter(Case.id == case_id, Case.project_id == project.id).first()
    if titik is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Titik tidak ditemukan di project ini.")
    return titik


def _respons(db: Session, project: Project, titik: Case) -> dict:
    kategori = project.kategori.value if project.kategori else "penyakit"
    return {
        "case_id": titik.id,
        "wilayah": titik.wilayah,
        **rekomendasi_titik(db, titik, kategori, tingkat_titik(titik.level_status)),
    }


@router.post("/{project_id}/proses", response_model=ProsesResponse)
def proses_data(
    jarak_km: float = Query(default=JARAK_BAWAAN_KM, gt=0, le=100, description="Jarak penyebaran dari titik merah (km)"),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Proses permodelan data: sebarkan status merah ke titik sekitar, lalu buat rekomendasi tiap titik.

    Aman dijalankan berulang. Rekomendasi yang diisi manual tidak ditimpa.
    """
    hasil = jalankan_pemodelan(db, project, jarak_km)
    if hasil is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Belum ada data titik. Upload CSV dulu.")
    return hasil


@router.get("/{project_id}/titik/{case_id}/rekomendasi", response_model=RekomendasiOwnerResponse)
def get_rekomendasi_owner(
    case_id: int,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Lihat rekomendasi satu titik milik project sendiri."""
    return _respons(db, project, _ambil_titik(db, project, case_id))


@router.put("/{project_id}/titik/{case_id}/rekomendasi", response_model=RekomendasiOwnerResponse)
def isi_rekomendasi_manual(
    case_id: int,
    data: RekomendasiInput,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Tulis rekomendasi sendiri untuk satu titik. Menggantikan semua butir lama dan tidak ditimpa proses otomatis."""
    titik = _ambil_titik(db, project, case_id)
    db.query(Recommendation).filter(Recommendation.case_id == titik.id).delete(synchronize_session=False)
    if data.peringatan:
        db.add(Recommendation(case_id=titik.id, tipe="peringatan", sumber="manual", recommendation_text=data.peringatan))
    for teks in data.tindakan:
        db.add(Recommendation(case_id=titik.id, tipe="tindakan", sumber="manual", recommendation_text=teks))
    db.commit()
    return _respons(db, project, titik)


@router.delete("/{project_id}/titik/{case_id}/rekomendasi", status_code=status.HTTP_204_NO_CONTENT)
def hapus_rekomendasi_manual(
    case_id: int,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Hapus rekomendasi manual. Titik kembali memakai teks bawaan sampai proses dijalankan lagi."""
    titik = _ambil_titik(db, project, case_id)
    db.query(Recommendation).filter(
        Recommendation.case_id == titik.id, Recommendation.sumber == "manual"
    ).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)