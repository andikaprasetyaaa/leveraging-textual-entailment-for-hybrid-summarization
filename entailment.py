# ========================================================================
# ENTAILMENT — IndoBERT RTE Filtering & Premise Extraction (3 Strategi)
# ========================================================================

import torch
from nltk.tokenize import sent_tokenize
from config import device
from models import ent_tok, ent_mdl


# ========================================================================
# CORE: CHECK ENTAILMENT
# ========================================================================

def check_entailment(premise: str, hypothesis: str) -> tuple:
    """Mengembalikan (is_entailment: bool, confidence: float)"""
    inputs = ent_tok(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = ent_mdl(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1)

    entailment_score = probs[0][0].item()
    predicted_label = torch.argmax(logits, dim=-1).item()
    return (predicted_label == 0), entailment_score


# ========================================================================
# PREMISE EXTRACTION — 3 STRATEGI
# ========================================================================

def extract_first_sentence(text: str) -> str:
    """Strategi 1: Kalimat pertama paragraf pertama."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        raise ValueError("Teks kosong, tidak ada paragraf.")
    sentences = sent_tokenize(paragraphs[0])
    if not sentences:
        raise ValueError("Tidak ada kalimat di paragraf pertama.")
    return sentences[0]


def extract_last_sentence(text: str) -> str:
    """Strategi 2: Kalimat terakhir dokumen."""
    sentences = sent_tokenize(text)
    if not sentences:
        raise ValueError("Tidak ada kalimat dalam teks.")
    return sentences[-1]


def extract_highlight_sentence(text: str) -> str:
    """
    Strategi 3: Kalimat paling 'sentral' (highlight).
    Kalimat dengan rata-rata confidence entailment tertinggi terhadap
    semua kalimat lain. Dibatasi 15 kalimat pertama.
    """
    sentences = sent_tokenize(text)
    if not sentences:
        raise ValueError("Tidak ada kalimat dalam teks.")
    if len(sentences) == 1:
        return sentences[0]

    candidates = sentences[:15]
    best_idx = 0
    best_avg = -1.0

    for i, candidate in enumerate(candidates):
        scores = []
        for j, other in enumerate(candidates):
            if i == j:
                continue
            _, score = check_entailment(candidate, other)
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        if avg_score > best_avg:
            best_avg = avg_score
            best_idx = i

    return candidates[best_idx]