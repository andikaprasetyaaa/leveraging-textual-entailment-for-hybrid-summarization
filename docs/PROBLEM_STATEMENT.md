# Problem Statement

## 1. Background

The rapid growth of internet and digital media has caused a massive and fast
spread of information (Azam et al. 2025; Husniah et al. 2022). Text data,
especially online news articles, is produced every day in enormous volume
(Putri, Trisna & Rusjayanthi 2025). This leads to **information overload**:
readers struggle to find relevant information within a huge amount of data
(N. Lin et al. 2022), making it slow and difficult to grasp the core of a
document (Mugi Karanja & Matheka 2022).

**Automatic Text Summarization (ATS)** is one of the main solutions to this
problem in the field of Natural Language Processing. ATS aims to produce a
short summary that preserves the essential meaning of the source text (Lwin &
Nwet 2021), helping readers get information quickly without reading the full
document (Husniah et al. 2022).

There are two main approaches to ATS:

- **Extractive summarization** — selects important sentences directly from
  the source text without changing their wording. It is factually safe but
  often incoherent when sentences from different parts of the document are
  stitched together.
- **Abstractive summarization** — rewrites the content using new sentences
  that represent the core meaning. It reads more naturally (similar to human
  writing) but is prone to generating information not fully supported by the
  source, a phenomenon known as **hallucination**.

Research on Indonesian-language ATS is still limited compared to English
(Wijaya & Girsang 2023). Most existing work uses conventional extractive
methods on small, closed datasets (Hadwirianto M, Hamami F & Pratiwi O 2024),
and deep-learning-based approaches are not yet optimal due to limited
dataset availability (Putra, Siahaan & Saikhu 2022; 2025).

Advances in NLP have produced Transformer architectures (e.g., **T5**) that
understand context well and generate coherent summaries (Itsnaini et al.
2023), and these have started to be adapted for low-resource languages such
as Indonesian. However, abstractive summarization still struggles to
maintain **factual consistency**. **Textual Entailment (TE)** — also known as
**Recognizing Textual Entailment (RTE)** — offers a way to verify whether a
generated summary is logically supported by (does not contradict) the source
document (Putra et al. 2023; Bhuyan et al. 2023).

This research proposes a **hybrid summarization system** that integrates
Textual Entailment and a Transformer model for Indonesian news: an extractive
stage first uses TE to select the most relevant and factual sentences, and an
abstractive stage then uses a Transformer (IndoT5) to generate a coherent
final summary.

## 2. Research Problem (Rumusan Masalah)

Based on the background above, the research questions are:

1. **How** can a hybrid text summarization system architecture be designed
   and implemented that integrates a textual-entailment-based extractive
   method for factual sentence selection with a Transformer-based abstractive
   method, to produce summaries of Indonesian-language news?
2. **How** does the quality of summaries produced by the proposed hybrid
   system — in terms of relevance, factuality, completeness, and readability
   — compare against a conventional hybrid summarization baseline
   (TextRank + IndoT5) on Indonesian-language news?

## 3. Objectives

1. Design and implement a hybrid text-summarization system that integrates
   textual entailment at the extractive stage with a Transformer model at the
   abstractive stage, for summarizing Indonesian-language news.
2. Compare the quality of summaries produced by the proposed hybrid model
   against a standard hybrid baseline, based on relevance, factuality,
   completeness, and readability.

## 4. Benefits

### 4.1 Theoretical

- **Advancing hybrid summarization models** — contributes a new hybrid
  architecture to the NLP body of knowledge, using textual entailment as a
  semantic selection mechanism to preserve information consistency before
  abstractive rewriting.
- **Contribution to Indonesian NLP** — provides a case study and benchmark
  for applying advanced deep-learning techniques (Transformer + textual
  entailment) to Indonesian, a low-resource language.

### 4.2 Practical

- **For readers / the general public** — an architecture that produces
  accurate, easy-to-understand news summaries, helping people cope with
  information overload and consume news faster.
- **For the media and journalism industry** — a potential tool for
  automatically generating article highlights/summaries, speeding up
  editorial workflows and improving reader engagement.
- **For academics and researchers** — a summarization tool that can help
  filter and summarize large volumes of Indonesian-language literature or
  documents, speeding up literature review and textual analysis.

## 5. Scope and Limitations (Batasan Masalah)

1. **Domain and language** — this research focuses exclusively on
   summarizing **Indonesian-language news articles**. Other domains
   (scientific papers, literary works, conversation transcripts) and other
   languages are out of scope.
2. **Type of summarization** — the architecture is designed for
   **single-document summarization**. Multi-document summarization
   challenges (e.g., cross-document redundancy) are not covered.
3. **Hybrid architecture scope** — the tested architecture is limited to the
   combination of textual entailment (sentence selection) and a Transformer
   model (text generation). An extensive comparison against other
   summarization architectures is not part of this research.

## 6. Data Sources

- **Tempo.co** and **Liputan6.com** news articles, collected between
  August–October 2025, via web scraping.
- Each article record includes: title, publication date, URL, existing
  summary/highlight, and full content.

## 7. Evaluation Approach

- **Automatic metrics:** ROUGE-1, ROUGE-2, ROUGE-L (precision, recall, F1),
  comparing the generated summary to a reference summary.
- **Human evaluation:** a linguistics-expert validator rubric (1–5 scale)
  scoring four aspects — **relevance**, **factuality**, **completeness**, and
  **readability**.
- **Baseline for comparison:** TextRank (extractive) + IndoT5 (abstractive).
