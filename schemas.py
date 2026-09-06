# ========================================================================
# SCHEMAS — Pydantic Request & Response Models
# ========================================================================

from pydantic import BaseModel, Field
from typing import Optional, Literal


class TextRequest(BaseModel):
    text: str
    min_length: Optional[int] = Field(30, ge=10, le=200, description="Panjang minimal ringkasan (token)")
    max_length: Optional[int] = Field(120, ge=30, le=400, description="Panjang maksimal ringkasan (token)")
    creativity: Optional[str] = Field(
        "balanced",
        description="Gaya bahasa: 'precise' | 'balanced' | 'creative'"
    )
    premise_strategy: Optional[Literal["first", "last", "highlight"]] = Field(
        "first",
        description="Strategi pemilihan kalimat premis: 'first' | 'last' | 'highlight'"
    )
    compression_ratio: Optional[float] = Field(
        1.0,
        ge=0.1,
        le=1.0,
        description="Rasio kompresi kalimat entailment yang digunakan (0.1–1.0)"
    )


class EntailmentDetail(BaseModel):
    position: int
    text: str
    confidence: float


class SummarizationResponse(BaseModel):
    premise: str
    premise_strategy: str
    entailed_sentences: list[str]
    entailment_details: list[EntailmentDetail]
    summary: str
    entailed_count: int
    total_sentences: int
    avg_confidence: float
    output_word_count: int
    # debug info untuk verifikasi ratio bekerja benar
    debug_k: int
    debug_total_entailed: int