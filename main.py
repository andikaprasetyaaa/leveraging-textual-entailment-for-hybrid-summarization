# ========================================================================
# FASTAPI APP — HYBRID ABSTRACTIVE SUMMARIZATION
# Pipeline:
#   1. Premise Selection (3 strategi: first / last / highlight)
#   2. Entailment Filtering (IndoBERT) + confidence score
#   3. Concatenation: premise + entailed sentences
#   4. Abstractive Rewrite (IndoT5) + full post-processing pipeline
#
# CHANGELOG v3.1.0:
#   [FIX] math.floor → math.ceil pada compression_ratio
#         Sebelumnya: floor(3 * 0.25) = 0 → max(1,0) = 1 (sama untuk 25% & 50%)
#         Sesudahnya: ceil(3 * 0.25) = 1, ceil(3 * 0.5) = 2 (berbeda)
#   [FIX] MAX_INPUT_CHARS di rewrite_with_t5 dibuat dinamis
#         Sebelumnya: selalu dipotong 800 char → input T5 sama walau ratio beda
#         Sesudahnya: menyesuaikan panjang teks actual, max 1500 char
#   [FIX] entailment_details tidak di-reset ketika fallback aktif
#         Sebelumnya: bisa duplikat antara entailed_with_score & fallback
#         Sesudahnya: fallback selalu rebuild entailment_details dari nol
#   [FIX] Prefix T5 diubah "summarize: " → "paraphrase: " (lihat summarizer.py)
#   [NEW] filter_sentences() masuk pipeline post-processing (lihat postprocessing.py)
#   [NEW] clean_t5_output & restore_proper_nouns diperbaiki (lihat postprocessing.py)
# ========================================================================

import math
import nltk
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import CREATIVITY_MAP
from schemas import TextRequest, EntailmentDetail, SummarizationResponse
from preprocessing import preprocess_input, get_limited_sentences
from entailment import (
    check_entailment,
    extract_first_sentence,
    extract_last_sentence,
    extract_highlight_sentence,
)
from summarizer import rewrite_with_t5

# ========================================================================
# NLTK
# ========================================================================
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

# ========================================================================
# FASTAPI INIT
# ========================================================================
app = FastAPI(
    title="Hybrid Summarization API",
    description="Sistem Peringkasan Hybrid: IndoBERT RTE + IndoT5 Abstraktif (3 Strategi Premis)",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================================
# API ENDPOINT
# ========================================================================

@app.post("/summarize", response_model=SummarizationResponse)
def summarize_text(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input teks kosong.")
    req.text = preprocess_input(req.text)
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Teks kosong setelah preprocessing.")
    if req.min_length >= req.max_length:
        raise HTTPException(
            status_code=400,
            detail="Panjang minimal harus lebih kecil dari panjang maksimal.",
        )
    if req.creativity not in CREATIVITY_MAP:
        raise HTTPException(
            status_code=400,
            detail="Nilai creativity tidak valid. Gunakan: precise | balanced | creative",
        )

    try:
        # ── 1. Ekstraksi Premise sesuai strategi ────────────────
        strategy = req.premise_strategy or "first"

        if strategy == "first":
            premise = extract_first_sentence(req.text)
        elif strategy == "last":
            premise = extract_last_sentence(req.text)
        elif strategy == "highlight":
            premise = extract_highlight_sentence(req.text)
        else:
            raise HTTPException(status_code=400, detail=f"Strategi tidak dikenal: {strategy}")

        # ── 2. Split kalimat ─────────────────────────────────────
        sentences = get_limited_sentences(req.text)
        total_sentences = len(sentences)

        # ── 3. RTE Filtering ─────────────────────────────────────
        entailed_with_score = []
        entailment_details_all = []

        for idx, hyp in enumerate(sentences):
            if hyp.strip() == premise.strip():
                continue
            is_ent, score = check_entailment(premise, hyp)
            if is_ent:
                entailed_with_score.append((score, hyp, idx + 1))
                entailment_details_all.append(
                    EntailmentDetail(position=idx + 1, text=hyp, confidence=round(score, 4))
                )

        # ── 4. Compression Ratio ─────────────────────────────────
        # FIX UTAMA: Ganti math.floor → math.ceil
        #
        # Masalah lama (floor):
        #   total=3, ratio=0.25 → floor(0.75)=0 → max(1,0)=1
        #   total=3, ratio=0.50 → floor(1.50)=1 → max(1,1)=1  ← SAMA!
        #
        # Setelah fix (ceil):
        #   total=3, ratio=0.25 → ceil(0.75)=1
        #   total=3, ratio=0.50 → ceil(1.50)=2  ← BEDA ✓
        #   total=3, ratio=0.75 → ceil(2.25)=3
        #   total=3, ratio=1.00 → ceil(3.00)=3

        ratio = req.compression_ratio if req.compression_ratio is not None else 1.0
        debug_total_entailed = len(entailed_with_score)

        if entailed_with_score:
            sorted_entailed = sorted(entailed_with_score, key=lambda x: x[0], reverse=True)

            # FIXED: ceil instead of floor
            k = max(1, math.ceil(len(sorted_entailed) * ratio))
            selected = sorted_entailed[:k]

            # Urutkan kembali sesuai posisi asli agar alur teks koheren
            selected_sorted_by_pos = sorted(selected, key=lambda x: x[2])
            entailed_texts = [s[1] for s in selected_sorted_by_pos]

            # Update entailment_details hanya untuk kalimat yang terpilih
            selected_positions = {s[2] for s in selected}
            entailment_details = [
                d for d in entailment_details_all if d.position in selected_positions
            ]
        else:
            entailed_texts = []
            entailment_details = []
            k = 0

        debug_k = k

        # FIX: Fallback rebuild entailment_details dari nol agar tidak duplikat
        if not entailed_texts:
            fallback = [s for s in sentences if s.strip() != premise.strip()][:3]
            entailed_texts = fallback
            entailment_details = [
                EntailmentDetail(position=i + 1, text=s, confidence=0.0)
                for i, s in enumerate(entailed_texts)
            ]
            debug_k = len(entailed_texts)

        # ── 5. Concatenation sesuai strategi ─────────────────────
        # - first / highlight: premise di depan
        # - last: premise di akhir
        if strategy == "last":
            concatenated_text = " ".join(entailed_texts) + " " + premise
        else:
            concatenated_text = " ".join([premise] + entailed_texts)

        # ── 6. Abstractive rewrite ───────────────────────────────
        final_summary = rewrite_with_t5(
            concatenated_text,
            min_len=req.min_length,
            max_len=req.max_length,
            creativity=req.creativity,
        )

        avg_conf = (
            sum(d.confidence for d in entailment_details) / len(entailment_details)
            if entailment_details else 0.0
        )

        return SummarizationResponse(
            premise=premise,
            premise_strategy=strategy,
            entailed_sentences=entailed_texts,
            entailment_details=entailment_details,
            summary=final_summary,
            entailed_count=len(entailed_texts),
            total_sentences=total_sentences,
            avg_confidence=round(avg_conf, 4),
            output_word_count=len(final_summary.split()),
            debug_k=debug_k,
            debug_total_entailed=debug_total_entailed,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# MAIN
# ========================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)