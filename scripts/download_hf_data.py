"""Download and process HuggingFace datasets for Alzheimer Chat-RL.

Downloads (English, then optionally translates to Spanish via Groq):
  - go_emotions   : 58 k Reddit comments with 28 emotion labels (Google)
  - daily_dialog  : 13 k everyday conversations + dialogue-act labels
  - soda          : 1.5 M social dialogues with emotion annotations (AllenAI)

Extracted subsets saved to data/hf/:
  empathy_openers_es.jsonl   — phrases per emotion (EN+ES)
  questions_es.jsonl         — question utterances by dialogue act
  short_responses_es.jsonl   — brief validating/affirming responses
  warmth_openers_es.jsonl    — warm/caring opening utterances
  stats.json                 — counts and corpus info

Usage:
    python scripts/download_hf_data.py            # EN patterns only (fast)
    python scripts/download_hf_data.py --translate # + Groq ES translation
    python scripts/download_hf_data.py --max 500  # limit per dataset
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datasets import load_dataset
from tqdm import tqdm

OUT_DIR = ROOT / "data" / "hf"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Groq translation helper ───────────────────────────────────────

def _groq_translate_batch(texts: list[str], client) -> list[str]:
    """Translate a batch of English phrases to Spanish via Groq."""
    joined = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        "Traduce al español natural estas frases cortas de conversación. "
        "Mantén el tono empático y cálido. Devuelve SOLO las traducciones "
        "numeradas, sin explicaciones:\n\n" + joined
    )
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.3,
    )
    lines = resp.choices[0].message.content.strip().splitlines()
    results = []
    for line in lines:
        line = re.sub(r"^\d+\.\s*", "", line).strip()
        if line:
            results.append(line)
    # Pad if model returned fewer lines
    while len(results) < len(texts):
        results.append(texts[len(results)])
    return results[:len(texts)]


def _get_groq_client():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=key)
    except Exception:
        return None


def translate_list(texts: list[str], client, batch: int = 20) -> list[str]:
    results = []
    for i in range(0, len(texts), batch):
        chunk = texts[i : i + batch]
        try:
            results.extend(_groq_translate_batch(chunk, client))
        except Exception as e:
            print(f"  [warn] traducción falló en batch {i}: {e}")
            results.extend(chunk)
    return results


# ── EmpatheticDialogues ───────────────────────────────────────────

EMOTION_MAP = {
    # positive → useful for engagement
    "joyful": "alegría", "excited": "entusiasmo", "proud": "orgullo",
    "grateful": "gratitud", "caring": "cariño", "hopeful": "esperanza",
    "nostalgic": "nostalgia", "sentimental": "sentimiento",
    # neutral
    "anticipating": "expectación", "content": "calma",
    "confident": "confianza", "prepared": "preparado",
    # relevant negative (to detect)
    "sad": "tristeza", "anxious": "ansiedad", "afraid": "miedo",
    "lonely": "soledad", "disgusted": "malestar",
}

USEFUL_EMOTIONS = set(EMOTION_MAP.keys())

# go_emotions label index → name (simplified split has 28 labels)
GO_EMOTIONS_LABELS = [
    "admiration","amusement","anger","annoyance","approval","caring",
    "confusion","curiosity","desire","disappointment","disapproval",
    "disgust","embarrassment","excitement","fear","gratitude","grief",
    "joy","love","nervousness","optimism","pride","realization",
    "relief","remorse","sadness","surprise","neutral",
]
GO_POSITIVE = {"admiration","caring","excitement","gratitude","joy","love","optimism","pride","relief","amusement","approval"}
GO_NEGATIVE = {"sadness","fear","grief","nervousness","disappointment","remorse"}


def process_go_emotions(max_samples: int, translate: bool, client) -> dict:
    print("\n[1/3] Descargando go_emotions (Google) …")
    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")

    positives: list[tuple[str, str]] = []  # (label_name, text)
    responses: list[str] = []

    for row in tqdm(ds, desc="  filtrando"):
        text = row["text"].strip()
        labels = row["labels"]
        if not labels or len(text) > 120 or len(text) < 8:
            continue
        label_name = GO_EMOTIONS_LABELS[labels[0]] if labels[0] < len(GO_EMOTIONS_LABELS) else "neutral"
        if label_name in GO_POSITIVE and len(positives) < max_samples:
            positives.append((label_name, text))
        if label_name in {"caring", "love", "gratitude"} and "?" not in text and len(text.split()) <= 18:
            responses.append(text)

    en_texts = [t for _, t in positives]
    es_texts = translate_list(en_texts, client) if translate and client else en_texts

    records = [
        {
            "emotion_en": lbl,
            "emotion_es": EMOTION_MAP.get(lbl, lbl),
            "utterance_en": en,
            "utterance_es": es,
            "source": "go_emotions",
        }
        for (lbl, en), es in zip(positives, es_texts)
    ]

    resp_sample = responses[:max_samples // 2]
    resp_es = translate_list(resp_sample, client) if translate and client else resp_sample
    resp_records = [
        {"utterance_en": en, "utterance_es": es, "source": "go_emotions_response"}
        for en, es in zip(resp_sample, resp_es)
    ]

    _save_jsonl(OUT_DIR / "empathy_openers_es.jsonl", records)
    _save_jsonl(OUT_DIR / "short_responses_es.jsonl", resp_records)

    print(f"  -> {len(records)} frases con emoción positiva, {len(resp_records)} respuestas cortas")
    return {"empathy_openers": len(records), "short_responses": len(resp_records)}


# ── DailyDialog ───────────────────────────────────────────────────

# Dialogue act labels: 0=dummy, 1=inform, 2=question, 3=directive, 4=commissive
DA_LABEL = {1: "inform", 2: "question", 3: "directive", 4: "commissive"}


def process_daily_dialog(max_samples: int, translate: bool, client) -> dict:
    """Extract question/directive patterns from SODA (works with current datasets API)."""
    print("\n[2/3] Extrayendo preguntas desde allenai/soda ...")
    try:
        ds = load_dataset("allenai/soda", split="train")
    except Exception as e:
        print(f"  [skip] soda no disponible: {e}")
        # Fallback: built-in seed questions relevant to the project
        questions = [
            "What do you enjoy doing in the mornings?",
            "Can you tell me something about your family?",
            "Do you remember any songs from your youth?",
            "What was your favorite meal when you were young?",
            "Where did you grow up?",
            "What hobbies did you have?",
            "Do you like music?",
            "What was your job?",
            "Do you have any children?",
            "What season do you prefer?",
        ]
        en_q = questions[:max_samples]
        es_q = translate_list(en_q, client) if translate and client else en_q
        records = [{"act": "question", "utterance_en": en, "utterance_es": es,
                    "source": "builtin"} for en, es in zip(en_q, es_q)]
        _save_jsonl(OUT_DIR / "questions_es.jsonl", records)
        print(f"  -> {len(records)} preguntas (fallback integrado)")
        return {"questions": len(records), "directives": 0}

    questions: list[str] = []
    directives: list[str] = []

    for row in tqdm(ds, desc="  filtrando diálogos"):
        if len(questions) >= max_samples and len(directives) >= max_samples // 2:
            break
        dialog = row.get("dialogue", [])
        for utt in dialog:
            utt = utt.strip()
            if len(utt) < 5 or len(utt) > 100:
                continue
            if "?" in utt and len(questions) < max_samples:
                questions.append(utt)
            elif not utt.endswith("?") and len(utt.split()) <= 15 and len(directives) < max_samples // 2:
                directives.append(utt)

    all_en = questions + directives
    all_es = translate_list(all_en, client) if translate and client else all_en

    records = [
        {"act": "question" if i < len(questions) else "directive",
         "utterance_en": en, "utterance_es": es, "source": "soda_dialog"}
        for i, (en, es) in enumerate(zip(all_en, all_es))
    ]

    _save_jsonl(OUT_DIR / "questions_es.jsonl", records)
    print(f"  -> {len(questions)} preguntas, {len(directives)} directivas")
    return {"questions": len(questions), "directives": len(directives)}


# ── SODA (social dialogues) ────────────────────────────────────────

def process_soda(max_samples: int, translate: bool, client) -> dict:
    print("\n[3/3] Descargando SODA (social dialogues) …")
    try:
        ds = load_dataset("allenai/soda", split="train")
    except Exception as e:
        print(f"  [skip] SODA no disponible: {e}")
        return {}

    warmth: list[str] = []
    for row in tqdm(ds, desc="  filtrando"):
        if len(warmth) >= max_samples:
            break
        narr = row.get("narrative", "")
        dialog = row.get("dialogue", [])
        if not dialog:
            continue
        # Take short first turns with positive/warm narrative context
        first = dialog[0].strip()
        if len(first) < 80 and len(first) > 8 and "care" in narr.lower():
            warmth.append(first)

    es_warmth = translate_list(warmth, client) if translate and client else warmth
    records = [
        {"utterance_en": en, "utterance_es": es, "source": "soda"}
        for en, es in zip(warmth, es_warmth)
    ]

    path = OUT_DIR / "warmth_openers_es.jsonl"
    _save_jsonl(path, records)
    print(f"  -> {len(records)} utterances de calidez")
    return {"soda_warmth": len(records)}


# ── Utilities ─────────────────────────────────────────────────────

def _save_jsonl(path: Path, records: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Guardado: {path.relative_to(ROOT)} ({len(records)} registros)")


def print_summary(stats: dict, translate: bool):
    print("\n" + "=" * 60)
    print("  RESUMEN  data/hf/")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:35s} {v:>6}")
    traduc = "SI (Groq)" if translate else "NO (EN original)"
    print(f"\n  Traduccion al espanol: {traduc}")
    print("\n  Archivos generados:")
    for f in sorted(OUT_DIR.glob("*.jsonl")):
        size = f.stat().st_size // 1024
        print(f"    {f.name:40s} {size:>5} KB")
    print("\n  Cómo usar estos datos:")
    print("  -> empathy_openers_es.jsonl   -> ampliar plantillas en src/chatbot/actions.py")
    print("  -> questions_es.jsonl         -> expandir CognitiveTestBank con preguntas reales")
    print("  -> short_responses_es.jsonl   -> mejorar prompts del simulador (patient.py)")
    print("  -> warmth_openers_es.jsonl    -> seed de GREETING y PROPOSE_ACTIVITY")


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--translate", action="store_true",
                        help="Traducir al español via Groq (requiere GROQ_API_KEY en .env)")
    parser.add_argument("--max", type=int, default=300,
                        help="Máximo de ejemplos por dataset (default: 300)")
    args = parser.parse_args()

    client = None
    if args.translate:
        client = _get_groq_client()
        if client:
            print("✓ Groq disponible — se traducirá al español")
        else:
            print("⚠ GROQ_API_KEY no encontrada — se guardarán en inglés")

    stats: dict = {}
    stats.update(process_go_emotions(args.max, args.translate, client))
    stats.update(process_daily_dialog(args.max, args.translate, client))
    stats.update(process_soda(args.max, args.translate, client))

    stats_path = OUT_DIR / "stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({"counts": stats, "translated": args.translate,
                   "max_per_dataset": args.max}, f, indent=2, ensure_ascii=False)

    print_summary(stats, args.translate)


if __name__ == "__main__":
    main()
