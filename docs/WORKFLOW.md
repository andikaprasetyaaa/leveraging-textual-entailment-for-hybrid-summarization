# System Workflow & Architecture

This document describes the end-to-end workflow of the hybrid summarization
system, from research design down to the deployed web application. Flowcharts
are provided as Mermaid diagrams (renderable on GitHub, GitLab, VS Code, and
most Markdown viewers). Standalone copies of each diagram also live in
[`diagrams/`](./diagrams).

---

## 1. Overall Research Flow

The research proceeds from problem identification through system
implementation and conclusion.

```mermaid
flowchart TD
    A[Identify Problem] --> B[Formulate Research Questions & Objectives]
    B --> C[Literature Study]
    C --> D[Collect Indonesian News Data<br/>Tempo.co & Liputan6.com]
    D --> E[Build NLI Dataset<br/>premise-hypothesis pairs]
    E --> F[Preprocessing<br/>text cleaning + deduplication]
    F --> G[Run 3 Pipeline Scenarios<br/>Highlight / First Sentence / Last Sentence as premise]
    G --> H[Entailment-based Extractive Selection]
    H --> I[Concatenate Selected Sentences]
    I --> J[Abstractive Summarization with IndoT5]
    J --> K[Evaluate Pipeline<br/>ROUGE + Human Evaluation]
    K --> L[Implement Web-based System<br/>FastAPI + Streamlit]
    L --> M[Analyze Results & Draw Conclusions]
```

---

## 2. End-to-End Pipeline Architecture

The core pipeline transforms a raw article into a hybrid (extractive +
abstractive) summary.

```mermaid
flowchart TD
    subgraph S1[1. Data Collection]
        A1[Web Scraping<br/>BeautifulSoup] --> A2[(Raw Data<br/>MongoDB)]
    end

    subgraph S2[2. NLI Dataset Construction]
        A2 --> B1[Split into Paragraphs & Sentences]
        B1 --> B2[Assign Sentence/Paragraph IDs]
        B2 --> B3[Build Premise-Hypothesis Pairs]
    end

    subgraph S3[3. Preprocessing]
        B3 --> C1[Text Cleaning<br/>remove noise, normalize whitespace]
        C1 --> C2[Drop Duplicate Pairs]
    end

    subgraph S4[4. Pipeline & Evaluation]
        C2 --> D0{Choose Premise Strategy}
        D0 -->|Highlight| D1[IndoBERT-RTE<br/>Entailment Classification]
        D0 -->|First Sentence| D1
        D0 -->|Last Sentence| D1
        D1 --> D2[Select Entailed Sentences]
        D2 --> D3[Concatenate & Group by Document]
        D3 --> D4[IndoT5<br/>Abstractive Summarization]
        D4 --> D5[Evaluate: ROUGE-1/2/L<br/>+ Human Evaluation]
    end

    D5 --> E1[Final Hybrid Summary]
```

---

## 3. Textual Entailment Sentence Selection (Extractive Stage)

Three premise strategies are evaluated independently, each producing its own
set of entailed sentences.

```mermaid
flowchart LR
    P0[Article] --> P1{Premise Source}
    P1 -->|Highlight| PA[Premise = Article Highlight]
    P1 -->|First Sentence| PB[Premise = First Sentence]
    P1 -->|Last Sentence| PC[Premise = Last Sentence]

    PA --> Q1[Pair with every other<br/>sentence as Hypothesis]
    PB --> Q1
    PC --> Q1

    Q1 --> R1[IndoBERT-RTE Model]
    R1 --> R2{Predicted Label}
    R2 -->|Entailment| S1[Keep Sentence<br/>+ Confidence Score]
    R2 -->|Contradiction / Neutral| S2[Discard Sentence]

    S1 --> T1[Ordered List of Entailed Sentences]
```

**Result highlights from the thesis:**

| Premise strategy | Avg. selection ratio (Tempo) | Avg. selection ratio (Liputan6) | Avg. confidence |
|---|---|---|---|
| Highlight | 17.18% | 25.96% | ~0.94 |
| First sentence | 18.57% | 20.20% | ~0.94 |
| Last sentence | 13.49% | 10.70% | ~0.92 |

---

## 4. Abstractive Summarization Stage (IndoT5)

