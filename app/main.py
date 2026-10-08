from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, owner, project, beranda

app = FastAPI(
    title="GeoSurveillance API",
    description="Backend untuk dashboard persebaran penyakit & bencana (plotting map)",
    version="0.1.0",
)

# CORS supaya frontend Next.js (beda origin) bisa akses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # nanti ganti ke domain frontend yang spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan semua router, masing-masing punya prefix & tag sendiri
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(owner.router, prefix="/owner", tags=["Owner"])
app.include_router(project.router, prefix="/project", tags=["Project"])
app.include_router(beranda.router, prefix="/beranda", tags=["Beranda Publik"])


@app.get("/")
def root():
    return {"message": "GeoSurveillance API is running"}
