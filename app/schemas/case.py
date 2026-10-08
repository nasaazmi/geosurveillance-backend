from pydantic import BaseModel


class CaseResponse(BaseModel):
    id: int
    wilayah: str
    provinsi: str
    latitude: float
    longitude: float
    jumlah_kasus: int
    level_status: str
    rekomendasi: str | None

    class Config:
        from_attributes = True
