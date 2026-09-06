import re
from nltk.tokenize import sent_tokenize
from config import MAX_SENTENCES


# Daftar lokasi umum untuk mendeteksi dateline berita di awal teks.
# Dibuat eksplisit agar tidak terlalu rakus menghapus isi artikel.
DATELINE_LOCATIONS = (
    "Jakarta|Bandung|Surabaya|Denpasar|Yogyakarta|Jogja|Semarang|Makassar|Medan|"
    "Palembang|Bogor|Bekasi|Depok|Tangerang|Solo|Malang|Bali|Kupang|Jayapura|"
    "Aceh|Pekanbaru|Mataram|Pontianak|Banjarmasin|Manado|Ambon|Jambi|Padang|"
    "Samarinda|Balikpapan|Kendari|Palu|Serang|Cirebon|Batam|Mojokerto|"
    "Gianyar|Tabanan|Badung|Singaraja|Karangasem|Klungkung|Bangli|Jembrana"
)

MEDIA_NAMES = (
    "kompas|liputan6|tempo|detik|cnnindonesia|cnn indonesia|tribunnews|tribun|"
    "republika|antara|okezone|merdeka|kumparan|suara|viva|metrotvnews|idntimes"
)


def remove_news_source_and_dateline(text: str) -> str:
    """Membersihkan sumber media dan dateline di awal baris/artikel.

    Contoh yang ditangani:
    - Kompas.com, Jakarta - Pemerintah ...
    - Liputan6.com, Jakarta - Pemerintah ...
    - TEMPO.CO, Jakarta - Pemerintah ...
    - Com, Jakarta-Pemerintah ...   # sisa domain dari cleaning sebelumnya
    - Jakarta - Pemerintah ...
    - Jakarta-Pemerintah ...
    """

    # 1) Hapus sumber media lengkap: "Kompas.com, Jakarta -", "TEMPO.CO, Jakarta -", dst.
    text = re.sub(
        rf"(?im)^\s*(?:{MEDIA_NAMES})(?:\.(?:com|co|id|net))?\s*,?\s*"
        rf"(?:{DATELINE_LOCATIONS})?\s*(?:,\s*\d{{1,2}}\s+\w+\s+\d{{4}})?\s*[-–—:]\s*",
        "",
        text,
    )

    # 2) Hapus sisa domain yang sering tertinggal: "Com, Jakarta-", "Co, Jakarta -".
    text = re.sub(
        rf"(?im)^\s*(?:com|co|id|net)\s*,\s*(?:{DATELINE_LOCATIONS})\s*"
        rf"(?:,\s*\d{{1,2}}\s+\w+\s+\d{{4}})?\s*[-–—:]\s*",
        "",
        text,
    )

    # 3) Hapus dateline tanpa sumber media: "Jakarta -", "Jakarta-", "Jakarta, 13 April 2025 -".
    text = re.sub(
        rf"(?im)^\s*(?:{DATELINE_LOCATIONS})\s*"
        rf"(?:,\s*\d{{1,2}}\s+\w+\s+\d{{4}})?\s*[-–—:]\s*",
        "",
        text,
    )

    return text


def preprocess_input(text: str) -> str:
    # Hapus tag HTML
    text = re.sub(r'<[^>]+>', ' ', text)

    # Hapus URL (http/https/www)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Hapus sumber media/dateline sebelum tanda baca dibersihkan
    text = remove_news_source_and_dateline(text)

    # Hapus emoji & simbol unicode non-latin
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u2018\u2019\u201C\u201D]', ' ', text)

    # Hapus sisa karakter aneh selain alfanumerik, tanda baca lazim, spasi
    text = re.sub(r'[^\w\s.,!?()\-:;\'\"]', ' ', text)

    # Ulangi lagi setelah normalisasi karakter untuk menangkap sisa seperti "Com, Jakarta-"
    text = remove_news_source_and_dateline(text)

    # Hapus pola navigasi artikel. Dibuat per baris agar tidak menghapus seluruh artikel jika teks satu baris panjang.
    text = re.sub(
        r'(?im)^\s*(baca\s+juga|lihat\s+juga|artikel\s+terkait|simak\s+juga)\s*:?.*$',
        '',
        text,
    )

    # Hapus kalimat caption foto: "Foto:", "Gambar:", "(Foto/...", "[Foto: ...]"
    text = re.sub(
        r'(?i)(\[.*?(foto|gambar|ilustrasi).*?\]|\(.*?(foto|gambar|ilustrasi).*?\)|foto\s*:.*|gambar\s*:.*)',
        '',
        text,
    )

    # Hapus baris sangat pendek (< 4 kata) yang kemungkinan header/label
    lines = text.splitlines()
    lines = [l for l in lines if len(l.split()) >= 4]
    text = '\n'.join(lines)

    # Normalisasi spasi dan tanda hubung yang menempel
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

    return text.strip()


def split_paragraphs(text: str) -> list:
    if not text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def get_limited_sentences(text: str, limit: int = MAX_SENTENCES) -> list:
    paragraphs = split_paragraphs(text)

    sentences = []
    for paragraph in paragraphs:
        sentences.extend(sent_tokenize(paragraph))

    return sentences[:limit]
