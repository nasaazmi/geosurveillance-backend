from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_owned_project
from app.database import get_db
from app.models.case import Case
from app.models.project import Project, StatusProject
from app.models.user import User
from app.schemas.project import (
    DashboardResponse,
    ProjectCreate,
    ProjectLokasi,
    ProjectResponse,
)

router = APIRouter()


@router.post("/project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Profil Proyek: buat project baru dengan status draft."""
    project = Project(
        owner_id=current_user.id,
        nama=data.nama,
        deskripsi=data.deskripsi,
        status=StatusProject.draft.value,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/project/{project_id}/lokasi", response_model=ProjectResponse)
def set_lokasi(
    data: ProjectLokasi,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):
    """Design Lokasi: simpan kategori, wilayah, titik pusat, dan radius."""
    project.kategori = data.kategori
    project.provinsi = data.provinsi
    project.kabupaten = data.kabupaten
    project.latitude = data.latitude
    project.longitude = data.longitude
    project.radius_km = data.radius_km
    db.commit()
    db.refresh(project)
    return project


@router.get("/project/{project_id}", response_model=ProjectResponse)
def get_project(project: Project = Depends(get_owned_project)):
    """Ambil isi project milik sendiri (untuk melanjutkan draft atau halaman Resume)."""
    return project


@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
):

    if project.status != StatusProject.draft.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hanya project draft yang bisa dibatalkan",
        )
    db.query(Case).filter(Case.project_id == project.id).delete()
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return {
        "username": current_user.username,
        "total_project": len(projects),
        "projects": projects,
    }