import re
from difflib import SequenceMatcher
from nltk.tokenize import sent_tokenize, word_tokenize


# ========================================================================
# BASIC CLEANING
# ========================================================================

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    return text.strip()


def remove_repetition(text: str) -> str:
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() == words[i - 1].lower():
            continue
        result.append(w)
    return " ".join(result)


# ========================================================================
# CONTEXT-AWARE NUMBER HANDLING
# ========================================================================

def is_valid_number_usage(sentence: str) -> bool:
    words = sentence.split()
    for i, w in enumerate(words):
        if re.match(r'^\d+[.,]?\d*$', w):
            if i != 0:
                return True
        if i > 0 and words[i - 1].lower() in ['pasal', 'bab', 'ayat', 'no', 'nomor']:
            return True
    return False


def clean_numbering(sentence: str) -> str:
    words = sentence.split()
    if not words:
        return sentence
    first = words[0]
    if re.match(r'^\d+\.$', first):
        return " ".join(words[1:])
    if first.isdigit() and not is_valid_number_usage(sentence):
        return " ".join(words[1:])
    return sentence


# ========================================================================
# MAIN T5 OUTPUT CLEANER  (diperbaiki sesuai notebook)
# ========================================================================

def clean_t5_output(text: str) -> str:
    # 1. Hapus quote artifacts
    text = text.replace("``", "").replace("''", "")

    # 2. Hapus kata awalan model yang bocor (summarize / paraphrase)
    #    [FIX] tambah "paraphrase" — prefix yang dipakai IndoT5-base-paraphrase
    text = re.sub(r'(?i)\b(summarize|paraphrase)\s*:?\s*', '', text)

    # 3. Karakter yang diizinkan diperluas:
    #    [FIX] tambah / () % & agar tanggal (12/05), singkatan (Rp.), dan
    #          persentase (7%) tidak ikut terhapus
    text = re.sub(r'[^\w\s.,:;!?\-\'\"\(\)/%&]', '', text)

    # 4. Normalisasi huruf kapital semua-besar
    #    [FIX] baru — cegah output seperti "PEMERINTAH" atau "KLUB"
    def normalize_caps(m):
        word = m.group(0)
        return word.capitalize() if len(word) > 4 else word
    text = re.sub(r'\b[A-Z]{5,}\b', normalize_caps, text)

    # 5. Hapus duplikasi frasa output (window 4 → 2 kata)
    words = text.split()
    result = []
    seen = set()
    i = 0
    while i < len(words):
        added = False
        for size in range(4, 1, -1):
            if i + size <= len(words):
                phrase = " ".join(words[i: i + size]).lower()
                if phrase in seen:
                    i += size
                    added = True
                    break
                else:
                    seen.add(phrase)
        if not added:
            result.append(words[i])
            i += 1
    text = " ".join(result)

    # 6. Fix tanda baca bertabrakan
    #    [FIX] baru — tangani ., dan ,. yang sering muncul di output T5
    text = re.sub(r'\.\s*,', ',', text)
    text = re.sub(r',\s*\.', '.', text)

    # 7. Fix spasi hilang antar kalimat
    #    [FIX] baru — "memilikinya.Pengalaman" → "memilikinya. Pengalaman"
    text = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', text)

    # 8. Hapus kalimat menggantung di akhir
    #    [FIX] baru — buang "Berikut:" / "sebagai berikut:" tanpa penutup
    text = re.sub(
        r'[^.]*\b(berikut|sebagai berikut|adalah)\s*:\s*$',
        '.',
        text,
        flags=re.IGNORECASE,
    )

    # 9. Rapikan tanda baca ganda & spasi berlebih
    text = re.sub(r'([,!?])\1+', r'\1', text)
    text = re.sub(r'\.{2,3}(?!\.)', '.', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# ========================================================================
# SENTENCE FILTER  (baru — dari notebook, belum ada di main6.py)
# ========================================================================

def filter_sentences(text: str) -> str:
    """
    Menyaring kalimat terlalu pendek atau penuh pengulangan dari output T5.
    Dipanggil sesudah clean_t5_output(), sebelum remove_similar_sentences().
    """
    sentences = sent_tokenize(text)
    clean_sentences = []

    for s in sentences:
        s = clean_numbering(s)
        words = word_tokenize(s)

        if not words:
            continue

        # Buang kalimat < 5 kata — biasanya fragmen/potongan
        if len(words) < 5:
            continue

        # Buang jika kalimat dimulai angka tanpa konteks yang valid
        if words[0].isdigit() and not is_valid_number_usage(s):
            continue

        # Buang jika rasio kata unik terlalu rendah (banyak pengulangan)
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.45:
            continue

        clean_sentences.append(s)

    # Fallback: jika semua kalimat terbuang, kembalikan teks asli
    return " ".join(clean_sentences) if clean_sentences else text


# ========================================================================
# REMOVE SIMILAR SENTENCES
# ========================================================================

def remove_similar_sentences(text: str) -> str:
    sentences = sent_tokenize(text)
    unique = []
    for s in sentences:
        if not any(s.lower() in u.lower() or u.lower() in s.lower() for u in unique):
            unique.append(s)
    return " ".join(unique)


# ========================================================================
# SMART SENTENCE SPLIT
# ========================================================================

def smart_sentence_split(text: str) -> str:
    sentences = sent_tokenize(text)
    final = []
    for s in sentences:
        s = s.strip().rstrip(',;:').strip()
        if not s:
            continue
        s = s[0].upper() + s[1:]
        if not s.endswith(('.', '!', '?')):
            s += '.'
        final.append(s)
    result = ' '.join(final)
    result = remove_repetition(result)
    return result


# ========================================================================
# PROPER NOUN PROTECTION  (diperbaiki sesuai notebook)
# ========================================================================

def protect_proper_nouns(text: str) -> tuple:
    entities = {}
    pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)\b'

    def replacer(m):
        idx = len(entities)
        key = f"ENT{idx}"
        entities[key] = m.group(0)
        return key

    protected_text = re.sub(pattern, replacer, text)
    return protected_text, entities


