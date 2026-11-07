import math

LABEL_TINGKAT = {"rendah": "Rendah", "tinggi": "Tinggi"}


def tingkat_titik(level_status: str, jumlah_kasus: int | None = None) -> str:
    """jumlah_kasus tidak dipakai lagi, dibiarkan supaya pemanggilnya tidak perlu diubah."""
    return "tinggi" if level_status == "merah" else "rendah"


def satuan_kasus(kategori: str) -> str:
    """Penyakit dihitung 'kasus', bencana dihitung 'kejadian'."""
    return "kejadian" if kategori == "bencana" else "kasus"


def label_kategori(kategori: str | None, jenis: str | None) -> str | None:
    """Teks kolom 'Kategori' di tabel, contoh: 'Penyakit (DBD)'."""
    if not kategori:
        return None
    return f"{kategori.capitalize()} ({jenis})" if jenis else kategori.capitalize()


def jarak_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak dua koordinat dalam km (rumus haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Teks rekomendasi bawaan (placeholder). Ganti dengan teks dari klien kalau sudah ada.
_TEMPLATE = {
    ("penyakit", "tinggi"): (
        "Waspada tinggi di {wilayah} ({kasus} kasus). Segera lakukan pencegahan di lingkungan tempat tinggal Anda.",
        [
            "Jaga kebersihan lingkungan dan hindari genangan air atau tempat berkembangnya vektor penyakit.",
            "Jika mengalami gejala lebih dari 2 hari, segera periksakan diri ke fasilitas kesehatan terdekat.",
        ],
    ),
    ("penyakit", "rendah"): (
        "{wilayah} relatif terkendali ({kasus} kasus). Tetap jaga kebersihan lingkungan.",
        ["Lanjutkan pola hidup bersih dan sehat."],
    ),
    ("bencana", "tinggi"): (
        "Waspada tinggi di {wilayah} ({kasus} kejadian). Ikuti arahan BPBD dan siapkan langkah evakuasi.",
        [
            "Siapkan tas siaga bencana dan dokumen penting.",
            "Pantau informasi resmi BPBD/BMKG dan hindari area berisiko.",
        ],
    ),
    ("bencana", "rendah"): (
        "{wilayah} relatif aman ({kasus} kejadian). Tetap waspada terhadap perubahan cuaca.",
        ["Ikuti informasi resmi secara berkala."],
    ),
}


def teks_template(kategori: str, tingkat: str, wilayah: str, jumlah_kasus: int, asal: str | None = None, jarak: float | None = None):
    """Susun (peringatan, daftar tindakan). Kalau titik hasil penyebaran, peringatan menyebut titik asalnya."""
    peringatan, tindakan = _TEMPLATE[(kategori, tingkat)]
    if asal is not None and jarak is not None:
        teks = f"{wilayah} berada {jarak:.1f} km dari {asal} yang berstatus Tinggi. Waspada penyebaran ke wilayah ini."
    else:
        teks = peringatan.format(wilayah=wilayah, kasus=jumlah_kasus)
    return teks, list(tindakan)


def buat_rekomendasi(kategori: str, tingkat: str, wilayah: str, jumlah_kasus: int, kustom: str | None) -> dict:
    """Pakai teks yang tersimpan di kolom cases.rekomendasi kalau ada, kalau tidak pakai template."""
    if kustom:
        return {"sumber": "kustom", "peringatan": kustom, "tindakan": []}
    peringatan, tindakan = teks_template(kategori, tingkat, wilayah, jumlah_kasus)
    return {"sumber": "template", "peringatan": peringatan, "tindakan": tindakan}