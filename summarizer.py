from config import MAX_INPUT_CHARS, CREATIVITY_MAP, device
from models import t5_tok, t5_mdl
from postprocessing import (
    clean_t5_output,
    filter_sentences,
    restore_proper_nouns,
    smart_sentence_split,
    remove_similar_sentences,
    filter_hallucination,
    fix_sentences,
    protect_proper_nouns,
)


def rewrite_with_t5(text: str, min_len: int, max_len: int, creativity: str) -> str:
    # Batasi input sesuai MAX_INPUT_CHARS (dinamis dari config)
    text_input = text[:MAX_INPUT_CHARS]

    # STEP 1: Protect proper nouns sebelum masuk T5
    protected_input, entities = protect_proper_nouns(text_input)

    # STEP 2: Tokenisasi dengan prefix "paraphrase:"
    #         [FIX] Sebelumnya "summarize: " → diubah ke "paraphrase: "
    #         sesuai model IndoT5-base-paraphrase
    inputs = t5_tok(
        "paraphrase: " + protected_input,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    input_ids = inputs.input_ids.to(device)
    attention_mask = inputs.attention_mask.to(device)

    gen_kwargs = CREATIVITY_MAP.get(creativity, CREATIVITY_MAP["balanced"])

    ids = t5_mdl.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_length=max_len,
        min_length=min_len,
        no_repeat_ngram_size=4,
        repetition_penalty=1.5,
        early_stopping=True,
        **gen_kwargs,
    )

    summary = t5_tok.decode(ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

    # STEP 3: Post-processing pipeline
    summary = clean_t5_output(summary)
    summary = filter_sentences(summary)          # [NEW] dari notebook
    summary = restore_proper_nouns(summary, entities)
    summary = smart_sentence_split(summary)
    summary = remove_similar_sentences(summary)
    summary = filter_hallucination(summary, text_input)
    summary = fix_sentences(summary)

    return summary if summary.strip() else text[:150]