def restore_proper_nouns(text: str, entities: dict) -> str:
    # 1. Kembalikan placeholder ENT/ENS ke nama asli
    #    Menangani ENT1, E N T 1, dan typo generatif seperti ENS1
    for key, original in entities.items():
        num_part = key.replace("ENT", "")
        pattern = r'E\s*N\s*[TS]\s*' + num_part + r'(?!\d)'
        text = re.sub(pattern, original, text, flags=re.IGNORECASE)

    # 2. Bersihkan sisa placeholder ENT/ENS halusinasi
    text = re.sub(r'E\s*N\s*[TS]\s*\d+(?!\d)', '', text, flags=re.IGNORECASE)

    # 3. Penyapu spasi aneh & nama dempet
    # a. Spasi nyangkut sebelum tanda baca
    text = re.sub(r'\s+([.,:;!?%])', r'\1', text)

    # b. Fix nama dempet dengan pengecualian eKTP / iPhone / McDonald
    text = re.sub(r'(?<!\be)(?<!\bi)(?<!\bMc)([a-z])([A-Z])', r'\1 \2', text)

    # c. Spasi nyangkut di dalam kurung atau tanda hubung
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r'\s*-\s*', '-', text)

    # d. Angka desimal yang terpecah, contoh 12 . 7 → 12.7
    text = re.sub(r'(\d)\s*([.,])\s*(\d)', r'\1\2\3', text)

    # 4. Rapikan spasi ganda
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# ========================================================================
# HALLUCINATION FILTER
# ========================================================================

def is_relevant(sentence: str, source_sents: list, threshold: float = 0.35) -> bool:
    return any(
        SequenceMatcher(None, sentence.lower(), src.lower()).ratio() >= threshold
        for src in source_sents
    )


def filter_hallucination(summary: str, source: str) -> str:
    source_sents = sent_tokenize(source)
    summary_sents = sent_tokenize(summary)
    filtered = [s for s in summary_sents if is_relevant(s, source_sents)]
    return " ".join(filtered) if filtered else summary


# ========================================================================
# FINAL SENTENCE FIX
# ========================================================================

def fix_sentences(text: str) -> str:
    text = clean_text(text)
    sentences = sent_tokenize(text)
    fixed = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        if not s.endswith(('.', '!', '?')):
            s += '.'
        fixed.append(s)
    return " ".join(fixed)