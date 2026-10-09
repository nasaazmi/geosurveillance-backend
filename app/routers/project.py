from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_owned_project
from app.database import get_db
from app.models.case import Case
from app.models.project import Project
from app.schemas.case import CaseResponse, UploadResponse
from app.services.csv_import import (
    AMBANG_MERAH_DEFAULT,
    CsvTidakValid,
    baca_csv_kasus,
    tentukan_status,
)

router = APIRouter()

MAKS_UKURAN_BYTE = 5 * 1024 * 1024  # 5 MB


@router.post("/{project_id}/upload", response_model=UploadResponse)
def upload_dataset(
    file: UploadFile = File(...),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Langkah 3 (Design Data): upload CSV berisi titik kasus. Upload ulang menggantikan data lama."""
    nama_file = file.filename or ""
    if not nama_file.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Saat ini hanya file .csv yang didukung (GeoJSON dan SHP menyusul).",
        )

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lengkapi Design Lokasi (langkah 2) sebelum mengunggah data.",
        )

    isi = file.file.read(MAKS_UKURAN_BYTE + 1)
    if len(isi) > MAKS_UKURAN_BYTE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran file maksimal 5 MB.",
        )

    try:
        baris_data = baca_csv_kasus(isi)
    except CsvTidakValid as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "pesan": e.pesan,
                "kesalahan": e.kesalahan,
                "total_kesalahan": e.total_kesalahan,
            },
        )

    # Semua baris sudah valid. Ganti data lama dalam satu transaksi.
    db.query(Case).filter(Case.project_id == project.id).delete()
    db.add_all(
        [
            Case(
                project_id=project.id,
                wilayah=b["wilayah"],
                provinsi=project.provinsi,  # provinsi diambil dari langkah 2
                latitude=b["latitude"],
                longitude=b["longitude"],
                jumlah_kasus=b["jumlah_kasus"],
                level_status=tentukan_status(b["jumlah_kasus"]),
            )
            for b in baris_data
        ]
    )
    db.commit()

    jumlah_merah = sum(1 for b in baris_data if tentukan_status(b["jumlah_kasus"]) == "merah")
    return UploadResponse(
        project_id=project.id,
        nama_file=nama_file,
        jumlah_titik=len(baris_data),
        total_kasus=sum(b["jumlah_kasus"] for b in baris_data),
        jumlah_merah=jumlah_merah,
        jumlah_hijau=len(baris_data) - jumlah_merah,
        ambang_merah=AMBANG_MERAH_DEFAULT,
    )


@router.get("/{project_id}/data", response_model=List[CaseResponse])
def get_project_data(project_id: int, db: Session = Depends(get_db)):
    """Data titik untuk peta publik. Masih placeholder, diisi saat mengerjakan sisi masyarakat."""
    return []