# Leveraging Textual Entailment for Hybrid Summarization

> Undergraduate Thesis Project — I Putu Andika Prasetya (NIM 2205551137)
> Information Technology Study Program, Faculty of Engineering, Universitas Udayana (2026)

This repository contains a **hybrid text summarization system** for Indonesian
online news. The system combines an **extractive stage** based on **Textual
Entailment (TE)** — using an IndoBERT-based Recognizing Textual Entailment
(RTE) model — with an **abstractive stage** based on the **IndoT5 Transformer
model**. The goal is to produce summaries that are short, fluent, and, most
importantly, **factually consistent** with the source article.

---

## 1. What This Project Does

Most abstractive summarizers built on Transformers (T5, BART, etc.) are fluent
but prone to **hallucination** — generating text that is not actually
supported by the source document. Purely extractive summarizers are factually
safe but read as disjointed, copy-pasted sentences.

This project bridges the two:

1. **Extractive filtering with Textual Entailment** — every sentence in a news
   article is checked against a *premise* (a short reference text). Only
   sentences that are logically **entailed** by the premise are kept.
2. **Abstractive rewriting with IndoT5** — the filtered, entailed sentences
   are concatenated and rewritten into a single, coherent, natural-sounding
   summary.

Three premise strategies are compared: **highlight** (existing article
summary), **first sentence**, and **last sentence**. The system is benchmarked
against a **TextRank + IndoT5** baseline using ROUGE-1/2/L and human
evaluation (relevance, factuality, completeness, readability).

**Key result:** the *first-sentence-as-premise* strategy performed best on
both datasets (Tempo.co and Liputan6.com), outperforming the TextRank–IndoT5
baseline on both automatic (ROUGE) and human evaluation metrics.

See [`PROBLEM_STATEMENT.md`](./PROBLEM_STATEMENT.md) for the full background,
research questions, objectives, and scope, and
[`WORKFLOW.md`](./WORKFLOW.md) for the end-to-end pipeline and system
architecture with flowcharts.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Data collection | Python, BeautifulSoup (web scraping), MongoDB (raw data storage) |
| Extractive selection | IndoBERT fine-tuned for Recognizing Textual Entailment (RTE) |
| Abstractive generation | IndoT5 (Text-to-Text Transfer Transformer, Indonesian) |
| Baseline comparison | TextRank + IndoT5 |
| Backend / API | FastAPI (RESTful) |
| Frontend | Streamlit |
| Evaluation | ROUGE-1 / ROUGE-2 / ROUGE-L, human evaluation rubric |
| Testing | Postman (API testing), Black-box testing (equivalence partitioning, boundary value analysis) |
| Experiment environment | Google Colab, Visual Studio Code |

---

## 3. Project Structure

```
project-root/
├── Scraping/               # News collection notebooks
├── Preprocessing/          # Preprocessing notebooks
├── Sentences Tagging/      # Sentence tagging notebooks
├── Liputan6/               # Liputan6 experiment notebooks and outputs
├── Tempo/                  # Tempo experiment notebooks and outputs
├── Baseline/               # TextRank baseline experiments
├── Evaluasi/               # Evaluation notebooks
├── main.py                 # FastAPI backend
├── frontend.py             # Streamlit frontend
├── web/                    # React/Vite frontend
└── docs/                   # Research and workflow documentation
```

---

## 4. How to Use

### 4.1 Prerequisites

- Python 3.9+
- MongoDB (local or hosted) for raw article storage
- GPU recommended (the thesis was run on an RTX 3060 6GB) for IndoBERT-RTE
  inference and IndoT5 generation, though CPU inference works for small
  batches
- Pretrained models: an IndoBERT-RTE checkpoint (fine-tuned for
  entailment/contradiction/neutral classification) and an IndoT5 checkpoint
  fine-tuned for abstractive summarization

### 4.2 Install dependencies

```bash
pip install -r requirements.txt

The fine-tuned IndoBERT-RTE checkpoint is not included in this repository.
Set `CHECKPOINT_ENT_PATH` to its local directory before starting the API.
```

### 4.3 Run the pipeline end-to-end (conceptual CLI)

```bash
# Start the API
python main.py
```

### 4.4 Run the web application

```bash
# Start the FastAPI backend
uvicorn main:app --reload --port 8000

# In a separate terminal, start the React frontend
cd web
npm install
npm run dev
```

Then open the Vite URL (usually `http://localhost:5173`), paste or type
an Indonesian news article into the text area, choose the premise strategy
and summary-length parameters, and click **Ringkas / Summarize** to get:

- the abstractive summary,
- the extractive sentences that were selected (with entailment confidence
  scores),
- summary statistics (original sentence count, selected sentence count,
  selection ratio, output word count).

### 4.5 API usage (example)

```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{
        "text": "<full news article text>",
        "premise_strategy": "first_sentence",
        "compression_ratio": 1.0,
        "min_length": 30,
        "max_length": 256
      }'
```

Response (simplified):

```json
{
  "summary": "...",
  "selected_sentences": ["...", "..."],
  "total_sentences": 22,
  "selected_sentence_count": 4,
  "selection_ratio": 0.18,
  "average_confidence": 0.94
}
```

---

## 5. Evaluation Summary

| Dataset | Best Strategy | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|---|
| Tempo.co | First sentence, ratio 100% | 0.6799 | 0.5534 | 0.6645 |
| Liputan6.com | First sentence, ratio 100% | 0.6335 | 0.4768 | 0.6066 |

Human evaluation (relevance, factuality, completeness, readability) also
favored the first-sentence-as-premise strategy on both datasets.

---

## 6. Related Documents

- [`PROBLEM_STATEMENT.md`](./PROBLEM_STATEMENT.md) — background, research
  problem, objectives, benefits, and scope/limitations.
- [`WORKFLOW.md`](./WORKFLOW.md) — full pipeline explanation with flowcharts
  (research flow, pipeline architecture, entailment selection, evaluation).
- [`diagrams/`](./diagrams) — standalone Mermaid flowcharts referenced from
  `WORKFLOW.md`.
