from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import KategoriProject, StatusProject

class ProjectCreate(BaseModel):
    """Profil Proyek."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nama: str = Field(min_length=1, max_length=150)
    deskripsi: str | None = None


class ProjectLokasi(BaseModel):
    """Design Lokasi."""

    model_config = ConfigDict(str_strip_whitespace=True)

    kategori: KategoriProject  # "penyakit" atau "bencana"
    provinsi: str = Field(min_length=1)
    kabupaten: str = Field(min_length=1)
    jenis: str | None = Field(default=None, max_length=50)  # bebas, opsional. Contoh: "DBD", "Cacar Monyet"
    latitude: float = Field(ge=-90, le=90)     # titik pusat hasil klik di peta
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(gt=0, le=500)     # radius perimeter siaga

    @field_validator("jenis")
    @classmethod
    def rapikan_jenis(cls, v):
        """Rapikan spasi berlebih. Teks kosong dianggap tidak diisi."""
        if v is None:
            return None
        return " ".join(v.split()) or None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama: str
    deskripsi: str | None
    kategori: KategoriProject | None
    provinsi: str | None
    kabupaten: str | None
    latitude: float | None
    longitude: float | None
    radius_km: float | None
    status: StatusProject
    created_at: datetime


class DashboardResponse(BaseModel):
    username: str | None
    total_project: int
    projects: list[ProjectResponse]

class ResumeLokasi(BaseModel):
    kategori: KategoriProject | None
    provinsi: str | None
    kabupaten: str | None
    latitude: float | None
    longitude: float | None
    radius_km: float | None
    lengkap: bool


class ResumeFile(BaseModel):
    nama_file: str | None
    diperbarui_pada: datetime | None
    jumlah_titik: int
    total_kasus: int
    jumlah_merah: int
    jumlah_hijau: int
    ambang_merah: int


class ResumeResponse(BaseModel):
    """Halaman Resume (langkah terakhir wizard) sebelum project diterbitkan."""

    id: int
    nama: str
    deskripsi: str | None
    status: StatusProject
    lokasi: ResumeLokasi
    file: ResumeFile
    siap_terbit: bool
    belum_lengkap: list[str]  # alasan belum bisa terbit (kosong kalau siap)