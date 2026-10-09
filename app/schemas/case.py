from pydantic import BaseModel, ConfigDict


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wilayah: str
    provinsi: str
    latitude: float
    longitude: float
    jumlah_kasus: int
    level_status: str
    rekomendasi: str | None


class UploadResponse(BaseModel):
    project_id: int
    nama_file: str
    jumlah_titik: int
    total_kasus: int
    jumlah_merah: int
    jumlah_hijau: int
    ambang_merah: int