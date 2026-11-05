from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.profil import GantiPassword, ProfilResponse, ProfilUpdate
from app.services.avatar import hapus_file_avatar, simpan_avatar, url_avatar

router = APIRouter()


def _respons(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "bio": user.bio,
        "avatar_url": url_avatar(user.avatar_path),
        "created_at": user.created_at,
    }


@router.get("", response_model=ProfilResponse)
def get_profil(user: User = Depends(get_current_user)):
    """Halaman Akun: data profil milik user yang sedang login."""
    return _respons(user)


@router.put("", response_model=ProfilResponse)
def update_profil(
    data: ProfilUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simpan Perubahan: ubah username, email, no. telp, dan bio. Yang tidak dikirim tidak berubah."""
    dikirim = data.model_dump(exclude_unset=True)

    if dikirim.get("email") and dikirim["email"] != user.email:
        dipakai = db.query(User).filter(User.email == dikirim["email"], User.id != user.id).first()
        if dipakai:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email sudah dipakai akun lain.")
        user.email = dikirim["email"]

    if dikirim.get("username"):
        user.username = dikirim["username"]
    if "phone" in dikirim:
        user.phone = dikirim["phone"]
    if "bio" in dikirim:
        user.bio = dikirim["bio"]

    db.commit()
    db.refresh(user)
    return _respons(user)


@router.post("/avatar", response_model=ProfilResponse)
def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ganti foto profil (ikon pensil di foto). JPG, PNG, atau WEBP, maksimal 2 MB."""
    path_baru = simpan_avatar(user.id, file)
    path_lama = user.avatar_path
    user.avatar_path = path_baru
    db.commit()
    hapus_file_avatar(path_lama)
    db.refresh(user)
    return _respons(user)


@router.delete("/avatar", response_model=ProfilResponse)
def hapus_avatar(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hapus foto profil."""
    path_lama = user.avatar_path
    user.avatar_path = None
    db.commit()
    hapus_file_avatar(path_lama)
    db.refresh(user)
    return _respons(user)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def ganti_password(
    data: GantiPassword,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ganti Password: password lama harus benar, password baru minimal 8 karakter."""
    if not verify_password(data.password_lama, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password lama salah.")
    if data.password_baru == data.password_lama:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password baru tidak boleh sama dengan password lama.")
    user.hashed_password = hash_password(data.password_baru)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)