```mermaid
flowchart TD
    A[Entailed & Concatenated Text] --> B[Tokenization]
    B --> C[IndoT5 Generation<br/>beam search, no-repeat n-gram, repetition penalty]
    C --> D[Decoding]
    D --> E[Post-processing]
    E --> F[Final Abstractive Summary]
```

Key generation hyperparameters used: max input length 512, output length
30–256 tokens, 2 beams, no-repeat n-gram size 4, repetition penalty 1.5,
length penalty 1.0, early stopping enabled.

---

## 5. Evaluation Workflow

Two complementary evaluation tracks run in parallel: automatic (ROUGE) and
human (expert linguistic rubric).

```mermaid
flowchart TD
    A[Generated Summaries<br/>per premise strategy] --> B[Automatic Evaluation]
    A --> C[Human Evaluation]

    B --> B1[Compute ROUGE-1 / ROUGE-2 / ROUGE-L<br/>vs Reference Summary]
    B1 --> B2[Compare against<br/>TextRank + IndoT5 Baseline]

    C --> C1[Linguistics Expert Validator]
    C1 --> C2[Score 1-5 on:<br/>Relevance, Factuality,<br/>Completeness, Readability]

    B2 --> D[Aggregate & Compare<br/>All Scenarios]
    C2 --> D
    D --> E[Select Best-performing<br/>Premise Strategy]
```

---

## 6. Web System Architecture (FastAPI + Streamlit)

```mermaid
flowchart LR
    U[User] -->|Enter/paste article| FE[Streamlit Frontend]
    FE -->|HTTP POST /summarize| BE[FastAPI Backend]
    BE --> M1[IndoBERT-RTE<br/>Entailment Selection]
    M1 --> M2[IndoT5<br/>Abstractive Generation]
    M2 -->|JSON response| BE
    BE -->|Summary + stats + selected sentences| FE
    FE -->|Render results| U
```

The FastAPI backend exposes a RESTful endpoint that receives the raw article
text (plus optional parameters such as premise strategy, compression ratio,
min/max summary length) and returns:

- the abstractive summary,
- the list of selected (entailed) sentences with confidence scores,
- summary statistics (total sentences, selected sentence count, selection
  ratio, output word count).

The Streamlit frontend provides an interactive UI (text area, buttons,
parameter widgets) and calls the backend API in real time, displaying the
final summary alongside transparency details of *why* those sentences were
kept (the entailment step).

---

## 7. System Testing Workflow (Black-box Testing)

```mermaid
flowchart TD
    A[Identify Test Cases &<br/>Test Plan] --> B[Valid Input Testing<br/>e.g. valid article text]
    A --> C[Invalid/Edge Input Testing<br/>empty text, special characters,<br/>boundary parameter values]
    B --> D[Execute via UI / Postman]
    C --> D
    D --> E[Compare Actual vs Expected Output]
    E --> F{Pass?}
    F -->|Yes| G[Mark Test Case Passed]
    F -->|No| H[Log Defect / Refine System]
```

Testing covers: input validation (empty text, whitespace-only, special
characters), parameter validation (e.g. `min_length >= max_length`,
compression ratio boundaries), UI behavior (reset form, error messages when
the backend is unavailable, expander interactions), and correctness of
displayed outputs (summary text, sentence counts, confidence categories).

---

## 8. Summary of the Full Journey (Problem → Solution)

```mermaid
flowchart LR
    A[Problem:<br/>Information overload from<br/>growing Indonesian online news] --> B[Gap:<br/>Abstractive Transformers are fluent<br/>but hallucinate; extractive methods<br/>are factual but incoherent]
    B --> C[Proposed Solution:<br/>Hybrid pipeline —<br/>Textual Entailment extractive filter<br/>+ IndoT5 abstractive generation]
    C --> D[Experimentation:<br/>3 premise strategies vs<br/>TextRank+IndoT5 baseline]
    D --> E[Evaluation:<br/>ROUGE-1/2/L + Human Evaluation<br/>on Tempo.co & Liputan6.com]
    E --> F[Finding:<br/>First-sentence-as-premise<br/>wins on both datasets]
    F --> G[Deployment:<br/>FastAPI + Streamlit<br/>web application]
```
