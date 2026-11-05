import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ProfilResponse(BaseModel):
    id: int
    username: str | None
    email: str
    phone: str | None
    bio: str | None
    avatar_url: str | None  # contoh: /uploads/avatars/3_ab12cd.png (awali dengan alamat server)
    created_at: datetime | None


class ProfilUpdate(BaseModel):
    """Isi hanya field yang mau diubah. Kirim phone atau bio kosong untuk menghapusnya."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    phone: str | None = None
    bio: str | None = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def cek_phone(cls, v):
        if not v:
            return None
        bersih = re.sub(r"[\s\-]", "", v)
        if not re.fullmatch(r"\+?[0-9]{8,15}", bersih):
            raise ValueError("Nomor telepon tidak valid (8-15 angka, boleh diawali +).")
        return bersih

    @field_validator("bio")
    @classmethod
    def cek_bio(cls, v):
        return v or None


class GantiPassword(BaseModel):
    password_lama: str
    password_baru: str = Field(min_length=8, max_length=72)