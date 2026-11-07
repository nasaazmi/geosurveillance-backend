from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProsesResponse(BaseModel):
    jarak_km: float
    jumlah_titik: int
    merah_asli: int
    merah_hasil_penyebaran: int
    hijau: int
    titik_direkomendasi: int
    dilewati_manual: int


class RekomendasiInput(BaseModel):
    """Isi rekomendasi satu titik secara manual. Menggantikan semua butir yang ada."""

    model_config = ConfigDict(str_strip_whitespace=True)

    peringatan: str | None = Field(default=None, max_length=500)
    tindakan: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("tindakan")
    @classmethod
    def rapikan_tindakan(cls, v):
        hasil = [t.strip() for t in v if t and t.strip()]
        if any(len(t) > 500 for t in hasil):
            raise ValueError("Setiap tindakan maksimal 500 karakter.")
        return hasil

    @model_validator(mode="after")
    def minimal_satu(self):
        self.peringatan = self.peringatan or None
        if not self.peringatan and not self.tindakan:
            raise ValueError("Isi peringatan atau minimal satu tindakan.")
        return self


class RekomendasiOwnerResponse(BaseModel):
    case_id: int
    wilayah: str
    sumber: str  # manual | otomatis | kustom | template
    peringatan: str | None
    tindakan: list[str]