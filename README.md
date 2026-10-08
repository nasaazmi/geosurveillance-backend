# GeoSurveillance Backend

Backend API untuk dashboard persebaran penyakit dan bencana (FastAPI + PostgreSQL).

## Cara menjalankan

1. Buat dan aktifkan virtual environment:
   python -m venv .venv
   .venv\Scripts\activate

2. Install dependency:
   python -m pip install -r requirements.txt

3. Buat database PostgreSQL bernama `geosurveillance`.

4. Salin `.env.example` menjadi `.env`, lalu isi DATABASE_URL dan SECRET_KEY.

5. Jalankan migrasi:
   python -m alembic upgrade head

6. Jalankan server:
   python -m uvicorn app.main:app --reload

Dokumentasi API otomatis (Swagger): http://127.0.0.1:8000/docs

## Struktur

- app/routers/  : endpoint per fitur (auth, owner, project, beranda)
- app/models/   : tabel database (SQLAlchemy)
- app/schemas/  : bentuk request dan response (Pydantic)
- app/core/     : keamanan (hash password, JWT)
- alembic/      : file migrasi database
