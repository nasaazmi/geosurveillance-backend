from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, owner, project, beranda, peta, profil
from app.services.avatar import UPLOAD_DIR
app = FastAPI(
    title="GeoSurveillance API",
    description="Backend untuk dashboard persebaran penyakit & bencana (plotting map)",
    version="0.1.0",
)

app.include_router(profil.router, prefix="/owner/profile", tags=["Profil"])

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # nanti ganti ke domain frontend yang spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan semua router
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(owner.router, prefix="/owner", tags=["Owner"])
app.include_router(project.router, prefix="/project", tags=["Project"])
app.include_router(beranda.router, prefix="/beranda", tags=["Beranda Publik"])
app.include_router(peta.router, prefix="/peta", tags=["Peta Publik"])


@app.get("/")
def root():
    return {"message": "GeoSurveillance API is running"}
