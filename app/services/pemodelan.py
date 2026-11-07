import bisect

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.services.peta import jarak_km, teks_template, tingkat_titik

JARAK_BAWAAN_KM = 5.0   # sama dengan "Radius Waspada 5 KM" di desain
KM_PER_DERAJAT = 111.0  # 1 derajat lintang kira-kira 111 km


def hitung_penyebaran(kasus: list[Case], batas_km: float) -> int:
    """Titik hijau yang berada dalam batas_km dari titik merah asli ikut menjadi merah (hasil penyebaran).

    Tidak berantai: hanya titik merah asli yang boleh menjadi sumber. Aman dijalankan berulang,
    karena hasil lama dikembalikan dulu sebelum dihitung ulang. Mengembalikan jumlah titik hasil penyebaran.
    """
    for k in kasus:
        if k.is_propagated:
            k.level_status = "hijau"
            k.is_propagated = False
            k.source_case_id = None

    sumber = sorted((k for k in kasus if k.level_status == "merah"), key=lambda k: k.latitude)
    lintang = [s.latitude for s in sumber]
    selisih = batas_km / KM_PER_DERAJAT

    jumlah = 0
    for k in kasus:
        if k.level_status == "merah":
            continue
        # hanya periksa sumber yang lintangnya berdekatan, supaya tidak membandingkan semua pasangan
        kiri = bisect.bisect_left(lintang, k.latitude - selisih)
        kanan = bisect.bisect_right(lintang, k.latitude + selisih)
        terdekat, jarak_min = None, None
        for s in sumber[kiri:kanan]:
            j = jarak_km(k.latitude, k.longitude, s.latitude, s.longitude)
            if j <= batas_km and (jarak_min is None or j < jarak_min):
                terdekat, jarak_min = s, j
        if terdekat is not None:
            k.level_status = "merah"
            k.is_propagated = True
            k.source_case_id = terdekat.id
            jumlah += 1
    return jumlah


def buat_ulang_rekomendasi(db: Session, project: Project, kasus: list[Case]) -> tuple[int, int]:
    """Buat ulang rekomendasi otomatis tiap titik. Titik yang rekomendasinya sudah diisi manual dilewati.

    Mengembalikan (jumlah titik yang dibuatkan, jumlah titik yang dilewati).
    """
    kategori = project.kategori.value if project.kategori else "penyakit"
    id_kasus = select(Case.id).where(Case.project_id == project.id)

    manual = {
        cid
        for (cid,) in db.query(Recommendation.case_id)
        .filter(Recommendation.case_id.in_(id_kasus), Recommendation.sumber == "manual")
        .distinct()
        .all()
    }
    db.query(Recommendation).filter(
        Recommendation.case_id.in_(id_kasus), Recommendation.sumber == "otomatis"
    ).delete(synchronize_session=False)

    per_id = {k.id: k for k in kasus}
    baru, dilewati = [], 0
    for k in kasus:
        if k.id in manual:
            dilewati += 1
            continue
        asal = jarak = None
        if k.is_propagated and k.source_case_id in per_id:
            s = per_id[k.source_case_id]
            asal, jarak = s.wilayah, jarak_km(k.latitude, k.longitude, s.latitude, s.longitude)
        peringatan, tindakan = teks_template(
            kategori, tingkat_titik(k.level_status), k.wilayah, k.jumlah_kasus, asal, jarak
        )
        baru.append(Recommendation(case_id=k.id, tipe="peringatan", sumber="otomatis", recommendation_text=peringatan))
        baru.extend(
            Recommendation(case_id=k.id, tipe="tindakan", sumber="otomatis", recommendation_text=t) for t in tindakan
        )
    db.add_all(baru)
    return len(kasus) - dilewati, dilewati


def jalankan_pemodelan(db: Session, project: Project, batas_km: float) -> dict | None:
    """Jalankan seluruh proses untuk satu project. Mengembalikan None kalau belum ada data titik."""
    kasus = db.query(Case).filter(Case.project_id == project.id).order_by(Case.id).all()
    if not kasus:
        return None

    hasil_sebar = hitung_penyebaran(kasus, batas_km)
    db.flush()
    diproses, dilewati = buat_ulang_rekomendasi(db, project, kasus)
    db.commit()

    merah_total = sum(1 for k in kasus if k.level_status == "merah")
    return {
        "jarak_km": batas_km,
        "jumlah_titik": len(kasus),
        "merah_asli": merah_total - hasil_sebar,
        "merah_hasil_penyebaran": hasil_sebar,
        "hijau": len(kasus) - merah_total,
        "titik_direkomendasi": diproses,
        "dilewati_manual": dilewati,
    }