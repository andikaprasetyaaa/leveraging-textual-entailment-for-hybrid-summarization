"""
Compare SeaLLM and IndoT5 first-sentence summaries
on matching Liputan6 documents.

SeaLLM file:
    summary_25
    summary_50
    summary_75
    summary_100

IndoT5 / Gold:
    automatically detects common summary column names.

Outputs:
    comparison_seallm_vs_indot5.csv
    comparison_seallm_vs_indot5_summary.csv
"""

from pathlib import Path
import json
import re

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from rouge_score import rouge_scorer


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).parent

SEALLM_FILE = (
    ROOT / "1_final_summary_first_sentences_liputan6_seallm.jsonl"
)

INDOT5_FILE = (
    ROOT / "Liputan6"
    / "Data"
    / "1_final_summary_first_sentences_liputan6.jsonl"
)

GOLD_FILE = (
    ROOT
    / "Gold Summary"
    / "Liputan6"
    / "silver_summary_first_sentences_liputan6.jsonl"
)

OUTPUT_DETAIL = ROOT / "comparison_seallm_vs_indot5.csv"

OUTPUT_SUMMARY = (
    ROOT / "comparison_seallm_vs_indot5_summary.csv"
)

OUTPUT_READABLE = (
    ROOT / "comparison_seallm_vs_indot5_readable.xlsx"
)


# ============================================================
# SEA LLM RATIO YANG AKAN DIBANDINGKAN
# ============================================================

# Pilih salah satu:
#
# "25"
# "50"
# "75"
# "100"
#
# Contoh:
# SEA LLM summary_100 -> dibandingkan dengan IndoT5

SEALLM_RATIO = "100"


# ============================================================
# LOAD JSONL
# ============================================================

