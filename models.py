# ========================================================================
# MODELS — Load IndoBERT Entailment & IndoT5 Abstractive
# ========================================================================

import os
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    BertForSequenceClassification,
)
from config import CHECKPOINT_ENT_PATH, T5_MODEL_NAME, device

print("[INFO] Loading IndoBERT Entailment Model...")
if not os.path.exists(CHECKPOINT_ENT_PATH):
    raise RuntimeError(f"Model path not found: {CHECKPOINT_ENT_PATH}")

ent_tok = AutoTokenizer.from_pretrained(CHECKPOINT_ENT_PATH, trust_remote_code=True)
ent_mdl = BertForSequenceClassification.from_pretrained(
    CHECKPOINT_ENT_PATH, trust_remote_code=True
)
ent_mdl.to(device)
ent_mdl.eval()

print("[INFO] Loading IndoT5 Abstractive Model...")
t5_tok = AutoTokenizer.from_pretrained(T5_MODEL_NAME, use_fast=False, legacy=False)
t5_mdl = AutoModelForSeq2SeqLM.from_pretrained(T5_MODEL_NAME)
t5_mdl.to(device)

print("[SUCCESS] Semua model berhasil dimuat.")