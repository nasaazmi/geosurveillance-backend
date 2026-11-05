import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

BASE_DIR = Path(__file__).resolve().parents[2]  # folder backend
UPLOAD_DIR = BASE_DIR / "uploads"
AVATAR_DIR = UPLOAD_DIR / "avatars"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB


def _deteksi_ekstensi(data: bytes) -> str | None:
    """Tentukan jenis gambar dari isi file (bukan dari nama file), supaya tidak bisa dipalsukan."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def simpan_avatar(user_id: int, file: UploadFile) -> str:
    """Validasi dan simpan foto. Mengembalikan path relatif, contoh: avatars/3_ab12cd.png"""
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Ukuran foto maksimal 2 MB.")
    ekstensi = _deteksi_ekstensi(data)
    if ekstensi is None:
        raise HTTPException(415, "Format foto harus JPG, PNG, atau WEBP.")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    nama_file = f"{user_id}_{uuid.uuid4().hex[:12]}{ekstensi}"
    (AVATAR_DIR / nama_file).write_bytes(data)
    return f"avatars/{nama_file}"


def hapus_file_avatar(path_relatif: str | None) -> None:
    """Hapus file foto lama. Hanya file di dalam folder uploads yang boleh dihapus."""
    if not path_relatif:
        return
    target = (UPLOAD_DIR / path_relatif).resolve()
    if UPLOAD_DIR.resolve() in target.parents and target.is_file():
        target.unlink(missing_ok=True)


def url_avatar(path_relatif: str | None) -> str | None:
    return f"/uploads/{path_relatif}" if path_relatif else None