def load_jsonl(path: Path) -> pd.DataFrame:
    """
    Membaca file JSONL menjadi pandas DataFrame.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"\nFile tidak ditemukan:\n{path}"
        )

    rows = []

    with path.open(
        encoding="utf-8"
    ) as source:

        for line_number, line in enumerate(
            source,
            start=1
        ):

            if not line.strip():
                continue

            try:
                rows.append(
                    json.loads(line)
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"\nJSON tidak valid di:\n"
                    f"{path}\n"
                    f"Baris: {line_number}\n"
                    f"Error: {exc}"
                )

    if not rows:
        raise ValueError(
            f"\nFile JSONL kosong:\n{path}"
        )

    return pd.DataFrame(rows)


# ============================================================
# DETEKSI KOLOM RINGKASAN
# ============================================================

def text_column(
    frame: pd.DataFrame,
    preferred_columns=None,
) -> str:
    """
    Mencari kolom ringkasan berdasarkan beberapa kemungkinan nama.
    """

    columns = list(frame.columns)

    # --------------------------------------------------------
    # 1. Prioritas kolom yang diberikan
    # --------------------------------------------------------

    if preferred_columns:

        for candidate in preferred_columns:

            if candidate in frame.columns:
                return candidate

    # --------------------------------------------------------
    # 2. Nama umum
    # --------------------------------------------------------

    candidates = [
        "Abstractive_Summary",
        "abstractive_summary",
        "summary",
        "silver_summary",
        "gold_summary",
        "Summary",
        "Silver_Summary",
    ]

    for candidate in candidates:

        if candidate in frame.columns:
            return candidate

    # --------------------------------------------------------
    # 3. Cari kolom yang mengandung "summary"
    # --------------------------------------------------------

    summary_columns = [
        column
        for column in columns
        if "summary" in column.lower()
    ]

    if len(summary_columns) == 1:
        return summary_columns[0]

    # --------------------------------------------------------
    # 4. Kalau masih ambigu -> error informatif
    # --------------------------------------------------------

    raise KeyError(
        "\nKolom ringkasan tidak ditemukan / ambigu.\n\n"
        f"Kolom yang tersedia:\n{columns}\n\n"
        f"Kolom yang mengandung 'summary':\n"
        f"{summary_columns}"
    )


def ratio_summary_column(frame: pd.DataFrame, ratio: str, label: str) -> str:
    """Resolve wide-format summary columns such as summary_25 or summary_100."""
    column = f"summary_{ratio}"
    if column in frame.columns:
        return column

    available = [
        name for name in frame.columns
        if name.startswith("summary_")
    ]
    raise KeyError(
        f"\nKolom {label} yang diminta tidak ditemukan.\n"
        f"Diminta: {column}\n"
        f"Tersedia: {available}\n"
        "Ubah SEALLM_RATIO agar sesuai dengan dataset."
    )


# ============================================================
# WORD COUNT
# ============================================================

def word_count(value) -> int:
    """
    Menghitung jumlah kata sederhana.
    """

    if pd.isna(value):
        return 0

    return len(
        re.findall(
            r"\b\w+\b",
            str(value)
        )
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(value) -> str:
    """
    Membersihkan nilai summary sebelum ROUGE.
    """

    if pd.isna(value):
        return ""

    text = str(value)

    # Normalisasi whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def extract_index(value):
    """Normalize numeric and prefixed dataset IDs to the same integer key."""
    value = str(value)
    match = re.search(r"_(\d+)$", value)
    if not match:
        match = re.search(r"^(\d+)$", value)
    if not match:
        match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else None


def save_readable_workbook(detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Write a side-by-side, wrapped Excel view for manual inspection."""
    readable_columns = [
        "index",
        "doc_id",
        "seallm_summary",
        "indot5_summary",
        "gold_summary",
        "seallm_words",
        "indot5_words",
        "seallm_composite",
        "indot5_composite",
        "winner",
    ]
    readable = detail[readable_columns].rename(
        columns={
            "index": "No.",
            "doc_id": "Doc ID",
            "seallm_summary": "SeaLLM Summary",
            "indot5_summary": "IndoT5 Summary",
            "gold_summary": "Gold Summary",
            "seallm_words": "SeaLLM Words",
            "indot5_words": "IndoT5 Words",
            "seallm_composite": "SeaLLM Score",
            "indot5_composite": "IndoT5 Score",
            "winner": "Winner",
        }
    )

    with pd.ExcelWriter(OUTPUT_READABLE, engine="openpyxl") as writer:
        readable.to_excel(writer, sheet_name="Side by Side", index=False)
        summary.to_excel(writer, sheet_name="Average", index=False)
        workbook = writer.book
        sheet = writer.sheets["Side by Side"]
        sheet.freeze_panes = "C2"
        sheet.auto_filter.ref = sheet.dimensions
        widths = {"A": 8, "B": 20, "C": 60, "D": 60, "E": 60, "F": 13, "G": 13, "H": 14, "I": 14, "J": 12}
        for column, width in widths.items():
            sheet.column_dimensions[column].width = width
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            if row[0].row > 1:
                sheet.row_dimensions[row[0].row].height = 90
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E3D")

        average = writer.sheets["Average"]
        for column in ("A", "B", "C", "D", "E", "F", "G"):
            average.column_dimensions[column].width = 18


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("COMPARISON SEALLM VS INDOT5")
    print("=" * 70)

    # ========================================================
    # LOAD FILE
    # ========================================================

    print("\n📂 Loading SeaLLM...")

    seallm_frame = load_jsonl(
        SEALLM_FILE
    )

    print(
        f"   Documents: {len(seallm_frame)}"
    )

    print(
        f"   Columns: {list(seallm_frame.columns)}"
    )


    print("\n📂 Loading IndoT5...")

    indot5_frame = load_jsonl(
        INDOT5_FILE
    )

    print(
        f"   Documents: {len(indot5_frame)}"
    )

    print(
        f"   Columns: {list(indot5_frame.columns)}"
    )


    print("\n📂 Loading Gold Summary...")

    gold_frame = load_jsonl(
        GOLD_FILE
    )

    print(
        f"   Documents: {len(gold_frame)}"
    )

    print(
        f"   Columns: {list(gold_frame.columns)}"
    )


    # ========================================================
    # VALIDASI DOC_ID
    # ========================================================

    for name, frame in [
        ("SeaLLM", seallm_frame),
        ("IndoT5", indot5_frame),
        ("Gold", gold_frame),
    ]:

        if "doc_id" not in frame.columns:

            raise KeyError(
                f"\nFile {name} tidak memiliki kolom 'doc_id'.\n"
                f"Kolom tersedia: {list(frame.columns)}"
            )


    # ========================================================
    # DETEKSI KOLOM SEALLM
    # ========================================================

    seallm_column = ratio_summary_column(
        seallm_frame,
        SEALLM_RATIO,
        "SeaLLM",
    )


    # ========================================================
    # DETEKSI KOLOM INDOT5
    # ========================================================

    indot5_column = ratio_summary_column(
        indot5_frame,
        SEALLM_RATIO,
        "IndoT5",
    )


    # ========================================================
    # DETEKSI KOLOM GOLD
    # ========================================================

    gold_column = text_column(
        gold_frame
    )


    print("\n" + "=" * 70)
    print("KOLOM YANG DIGUNAKAN")
    print("=" * 70)

    print(
        f"SeaLLM : {seallm_column}"
    )

    print(
        f"IndoT5 : {indot5_column}"
    )

    print(
        f"Gold   : {gold_column}"
    )


    # ========================================================
    # PREPARE DATA
    # ========================================================

    seallm = (
        seallm_frame[
            [
                "doc_id",
                seallm_column
            ]
        ]
        .rename(
            columns={
                "doc_id": "seallm_doc_id",
                seallm_column:
                    "seallm_summary"
            }
        )
    )


    indot5 = (
        indot5_frame[
            [
                "doc_id",
                indot5_column
            ]
        ]
        .rename(
            columns={
                "doc_id": "indot5_doc_id",
                indot5_column:
                    "indot5_summary"
            }
        )
    )


    gold = (
        gold_frame[
            [
                "doc_id",
                gold_column
            ]
        ]
        .rename(
            columns={
                "doc_id": "gold_doc_id",
                gold_column:
                    "gold_summary"
            }
        )
    )


    # ========================================================
    # NORMALIZE IDS BEFORE MERGE
    # ========================================================

    # Prediction IDs use values such as liputan6_00002 while the
    # gold file uses numeric IDs such as 2. The evaluation notebook
    # uses the numeric part as the canonical matching key.
    for dataset, id_column in (
        (seallm, "seallm_doc_id"),
        (indot5, "indot5_doc_id"),
        (gold, "gold_doc_id"),
    ):
        dataset["index"] = dataset[id_column].map(extract_index)
        dataset.dropna(subset=["index"], inplace=True)
        dataset["index"] = dataset["index"].astype(int)


    # ========================================================
    # REMOVE DUPLICATE INDEX
    # ========================================================

    seallm = seallm.drop_duplicates(subset=["index"])

    indot5 = indot5.drop_duplicates(subset=["index"])

    gold = gold.drop_duplicates(subset=["index"])


    # ========================================================
    # MERGE
    # ========================================================

    frame = (
        seallm
        .merge(
            indot5,
            on="index",
            how="inner"
        )
        .merge(
            gold,
            on="index",
            how="inner"
        )
    )


    print("\n" + "=" * 70)
    print("MATCHING DOCUMENTS")
    print("=" * 70)

    print(
        f"SeaLLM documents : {len(seallm)}"
    )

    print(
        f"IndoT5 documents : {len(indot5)}"
    )

    print(
        f"Gold documents   : {len(gold)}"
    )

    print(
        f"Matched documents: {len(frame)}"
    )

    if len(frame) < min(len(seallm), len(indot5), len(gold)):
        print(
            "WARNING: Tidak semua dokumen memiliki pasangan index "
            "di ketiga dataset."
        )


    if frame.empty:

        raise ValueError(
            "\nTidak ada doc_id yang cocok antara "
            "SeaLLM, IndoT5, dan Gold."
        )


    # ========================================================
    # ROUGE SCORER
    # ========================================================

    scorer = rouge_scorer.RougeScorer(
        [
            "rouge1",
            "rouge2",
            "rougeL",
        ],
        use_stemmer=False,
    )


    # ========================================================
    # CALCULATE ROUGE
    # ========================================================

    rows = []

    print("\n📊 Calculating ROUGE...")

    for row in frame.itertuples(
        index=False
    ):

        # ----------------------------------------------------
        # Clean
        # ----------------------------------------------------

        gold_summary = clean_text(
            row.gold_summary
        )

        seallm_summary = clean_text(
            row.seallm_summary
        )

        indot5_summary = clean_text(
            row.indot5_summary
        )


        # ----------------------------------------------------
        # Skip jika kosong
        # ----------------------------------------------------

        if not gold_summary:

            continue


        # ----------------------------------------------------
        # ROUGE SeaLLM
        # ----------------------------------------------------

        seallm_scores = scorer.score(
            gold_summary,
            seallm_summary
        )


        # ----------------------------------------------------
        # ROUGE IndoT5
        # ----------------------------------------------------

        indot5_scores = scorer.score(
            gold_summary,
            indot5_summary
        )


        # ----------------------------------------------------
        # Composite score
        #
        # Mean ROUGE-1 F1 + ROUGE-L F1
        # ----------------------------------------------------

        seallm_score = (
            seallm_scores["rouge1"].fmeasure
            +
            seallm_scores["rougeL"].fmeasure
        ) / 2


        indot5_score = (
            indot5_scores["rouge1"].fmeasure
            +
            indot5_scores["rougeL"].fmeasure
        ) / 2


        # ----------------------------------------------------
        # Winner
        # ----------------------------------------------------

        if seallm_score > indot5_score:

            winner = "SeaLLM"

        elif indot5_score > seallm_score:

            winner = "IndoT5"

        else:

            winner = "Tie"


        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        rows.append(
            {
                "doc_id": row.seallm_doc_id,

                "index": row.index,

                "seallm_doc_id": row.seallm_doc_id,

                "indot5_doc_id": row.indot5_doc_id,

                "gold_doc_id": row.gold_doc_id,

                "seallm_summary":
                    seallm_summary,

                "indot5_summary":
                    indot5_summary,

                "gold_summary":
                    gold_summary,

                "seallm_words":
                    word_count(
                        seallm_summary
                    ),

                "indot5_words":
                    word_count(
                        indot5_summary
                    ),

                "seallm_rouge1":
                    round(
                        seallm_scores[
                            "rouge1"
                        ].fmeasure,
                        4
                    ),

                "indot5_rouge1":
                    round(
                        indot5_scores[
                            "rouge1"
                        ].fmeasure,
                        4
                    ),

                "seallm_rouge2":
                    round(
                        seallm_scores[
                            "rouge2"
                        ].fmeasure,
                        4
                    ),

                "indot5_rouge2":
                    round(
                        indot5_scores[
                            "rouge2"
                        ].fmeasure,
                        4
                    ),

                "seallm_rougeL":
                    round(
                        seallm_scores[
                            "rougeL"
                        ].fmeasure,
                        4
                    ),

                "indot5_rougeL":
                    round(
                        indot5_scores[
                            "rougeL"
                        ].fmeasure,
                        4
                    ),

                "seallm_composite":
                    round(
                        seallm_score,
                        4
                    ),

                "indot5_composite":
                    round(
                        indot5_score,
                        4
                    ),

                "winner":
                    winner,
            }
        )


    # ========================================================
    # DETAIL DATAFRAME
    # ========================================================

    detail = pd.DataFrame(
        rows
    )


    if detail.empty:

        raise ValueError(
            "\nTidak ada data valid untuk dihitung."
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = pd.DataFrame(
        [
            {
                "method":
                    "SeaLLM",

                "ratio":
                    f"{SEALLM_RATIO}%",

                "documents":
                    len(detail),

                "mean_words":
                    round(
                        detail[
                            "seallm_words"
                        ].mean(),
                        2
                    ),

                "mean_rouge1":
                    round(
                        detail[
                            "seallm_rouge1"
                        ].mean(),
                        4
                    ),

                "mean_rouge2":
                    round(
                        detail[
                            "seallm_rouge2"
                        ].mean(),
                        4
                    ),

                "mean_rougeL":
                    round(
                        detail[
                            "seallm_rougeL"
                        ].mean(),
                        4
                    ),

                "mean_composite":
                    round(
                        detail[
                            "seallm_composite"
                        ].mean(),
                        4
                    ),

                "wins":
                    int(
                        (
                            detail["winner"]
                            == "SeaLLM"
                        ).sum()
                    ),
            },

            {
                "method":
                    "IndoT5",

                "ratio":
                    "-",

                "documents":
                    len(detail),

                "mean_words":
                    round(
                        detail[
                            "indot5_words"
                        ].mean(),
                        2
                    ),

                "mean_rouge1":
                    round(
                        detail[
                            "indot5_rouge1"
                        ].mean(),
                        4
                    ),

                "mean_rouge2":
                    round(
                        detail[
                            "indot5_rouge2"
                        ].mean(),
                        4
                    ),

                "mean_rougeL":
                    round(
                        detail[
                            "indot5_rougeL"
                        ].mean(),
                        4
                    ),

                "mean_composite":
                    round(
                        detail[
                            "indot5_composite"
                        ].mean(),
                        4
                    ),

                "wins":
                    int(
                        (
                            detail["winner"]
                            == "IndoT5"
                        ).sum()
                    ),
            },
        ]
    )


    # ========================================================
    # ADD TIE COUNT
    # ========================================================

    tie_count = int(
        (
            detail["winner"]
            == "Tie"
        ).sum()
    )


    # ========================================================
    # SAVE
    # ========================================================

    detail.to_csv(
        OUTPUT_DETAIL,
        index=False,
        encoding="utf-8-sig"
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig"
    )

    save_readable_workbook(detail, summary)


    # ========================================================
    # PRINT RESULT
    # ========================================================

    print("\n" + "=" * 70)
    print("HASIL PERBANDINGAN")
    print("=" * 70)

    print(
        summary.to_string(
            index=False
        )
    )

    print(
        f"\nTie: {tie_count}"
    )

    print("\n📁 Output:")

    print(
        f"Detail : {OUTPUT_DETAIL}"
    )

    print(
        f"Summary: {OUTPUT_SUMMARY}"
    )

    print(
        f"Readable: {OUTPUT_READABLE}"
    )

    print("\n✅ Selesai.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()