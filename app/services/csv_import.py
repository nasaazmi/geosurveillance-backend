import csv
import io

KOLOM_WAJIB = ["wilayah", "latitude", "longitude", "jumlah_kasus"]
MAKS_BARIS = 10_000
MAKS_KASUS_PER_TITIK = 1_000_000_000
MAKS_KESALAHAN_DITAMPILKAN = 20

AMBANG_MERAH_DEFAULT = 10


class CsvTidakValid(Exception):
    def __init__(self, pesan: str, kesalahan: list[str] | None = None, total_kesalahan: int = 0):
        super().__init__(pesan)
        self.pesan = pesan
        self.kesalahan = kesalahan or []
        self.total_kesalahan = total_kesalahan


def tentukan_status(jumlah_kasus: int, ambang_merah: int = AMBANG_MERAH_DEFAULT) -> str:
    return "merah" if jumlah_kasus >= ambang_merah else "hijau"


def _ke_desimal(teks: str) -> float:
    return float(teks.strip().replace(",", "."))


def _ke_bilangan_bulat(teks: str) -> int:
    nilai = _ke_desimal(teks)
    if nilai != int(nilai):
        raise ValueError("bukan bilangan bulat")
    return int(nilai)


def baca_csv_kasus(isi: bytes) -> list[dict]:
    try:
        teks = isi.decode("utf-8-sig")  # utf-8-sig membuang BOM bawaan Excel
    except UnicodeDecodeError:
        raise CsvTidakValid("File harus berformat UTF-8. Simpan ulang dari Excel sebagai 'CSV UTF-8'.")

    if not teks.strip():
        raise CsvTidakValid("File kosong.")

    baris_header = teks.strip().splitlines()[0]
    pemisah = ";" if baris_header.count(";") > baris_header.count(",") else ","

    pembaca = csv.DictReader(io.StringIO(teks), delimiter=pemisah)
    kolom = [(k or "").strip().lower() for k in (pembaca.fieldnames or [])]
    pembaca.fieldnames = kolom

    hilang = [k for k in KOLOM_WAJIB if k not in kolom]
    if hilang:
        raise CsvTidakValid(
            f"Kolom wajib tidak ditemukan: {', '.join(hilang)}. "
            f"Kolom yang terbaca: {', '.join(kolom)}. "
            f"Kolom yang dibutuhkan: {', '.join(KOLOM_WAJIB)}."
        )

    hasil: list[dict] = []
    kesalahan: list[str] = []

    for nomor, baris in enumerate(pembaca, start=2):  # baris 1 = header
        if nomor - 1 > MAKS_BARIS:
            raise CsvTidakValid(f"Maksimal {MAKS_BARIS} baris data per file.")

        nilai_baris = [v for k, v in baris.items() if k is not None]
        if all((v or "").strip() == "" for v in nilai_baris) and not baris.get(None):
            continue  # baris kosong (sering ada sisa di akhir file Excel)

        galat: list[str] = []

        if baris.get(None):
            galat.append("jumlah kolom lebih banyak dari header")

        wilayah = (baris.get("wilayah") or "").strip()
        if not wilayah:
            galat.append("wilayah kosong")

        latitude = longitude = None
        try:
            latitude = _ke_desimal(baris.get("latitude") or "")
            if not -90 <= latitude <= 90:
                galat.append("latitude harus antara -90 dan 90")
        except ValueError:
            galat.append("latitude kosong atau bukan angka")

        try:
            longitude = _ke_desimal(baris.get("longitude") or "")
            if not -180 <= longitude <= 180:
                galat.append("longitude harus antara -180 dan 180")
        except ValueError:
            galat.append("longitude kosong atau bukan angka")

        jumlah_kasus = None
        try:
            jumlah_kasus = _ke_bilangan_bulat(baris.get("jumlah_kasus") or "")
            if jumlah_kasus < 0:
                galat.append("jumlah_kasus tidak boleh negatif")
            elif jumlah_kasus > MAKS_KASUS_PER_TITIK:
                galat.append("jumlah_kasus terlalu besar")
        except (ValueError, OverflowError):
            galat.append("jumlah_kasus kosong atau bukan bilangan bulat")

        if galat:
            kesalahan.append(f"Baris {nomor}: " + ", ".join(galat))
        else:
            hasil.append(
                {
                    "wilayah": wilayah,
                    "latitude": latitude,
                    "longitude": longitude,
                    "jumlah_kasus": jumlah_kasus,
                }
            )

    if kesalahan:
        raise CsvTidakValid(
            "Ada baris yang tidak valid. Tidak ada data yang disimpan.",
            kesalahan[:MAKS_KESALAHAN_DITAMPILKAN],
            len(kesalahan),
        )
    if not hasil:
        raise CsvTidakValid("Tidak ada baris data di dalam file (hanya header).")
    return hasil