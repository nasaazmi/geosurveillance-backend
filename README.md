# GeoSurveillance API (skeleton)

Struktur awal backend FastAPI untuk proyek GeoSurveillance.

## Menjalankan
```
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Lalu buka http://localhost:8000/docs untuk lihat Swagger UI (dokumentasi endpoint otomatis).

## Struktur
- app/main.py       -> entry point, daftar semua router
- app/database.py    -> koneksi PostgreSQL
- app/models/        -> tabel database (SQLAlchemy)
- app/schemas/        -> bentuk request/response (Pydantic)
- app/routers/        -> definisi endpoint per fitur
- app/services/        -> logic berat (processing spasial, forecasting) - masih kosong

## Yang masih TODO
Semua fungsi endpoint baru kerangka (belum ada query database & auth beneran).
Cari komentar `# TODO` di tiap router untuk lihat apa yang perlu diisi.
