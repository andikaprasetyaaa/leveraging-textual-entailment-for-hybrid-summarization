# ========================================================================
# CONFIG — Konstanta & Konfigurasi Global
# ========================================================================

import os
import torch

os.environ["DISABLE_TRANSFORMERS_AV"] = "1"

# Set this to the local directory containing the fine-tuned IndoBERT-RTE model.
CHECKPOINT_ENT_PATH = os.environ.get(
    "CHECKPOINT_ENT_PATH",
    os.path.join(os.path.dirname(__file__), "models", "indobert-rte"),
)
T5_MODEL_NAME = "Wikidepia/IndoT5-base-paraphrase"

MAX_SENTENCES = 800
MAX_INPUT_CHARS = 1500

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")

CREATIVITY_MAP = {
    "precise":  {"do_sample": True, "num_beams": 4, "length_penalty": 1.2},
    "balanced": {"do_sample": True, "num_beams": 2, "length_penalty": 1.0},
    "creative": {"do_sample": True,  "num_beams": 1, "temperature": 0.9,
                 "top_k": 50, "top_p": 0.95, "length_penalty": 0.8},
}