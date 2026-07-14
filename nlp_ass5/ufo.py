from __future__ import annotations

import math
import os
import re
from collections import Counter
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .common import DATA_PROCESSED, DATA_RAW, FIGURES, REPORTS, STOPWORDS, clean_text, ensure_dirs, save_bar, tokenize, top_terms
from .manual_docs import compact_name
from .semantic import SemanticEmbedder, chunk_text


PURSUE_MIRROR = "https://raw.githubusercontent.com/DenisSergeevitch/UFO-USA/main/metadata/uap-csv.csv"
SCHEMA = [
    "source", "record_id", "date", "date_precision", "date_hint_start", "date_hint_end",
    "city", "state", "country", "latitude", "longitude", "location_text",
    "description_text", "text_kind", "extracted_text_path", "object_shape", "duration", "source_file_or_link",
]
SHAPE_CANONICAL = {
    "light": "light",
    "lights": "light",
    "sphere": "sphere",
    "spherical": "sphere",
    "ball": "sphere",
    "orb": "sphere",
    "orbs": "sphere",
    "triangle": "triangle",
    "triangular": "triangle",
    "delta": "triangle",
    "disk": "disk",
    "disc": "disk",
    "saucer": "disk",
    "fireball": "fireball",
    "formation": "formation",
    "cigar": "cigar",
    "cylinder": "cigar",
    "cylindrical": "cigar",
    "circle": "circle",
    "circular": "circle",
    "oval": "oval",
}
SHAPE_TERMS = sorted(set(SHAPE_CANONICAL.values()))
COLOR_TERMS = ["red", "orange", "blue", "green", "white", "yellow", "silver", "black", "gray", "grey", "gold"]
MOTION_TERMS = ["hover", "hovering", "accelerate", "accelerated", "turn", "turned", "descend", "descending", "rise", "rising", "disappear", "vanish", "formation"]
MILITARY_TERMS = ["military", "base", "aircraft", "radar", "pilot", "navy", "army", "fbi", "missile", "air force", "nasa", "cia", "faa"]
ENTITY_TERMS = SHAPE_TERMS + COLOR_TERMS + MOTION_TERMS + MILITARY_TERMS + ["weather", "cloud"]
LOCATION_HINTS = [
    "vandenberg", "roswell", "wright patterson", "nellis", "groom lake", "oak ridge",
    "washington", "turkmenistan", "georgia", "syria", "iraq", "persian gulf",
    "arabian gulf", "mediterranean sea", "strait of hormuz", "low earth orbit", "moon",
]
TEXT_WEIGHT_WITH_TRANSFORMER = 0.60
DATE_WEIGHT = 0.15
ENTITY_WEIGHT_WITH_TRANSFORMER = 0.15
LOCATION_WEIGHT_WITH_TRANSFORMER = 0.10
TEXT_WEIGHT_WITHOUT_TRANSFORMER = 0.45
ENTITY_WEIGHT_WITHOUT_TRANSFORMER = 0.20
LOCATION_WEIGHT_WITHOUT_TRANSFORMER = 0.20


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def normalize_date(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).replace({"N/A": "", "nan": "", "None": ""})
    return pd.to_datetime(cleaned, errors="coerce", utc=False, format="mixed").dt.date.astype("string")


def parse_date_value(value: object, prefer_1900s_for_two_digit_year: bool = False) -> tuple[str, str]:
    raw = str(value).strip()
    if raw.lower() in {"", "nan", "none", "n/a", "na"}:
        return ("", "none")
    if re.fullmatch(r"\d{4}", raw):
        return (raw, "year")
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2})", raw)
    if match and prefer_1900s_for_two_digit_year:
        month, day, year = map(int, match.groups())
        year += 1900 if year >= 30 else 2000
        return (f"{year:04d}-{month:02d}-{day:02d}", "day")
    parsed = pd.to_datetime(raw, errors="coerce", format="mixed")
    if pd.isna(parsed):
        return ("", "none")
    return (str(parsed.date()), "day")


def load_kaggle(path: Path = DATA_RAW / "ufo" / "kaggle_ufo.csv") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=SCHEMA)
    df = pd.read_csv(path, low_memory=False)
    cols = {
        "date": first_existing_column(df, ["datetime", "date", "Date_time"]),
        "city": first_existing_column(df, ["city"]),
        "state": first_existing_column(df, ["state", "state/province"]),
        "country": first_existing_column(df, ["country"]),
        "latitude": first_existing_column(df, ["latitude"]),
        "longitude": first_existing_column(df, ["longitude"]),
        "location_text": first_existing_column(df, ["location", "city"]),
        "description_text": first_existing_column(df, ["comments", "description", "text"]),
        "object_shape": first_existing_column(df, ["shape", "UFO_shape"]),
        "duration": first_existing_column(df, ["duration (seconds)", "duration", "duration (hours/min)", "described_duration_of_encounter", "length_of_encounter_seconds"]),
    }
    out = pd.DataFrame(index=df.index)
    out["record_id"] = df.index.astype(str)
    out["source"] = "kaggle"
    for target, source in cols.items():
        out[target] = df[source] if source else ""
    out["date"] = normalize_date(out["date"])
    out["date_precision"] = "day"
    out["date_hint_start"] = pd.to_datetime(out["date"], errors="coerce").dt.year
    out["date_hint_end"] = out["date_hint_start"]
    out["text_kind"] = "eyewitness_report"
    out["extracted_text_path"] = ""
    out["source_file_or_link"] = str(path)
    return out[SCHEMA]


def load_pursue(path: Path = DATA_RAW / "ufo" / "pursue_metadata.csv") -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        try:
            df = pd.read_csv(PURSUE_MIRROR)
        except Exception:
            return pd.DataFrame(columns=SCHEMA)
    out = pd.DataFrame(index=df.index)
    title = first_existing_column(df, ["Title", "title"]) or df.columns[0]
    out["record_id"] = df[title].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    out["source"] = "pursue"
    desc_col = first_existing_column(df, ["Description Blurb", "Description", "Text"])
    desc = df[desc_col].astype(str) if desc_col else df[title].astype(str)
    incident_col = first_existing_column(df, ["Incident Date", "Date"])
    parsed_dates = (df[incident_col] if incident_col else pd.Series([""] * len(df), index=df.index)).map(
        lambda value: parse_date_value(value, prefer_1900s_for_two_digit_year=True)
    )
    out["date"] = parsed_dates.map(lambda item: item[0])
    out["date_precision"] = parsed_dates.map(lambda item: item[1])
    year_ranges = [
        years_in_text(date, record_id, description)
        for date, record_id, description in zip(out["date"], out["record_id"], desc)
    ]
    out["date_hint_start"] = [item[0] for item in year_ranges]
    out["date_hint_end"] = [item[1] for item in year_ranges]
    loc_col = first_existing_column(df, ["Incident Location", "Location"])
    out["location_text"] = df[loc_col].astype(str) if loc_col else ""
    out["city"] = ""
    out["state"] = ""
    out["country"] = "USA"
    out["latitude"] = np.nan
    out["longitude"] = np.nan
    out["description_text"] = desc
    out["extracted_text_path"] = ""
    duplicate_counts = out["description_text"].map(out["description_text"].value_counts())
    out["text_kind"] = np.where(duplicate_counts > 1, "metadata_repeated_summary", "metadata_summary")
    out["object_shape"] = out["description_text"].apply(infer_shape)
    out["duration"] = ""
    link_col = first_existing_column(df, ["PDF | Image Link", "Link", "source_file_or_link"])
    out["source_file_or_link"] = df[link_col].astype(str) if link_col else ""
    return out[SCHEMA]


def load_document_text_index(path: Path = DATA_PROCESSED / "pursue_document_text_index.csv") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df[df["text_length"].fillna(0).astype(int) > 0].copy()


def read_extracted_text(text_path: object) -> str:
    if not isinstance(text_path, str) or not text_path:
        return ""
    path = ROOT_SAFE_PATH(text_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def ROOT_SAFE_PATH(relative_path: str) -> Path:
    path = (DATA_RAW.parents[1] / relative_path).resolve()
    root = DATA_RAW.parents[1].resolve()
    if root not in path.parents and path != root:
        raise ValueError(f"Path escapes project root: {relative_path}")
    return path


def infer_location_from_text(text: str) -> str:
    lowered = clean_text(text).lower()
    hits = [hint for hint in LOCATION_HINTS if hint in lowered]
    return "; ".join(dict.fromkeys(hits[:5]))


def normalized_shapes(*texts: object) -> list[str]:
    shapes: list[str] = []
    for text in texts:
        tokens = tokenize(str(text))
        for token in tokens:
            canonical = SHAPE_CANONICAL.get(token)
            if canonical:
                shapes.append(canonical)
    return list(dict.fromkeys(shapes))


def normalize_shape_value(raw_shape: object, description: object = "") -> str:
    shapes = normalized_shapes(raw_shape, description)
    return "; ".join(shapes)


def attach_pursue_document_text(pursue: pd.DataFrame) -> pd.DataFrame:
    index = load_document_text_index()
    if pursue.empty or index.empty:
        return pursue
    docs = index.to_dict("records")
    updated = pursue.copy()
    for row_idx, row in updated.iterrows():
        keys = [
            compact_name(row.get("record_id", "")),
            compact_name(Path(str(row.get("source_file_or_link", ""))).name),
        ]
        best = None
        best_score = 0
        for doc in docs:
            doc_key = str(doc.get("compact_name", ""))
            scores = [SequenceMatcher(None, key, doc_key).ratio() for key in keys if key and doc_key]
            if not scores:
                continue
            score = max(scores)
            if score > best_score:
                best = doc
                best_score = score
        if best and best_score >= 0.78:
            text = read_extracted_text(best.get("text_path", ""))
            if text:
                updated.at[row_idx, "description_text"] = clean_text(text[:20000])
                updated.at[row_idx, "text_kind"] = "extracted_document_text"
                updated.at[row_idx, "extracted_text_path"] = best.get("text_path", "")
                if not clean_text(updated.at[row_idx, "location_text"]):
                    updated.at[row_idx, "location_text"] = infer_location_from_text(text)
    return updated


def infer_shape(text: str) -> str:
    return "; ".join(normalized_shapes(text))


def bigram_counts(texts: pd.Series, n: int = 40) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for text in texts.fillna("").astype(str):
        words = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]
        counts.update(" ".join(pair) for pair in zip(words, words[1:]))
    return pd.DataFrame(counts.most_common(n), columns=["phrase", "count"])


def entity_hits(text: str) -> list[str]:
    tokens = set(tokenize(text))
    hits = sorted(tokens & set(ENTITY_TERMS))
    years = sorted(set(re.findall(r"\b(?:19[4-9]\d|20[0-2]\d)\b", str(text))))
    return hits + [f"YEAR_{year}" for year in years[:5]]


def extract_named_entities(row: pd.Series) -> list[dict[str, str]]:
    text = str(row.get("description_text", ""))
    lowered = clean_text(text).lower()
    entities: list[dict[str, str]] = []

    def add(label: str, value: object, method: str) -> None:
        value_text = clean_text(value)
        if value_text and value_text.lower() not in {"nan", "none", "n/a", "na"}:
            entities.append({
                "source": str(row.get("source", "")),
                "record_id": str(row.get("record_id", "")),
                "entity_label": label,
                "entity_text": value_text,
                "method": method,
            })

    for field, label in [("city", "GPE"), ("state", "GPE"), ("country", "GPE"), ("location_text", "LOC")]:
        add(label, row.get(field, ""), f"schema_{field}")
    for date_text in re.findall(r"\b(?:\d{4}-\d{2}-\d{2}|19[4-9]\d|20[0-2]\d)\b", text):
        add("DATE", date_text, "regex_date")
    for hint in LOCATION_HINTS:
        if hint in lowered:
            add("LOC", hint, "location_hint")
    for term in MILITARY_TERMS:
        if term in lowered:
            label = "ORG" if term in {"fbi", "nasa", "cia", "faa"} else "MILITARY"
            add(label, term, "domain_lexicon")
    for shape in normalized_shapes(row.get("object_shape", ""), text):
        add("OBJECT_SHAPE", shape, "shape_lexicon")
    for color in COLOR_TERMS:
        if re.search(rf"\b{re.escape(color)}\b", lowered):
            add("COLOR", color, "color_lexicon")
    for motion in MOTION_TERMS:
        if re.search(rf"\b{re.escape(motion)}\b", lowered):
            add("MOTION", motion, "motion_lexicon")
    return entities


def tfidf_similarity(a: str, b: str) -> float:
    if not has_usable_text(a) or not has_usable_text(b):
        return 0.0
    docs = []
    for text in [a, b]:
        words = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]
        bigrams = [" ".join(pair) for pair in zip(words, words[1:])]
        docs.append(Counter(words + bigrams))
    if not docs[0] or not docs[1]:
        return 0.0
    terms = set(docs[0]) | set(docs[1])
    df = {term: int(term in docs[0]) + int(term in docs[1]) for term in terms}
    vectors = []
    for doc in docs:
        total = sum(doc.values()) or 1
        vector = {}
        for term, count in doc.items():
            idf = math.log((1 + len(docs)) / (1 + df[term])) + 1
            vector[term] = (count / total) * idf
        vectors.append(vector)
    dot = sum(vectors[0].get(term, 0.0) * vectors[1].get(term, 0.0) for term in terms)
    norm_a = math.sqrt(sum(value * value for value in vectors[0].values()))
    norm_b = math.sqrt(sum(value * value for value in vectors[1].values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def unified_table() -> pd.DataFrame:
    ensure_dirs()
    pursue = attach_pursue_document_text(load_pursue())
    frames = [frame for frame in [load_kaggle(), pursue] if not frame.empty]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=SCHEMA)
    for col in SCHEMA:
        if col not in df:
            df[col] = ""
    df["description_text"] = df["description_text"].fillna("").map(clean_text)
    df["location_text"] = df["location_text"].fillna("").map(clean_text)
    df["object_shape"] = df.apply(
        lambda row: normalize_shape_value(row.get("object_shape", ""), row.get("description_text", "")),
        axis=1,
    )
    df.to_csv(DATA_PROCESSED / "ufo_unified.csv", index=False)
    return df


def text_similarity(a: str, b: str) -> float:
    a_tokens = set(t for t in tokenize(a) if t not in STOPWORDS)
    b_tokens = set(t for t in tokenize(b) if t not in STOPWORDS)
    if not a_tokens or not b_tokens:
        return 0.0
    jaccard = len(a_tokens & b_tokens) / len(a_tokens | b_tokens)
    seq = SequenceMatcher(None, clean_text(a).lower(), clean_text(b).lower()).ratio()
    return 0.65 * jaccard + 0.35 * seq


def write_leaflet_geo_map(df: pd.DataFrame, path: Path = FIGURES / "ufo_geographic_map.html") -> None:
    points = df[
        (df["source"] == "kaggle")
        & pd.to_numeric(df["latitude"], errors="coerce").notna()
        & pd.to_numeric(df["longitude"], errors="coerce").notna()
    ].copy()
    if points.empty:
        path.write_text("<html><body><p>No geocoded UFO points available.</p></body></html>", encoding="utf-8")
        return
    points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
    points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
    points["year"] = pd.to_datetime(points["date"], errors="coerce").dt.year
    sample = points.sample(min(len(points), 1200), random_state=7)
    markers = []
    for _, row in sample.iterrows():
        label = escape(
            f"{row.get('date', '')} | {row.get('location_text', '')} | "
            f"{row.get('object_shape', '') or 'unknown'}"
        )
        markers.append(
            f"L.circleMarker([{float(row['latitude']):.6f}, {float(row['longitude']):.6f}], "
            "{radius: 3, color: '#2563eb', fillColor: '#60a5fa', fillOpacity: 0.55, weight: 1}"
            f").bindPopup({label!r}).addTo(markers);"
        )
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>UFO Geographic Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; }}
    #map {{ height: 92vh; }}
    .note {{ padding: 8px 12px; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="note">Sampled {len(sample):,} geocoded Kaggle UFO records from {len(points):,} available points. PURSUE records are not mapped when locations are missing, broad, or non-terrestrial.</div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([39.5, -98.35], 4);
    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);
    const markers = L.layerGroup().addTo(map);
    {' '.join(markers)}
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def candidate_snippet(document_text: str, query_text: str, max_chars: int = 450) -> str:
    text = clean_text(document_text)
    if len(text) <= max_chars:
        return text
    query_tokens = token_set(query_text) | entity_set(query_text)
    if not query_tokens:
        return text[:max_chars]
    windows = re.split(r"(?<=[.!?])\s+", text)
    best_score = -1
    best_idx = 0
    for idx, window in enumerate(windows[:2000]):
        tokens = token_set(window) | entity_set(window)
        score = len(tokens & query_tokens)
        if score > best_score:
            best_score = score
            best_idx = idx
    snippet = " ".join(windows[max(0, best_idx - 1): best_idx + 2])
    return snippet[:max_chars]


def full_text_for_embedding(row: pd.Series) -> str:
    path_value = row.get("extracted_text_path", "")
    if isinstance(path_value, str) and path_value:
        try:
            text = read_extracted_text(path_value)
            if text:
                return text
        except Exception:
            pass
    return str(row.get("description_text", ""))


def has_usable_text(value: object) -> bool:
    text = clean_text(value).lower()
    return bool(text) and text not in {"nan", "none", "n/a", "na"}


def prepare_semantic_context(kaggle: pd.DataFrame, pursue: pd.DataFrame) -> dict:
    enabled = str(os.environ.get("UFO_USE_TRANSFORMERS", "1")).lower() not in {"0", "false", "no"}
    context = {"available": False, "error": ""}
    if not enabled:
        context["error"] = "UFO_USE_TRANSFORMERS disabled"
        return context

    embedder = SemanticEmbedder()
    usable_kaggle = kaggle[kaggle["description_text"].map(has_usable_text)]
    kaggle_ids = usable_kaggle.index.astype(str).tolist()
    kaggle_texts = usable_kaggle["description_text"].fillna("").astype(str).tolist()
    try:
        kaggle_encoded = embedder.encode_cached("kaggle_descriptions", kaggle_ids, kaggle_texts)
    except Exception as exc:
        context["error"] = str(exc)
        return context
    kaggle_pos = {int(item_id): pos for pos, item_id in enumerate(kaggle_encoded.ids)}

    chunk_ids: list[str] = []
    chunk_texts: list[str] = []
    pursue_chunk_positions: dict[int, list[int]] = {}
    for row_idx, row in pursue.iterrows():
        text = full_text_for_embedding(row)
        chunks = chunk_text(text)
        if not chunks and has_usable_text(row.get("description_text", "")):
            chunks = [str(row.get("description_text", ""))]
        if not chunks:
            pursue_chunk_positions[int(row_idx)] = []
            continue
        positions: list[int] = []
        for chunk_no, chunk in enumerate(chunks):
            positions.append(len(chunk_ids))
            chunk_ids.append(f"{row_idx}:{chunk_no}")
            chunk_texts.append(chunk)
        pursue_chunk_positions[int(row_idx)] = positions
    try:
        chunk_encoded = embedder.encode_cached("pursue_chunks", chunk_ids, chunk_texts)
    except Exception as exc:
        context["error"] = str(exc)
        return context

    return {
        "available": True,
        "error": "",
        "model_name": embedder.model_name,
        "kaggle_embeddings": kaggle_encoded.embeddings,
        "kaggle_pos": kaggle_pos,
        "pursue_embeddings": chunk_encoded.embeddings,
        "pursue_chunk_texts": chunk_encoded.texts,
        "pursue_chunk_positions": pursue_chunk_positions,
    }


def semantic_block_scores(context: dict, block_indices: list[int], pursue_idx: int) -> tuple[dict[int, float], dict[int, str]]:
    if not context.get("available") or not block_indices:
        return {}, {}
    k_positions = [context["kaggle_pos"][int(idx)] for idx in block_indices if int(idx) in context["kaggle_pos"]]
    valid_indices = [int(idx) for idx in block_indices if int(idx) in context["kaggle_pos"]]
    p_positions = context["pursue_chunk_positions"].get(int(pursue_idx), [])
    if not k_positions or not p_positions:
        return {}, {}
    k_matrix = context["kaggle_embeddings"][k_positions]
    p_matrix = context["pursue_embeddings"][p_positions]
    score_matrix = np.maximum(k_matrix @ p_matrix.T, 0.0)
    best_chunk_offsets = score_matrix.argmax(axis=1)
    best_scores = score_matrix.max(axis=1)
    scores: dict[int, float] = {}
    snippets: dict[int, str] = {}
    for idx, score, chunk_offset in zip(valid_indices, best_scores, best_chunk_offsets):
        chunk_position = p_positions[int(chunk_offset)]
        scores[idx] = float(score)
        snippets[idx] = context["pursue_chunk_texts"][chunk_position][:450]
    return scores, snippets


LIKELY_SHARE = 0.03
POSSIBLE_SHARE = 0.32
MAX_EXPORTED_CANDIDATES = 500


def validation_notes(row: pd.Series, label: str) -> str:
    text = float(row.get("text_similarity", 0) or 0)
    entity = float(row.get("entity_similarity", 0) or 0)
    date = pd.to_numeric(row.get("date_similarity", np.nan), errors="coerce")
    loc = pd.to_numeric(row.get("location_similarity", np.nan), errors="coerce")
    text_kind = str(row.get("pursue_text_kind", ""))
    percentile = pd.to_numeric(row.get("score_percentile", 0), errors="coerce")

    weak_reasons = []
    strong_reasons = []
    if label == "likely same event":
        strong_reasons.append(f"top {LIKELY_SHARE:.0%} of exported candidates by final score")
    elif label == "possibly same event":
        strong_reasons.append(f"next {POSSIBLE_SHARE:.0%} of exported candidates by final score")
    else:
        weak_reasons.append("lower-ranked candidate relative to exported matches")
    if text_kind == "extracted_document_text":
        strong_reasons.append("uses extracted official document text")
    if pd.notna(date) and date >= 0.9:
        strong_reasons.append("date is exact or within a few days")
    elif pd.notna(date) and date >= 0.45:
        strong_reasons.append("date is in a moderately close window")
    elif pd.isna(date):
        weak_reasons.append("official date is missing or only inferred")
    else:
        weak_reasons.append("date support is weak")
    if pd.notna(loc) and loc >= 0.45:
        strong_reasons.append("location text has moderate overlap")
    elif pd.isna(loc):
        weak_reasons.append("official location was not usable")
    if text < 0.08:
        weak_reasons.append("direct text similarity is low")
    if entity >= 0.5:
        strong_reasons.append("entity/keyword overlap is meaningful")
    if pd.notna(percentile):
        strong_reasons.append(f"score percentile {percentile:.3f}")
    return "; ".join(strong_reasons + weak_reasons)


def assign_relative_validation_labels(out: pd.DataFrame) -> pd.DataFrame:
    if out.empty:
        return out
    labeled = out.copy()
    n = len(labeled)
    likely_count = max(1, round(n * LIKELY_SHARE))
    possible_count = max(1, round(n * POSSIBLE_SHARE))
    likely_count = min(likely_count, n)
    possible_count = min(possible_count, n - likely_count)
    labels = (
        ["likely same event"] * likely_count
        + ["possibly same event"] * possible_count
        + ["probably not same event"] * (n - likely_count - possible_count)
    )
    labeled["manual_label"] = labels
    labeled["manual_notes"] = [
        validation_notes(row, label)
        for (_, row), label in zip(labeled.iterrows(), labels)
    ]
    return labeled


def validation_label(row: pd.Series) -> tuple[str, str]:
    label = str(row.get("manual_label", "probably not same event"))
    return label, validation_notes(row, label)


def date_similarity(a: str, b: str, b_precision: str = "day") -> float:
    da = pd.to_datetime(a, errors="coerce")
    if str(b_precision) == "year" and re.fullmatch(r"\d{4}", str(b)):
        db_year = int(str(b))
        if pd.isna(da):
            return np.nan
        diff = abs(int(da.year) - db_year)
        if diff == 0:
            return 0.35
        if diff == 1:
            return 0.15
        return 0.0
    db = pd.to_datetime(b, errors="coerce")
    if pd.isna(da) or pd.isna(db):
        return np.nan
    days = abs((da - db).days)
    if days == 0:
        return 1.0
    if days <= 1:
        return 0.95
    if days <= 3:
        return 0.9
    if days <= 7:
        return 0.82
    if days <= 14:
        return 0.72
    if days <= 30:
        return 0.62
    if days <= 90:
        return 0.45
    if days <= 180:
        return 0.32
    if days <= 365:
        return 0.18
    return 0.0


def clean_location_value(value: object) -> str:
    text = clean_text(value).lower()
    if text in {"", "nan", "none", "n/a", "na"}:
        return ""
    return text


def reliable_pursue_location(value: object) -> bool:
    loc = clean_location_value(value)
    if not loc:
        return False
    unavailable = {"moon", "low earth orbit", "earth orbit", "space"}
    too_broad = {"united states", "western united states", "middle east"}
    return loc not in unavailable and loc not in too_broad


def location_similarity(a: pd.Series, b: pd.Series) -> float:
    if b.get("source") == "pursue" and not reliable_pursue_location(b.get("location_text", "")):
        return np.nan
    loc_a = " ".join(str(a.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
    loc_b = " ".join(str(b.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
    if not clean_location_value(loc_a) or not clean_location_value(loc_b):
        return np.nan
    ratio = SequenceMatcher(None, clean_text(loc_a), clean_text(loc_b)).ratio()
    try:
        lat1, lon1, lat2, lon2 = map(float, [a["latitude"], a["longitude"], b["latitude"], b["longitude"]])
        if all(math.isfinite(x) for x in [lat1, lon1, lat2, lon2]):
            distance = haversine_km(lat1, lon1, lat2, lon2)
            geo = max(0.0, 1.0 - distance / 500.0)
            return max(ratio, geo)
    except Exception:
        pass
    return ratio


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def entity_similarity(a: str, b: str) -> float:
    ea = set(tokenize(a)) & set(ENTITY_TERMS)
    eb = set(tokenize(b)) & set(ENTITY_TERMS)
    if not ea and not eb:
        return 0.1
    if not ea or not eb:
        return 0.0
    return len(ea & eb) / len(ea | eb)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def token_set(text: str) -> set[str]:
    return {t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2}


def entity_set(text: str) -> set[str]:
    return set(tokenize(text)) & set(ENTITY_TERMS)


def date_or_range_similarity(k_date: str, p_date: str, p_precision: str, p_year_min: float, p_year_max: float) -> float:
    direct = date_similarity(k_date, p_date, p_precision)
    if pd.notna(direct):
        return direct
    k_year = pd.to_datetime(k_date, errors="coerce").year
    if pd.isna(k_year) or pd.isna(p_year_min) or pd.isna(p_year_max):
        return np.nan
    if p_year_min <= k_year <= p_year_max:
        return 0.20
    if p_year_min - 1 <= k_year <= p_year_max + 1:
        return 0.10
    return 0.0


def weighted_score(
    transformer_score: float,
    lexical_score: float,
    tfidf_score: float,
    location_score: float,
    date_score: float,
    entity_score: float,
    text_kind: str,
) -> tuple[float, str]:
    if pd.notna(transformer_score):
        components = [
            ("transformer_text", transformer_score, 0.45),
            ("lexical_text", lexical_score, 0.05),
            ("tfidf_text", tfidf_score, 0.10),
            ("date", date_score, DATE_WEIGHT),
            ("entity", entity_score, ENTITY_WEIGHT_WITH_TRANSFORMER),
        ]
        location_weight = LOCATION_WEIGHT_WITH_TRANSFORMER
    else:
        components = [
            ("lexical_text", lexical_score, 0.20),
            ("tfidf_text", tfidf_score, 0.25),
            ("date", date_score, DATE_WEIGHT),
            ("entity", entity_score, ENTITY_WEIGHT_WITHOUT_TRANSFORMER),
        ]
        location_weight = LOCATION_WEIGHT_WITHOUT_TRANSFORMER
    if pd.notna(location_score):
        components.append(("location", location_score, location_weight))
    available = [(name, score, weight) for name, score, weight in components if pd.notna(score)]
    if not available:
        return (0.0, "No reliable scoring signals.")
    total_weight = sum(weight for _, _, weight in available)
    score = sum(score * weight for _, score, weight in available) / total_weight
    notes = [f"used {', '.join(name for name, _, _ in available)}"]
    if pd.isna(location_score):
        notes.append("location ignored because PURSUE location is missing, non-terrestrial, or too broad")
    if str(text_kind) == "metadata_repeated_summary":
        score *= 0.72
        notes.append("penalized repeated PURSUE metadata summary")
    elif str(text_kind) == "metadata_summary":
        score *= 0.88
        notes.append("PURSUE text is metadata summary, not extracted document text")
    return (score, "; ".join(notes))


def years_in_text(*texts: str) -> tuple[float, float]:
    years: list[int] = []
    for text in texts:
        for match in re.findall(r"\b(19[4-9]\d|20[0-2]\d)\b", str(text)):
            years.append(int(match))
    if not years:
        return (np.nan, np.nan)
    return (min(years), max(years))


def candidate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    kaggle = df[df["source"] == "kaggle"].copy()
    pursue = df[df["source"] == "pursue"].copy()
    if kaggle.empty or pursue.empty:
        empty = pd.DataFrame(columns=[
            "candidate_rank", "score_percentile",
            "kaggle_record_id", "pursue_record_id", "kaggle_date", "pursue_date",
            "pursue_date_precision", "pursue_date_hint_start", "pursue_date_hint_end",
            "kaggle_location", "pursue_location", "kaggle_text", "pursue_text",
            "pursue_text_kind", "kaggle_source_file_or_link", "pursue_source_file_or_link", "pursue_extracted_text_path",
            "transformer_similarity", "lexical_text_similarity", "tfidf_text_similarity", "text_similarity",
            "location_similarity", "date_similarity",
            "entity_similarity", "final_score", "match_explanation",
            "manual_label", "manual_notes",
        ])
        empty.drop(columns=["manual_label", "manual_notes"]).to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
        empty.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
        return pd.DataFrame()
    rows = []
    kaggle = kaggle[kaggle["description_text"].map(has_usable_text)].copy()
    pursue = pursue[pursue["description_text"].map(has_usable_text)].copy()
    kaggle["year"] = pd.to_datetime(kaggle["date"], errors="coerce").dt.year
    kaggle["tokens"] = kaggle["description_text"].map(token_set)
    kaggle["entities"] = kaggle["description_text"].map(entity_set)
    pursue["year"] = pd.to_datetime(pursue["date"], errors="coerce").dt.year
    pursue["tokens"] = pursue["description_text"].map(token_set)
    pursue["entities"] = pursue["description_text"].map(entity_set)
    semantic_context = prepare_semantic_context(kaggle, pursue)
    year_ranges = pursue.apply(
        lambda r: years_in_text(r.get("date", ""), r.get("record_id", ""), r.get("description_text", "")),
        axis=1,
        result_type="expand",
    )
    pursue["year_min"] = year_ranges[0]
    pursue["year_max"] = year_ranges[1]
    for _, p in pursue.iterrows():
        if semantic_context.get("available"):
            block = kaggle
        elif pd.notna(p["year"]):
            block = kaggle[abs(kaggle["year"] - p["year"]) <= 1]
        elif pd.notna(p["year_min"]) and pd.notna(p["year_max"]):
            block = kaggle[(p["year_min"] - 1 <= kaggle["year"]) & (kaggle["year"] <= p["year_max"] + 1)]
        else:
            block = kaggle
        if block.empty:
            continue
        if not semantic_context.get("available") and p["entities"] and len(block) > 5000:
            block = block[block["entities"].map(lambda ents: bool(ents & p["entities"]))]
        if not semantic_context.get("available") and len(block) > 3000:
            block = block.sample(3000, random_state=7)
        block_indices = [int(idx) for idx in block.index]
        semantic_scores, semantic_snippets = semantic_block_scores(semantic_context, block_indices, int(p.name))

        cheap_candidates = []
        if semantic_context.get("available"):
            for idx, sem_for_rank in sorted(semantic_scores.items(), key=lambda item: item[1], reverse=True)[:120]:
                if sem_for_rank >= 0.12:
                    cheap_candidates.append((sem_for_rank, idx))
        else:
            for idx, k in block.iterrows():
                ent = jaccard(k["entities"], p["entities"])
                txt_cheap = jaccard(k["tokens"], p["tokens"])
                dat_cheap = date_or_range_similarity(k["date"], p["date"], p["date_precision"], p["year_min"], p["year_max"])
                dat_for_rank = 0.0 if pd.isna(dat_cheap) else dat_cheap
                cheap = 0.55 * txt_cheap + 0.25 * ent + 0.20 * dat_for_rank
                if cheap >= 0.025:
                    cheap_candidates.append((cheap, idx))
        for _, idx in sorted(cheap_candidates, reverse=True)[:40]:
            k = kaggle.loc[idx]
            transformer_score = semantic_scores.get(int(idx), np.nan)
            p_snippet = semantic_snippets.get(int(idx)) or candidate_snippet(p["description_text"], k["description_text"])
            ent = jaccard(k["entities"], p["entities"])
            dat = date_or_range_similarity(k["date"], p["date"], p["date_precision"], p["year_min"], p["year_max"])
            lexical = text_similarity(k["description_text"], p_snippet)
            tfidf = tfidf_similarity(k["description_text"], p_snippet)
            loc = location_similarity(k, p)
            final, scoring_notes = weighted_score(transformer_score, lexical, tfidf, loc, dat, ent, p["text_kind"])
            if final >= 0.25:
                rows.append({
                    "kaggle_record_id": k["record_id"],
                    "pursue_record_id": p["record_id"],
                    "kaggle_date": k["date"],
                    "pursue_date": p["date"],
                    "pursue_date_precision": p["date_precision"],
                    "pursue_date_hint_start": p["date_hint_start"],
                    "pursue_date_hint_end": p["date_hint_end"],
                    "kaggle_location": k["location_text"] or f"{k['city']} {k['state']} {k['country']}",
                    "pursue_location": p["location_text"],
                    "kaggle_text": k["description_text"][:350],
                    "pursue_text": p_snippet,
                    "pursue_text_kind": p["text_kind"],
                    "kaggle_source_file_or_link": k["source_file_or_link"],
                    "pursue_source_file_or_link": p["source_file_or_link"],
                    "pursue_extracted_text_path": p["extracted_text_path"],
                    "transformer_similarity": "" if pd.isna(transformer_score) else round(transformer_score, 4),
                    "lexical_text_similarity": round(lexical, 4),
                    "tfidf_text_similarity": round(tfidf, 4),
                    "text_similarity": round(transformer_score, 4) if pd.notna(transformer_score) else round(lexical, 4),
                    "location_similarity": "" if pd.isna(loc) else round(loc, 4),
                    "date_similarity": "" if pd.isna(dat) else round(dat, 4),
                    "entity_similarity": round(ent, 4),
                    "final_score": round(final, 4),
                    "match_explanation": scoring_notes,
                })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("final_score", ascending=False).head(MAX_EXPORTED_CANDIDATES).reset_index(drop=True)
        out.insert(0, "candidate_rank", range(1, len(out) + 1))
        denominator = max(len(out) - 1, 1)
        out.insert(1, "score_percentile", [round(1 - (rank - 1) / denominator, 4) for rank in out["candidate_rank"]])
        out = assign_relative_validation_labels(out)
    out.to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
    manual = out.head(20).copy()
    manual.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
    manual.to_csv(REPORTS / "ufo_manual_validation_completed.csv", index=False)
    write_manual_review_helper(manual)
    return out


def write_manual_review_helper(manual: pd.DataFrame) -> None:
    helper_path = REPORTS / "ufo_top20_manual_review_helper.csv"
    md_path = REPORTS / "ufo_top20_manual_review_helper.md"
    if manual.empty:
        pd.DataFrame().to_csv(helper_path, index=False)
        md_path.write_text("# UFO Top 20 Manual Review Helper\n\nNo candidates available.\n", encoding="utf-8")
        return
    helper = manual.copy()
    helper["review_kaggle_row_hint"] = helper["kaggle_record_id"].map(
        lambda value: f"Open data/processed/ufo_unified.csv and filter source=kaggle, record_id={value}"
    )
    helper["review_pursue_row_hint"] = helper["pursue_record_id"].map(
        lambda value: f"Open data/processed/ufo_unified.csv and filter source=pursue, record_id={value}"
    )
    helper["review_questions"] = (
        "1. Are the event dates truly event dates? "
        "2. Are locations compatible or only broad metadata? "
        "3. Do shape/color/motion/witness details match? "
        "4. Is the official snippet a single event or a broad collection? "
        "5. Would you keep or change the automated label?"
    )
    helper.to_csv(helper_path, index=False)
    lines = [
        "# UFO Top 20 Manual Review Helper",
        "",
        "Use this after the automated scoring changes are finalized. The CSV version contains the full fields plus review prompts.",
        "",
        "Checklist for each pair:",
        "",
        "- Confirm whether both dates are event dates, not release or administrative dates.",
        "- Compare location specificity and treat broad official locations cautiously.",
        "- Compare shape, color, motion, witness type, aircraft/base/radar terms, and number of objects.",
        "- Decide whether the PURSUE snippet is a single incident or a broad document collection.",
        "- Edit `manual_label` and `manual_notes` in `ufo_manual_validation_completed.csv` if your judgment differs.",
        "",
        "## Top 20",
    ]
    for _, row in helper.iterrows():
        lines.extend([
            "",
            f"### Rank {row['candidate_rank']}: Kaggle {row['kaggle_record_id']} vs PURSUE {row['pursue_record_id']}",
            "",
            f"- Automated label: `{row['manual_label']}`",
            f"- Final score: `{row['final_score']}`",
            f"- Dates: Kaggle `{row['kaggle_date']}` vs PURSUE `{row['pursue_date']}`",
            f"- Locations: Kaggle `{row['kaggle_location']}` vs PURSUE `{row['pursue_location']}`",
            f"- Source link/file: `{row.get('pursue_source_file_or_link', '')}`",
            f"- Extracted text path: `{row.get('pursue_extracted_text_path', '')}`",
            f"- Automated reason: {row['manual_notes']}",
        ])
    md_path.write_text("\n".join(lines), encoding="utf-8")


def explore(df: pd.DataFrame) -> None:
    terms = top_terms(df["description_text"], STOPWORDS, 30)
    terms.to_csv(DATA_PROCESSED / "ufo_top_terms.csv", index=False)
    save_bar(terms.head(20), "term", "count", "UFO/UAP Top Description Terms", FIGURES / "ufo_top_terms.png")

    phrases = bigram_counts(df["description_text"], 50)
    phrases.to_csv(DATA_PROCESSED / "ufo_common_phrases.csv", index=False)

    shape_rows = []
    for shape_text in df["object_shape"].fillna("").astype(str):
        for shape in re.split(r"[;,/ ]+", shape_text.lower()):
            if shape in SHAPE_TERMS:
                shape_rows.append(shape)
    shapes = pd.Series(shape_rows).value_counts().rename_axis("shape").reset_index(name="count")
    shapes.to_csv(DATA_PROCESSED / "ufo_shape_counts.csv", index=False)
    save_bar(shapes.head(20), "shape", "count", "Common UFO/UAP Shapes", FIGURES / "ufo_shapes.png")

    by_source = df.groupby("source").size().reset_index(name="records")
    save_bar(by_source, "source", "records", "Records by Source", FIGURES / "ufo_records_by_source.png", rotate=0)

    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    years = df.dropna(subset=["year"]).groupby(["year", "source"]).size().reset_index(name="records")
    years.to_csv(DATA_PROCESSED / "ufo_temporal_trends.csv", index=False)
    if not years.empty:
        pivot = years.pivot_table(index="year", columns="source", values="records", fill_value=0)
        fig, ax = plt.subplots(figsize=(11, 5))
        pivot.plot(ax=ax)
        ax.set_title("UFO/UAP Records by Year and Source")
        ax.set_xlabel("Year")
        ax.set_ylabel("Records")
        fig.tight_layout()
        fig.savefig(FIGURES / "ufo_temporal_trends.png", dpi=160)
        plt.close(fig)

    entity_rows = []
    ner_rows = []
    for _, row in df.iterrows():
        for entity in entity_hits(row["description_text"]):
            entity_rows.append({"source": row["source"], "entity": entity})
        ner_rows.extend(extract_named_entities(row))
    entities = pd.DataFrame(entity_rows)
    if not entities.empty:
        entity_counts = entities.groupby(["source", "entity"]).size().reset_index(name="count").sort_values("count", ascending=False)
    else:
        entity_counts = pd.DataFrame(columns=["source", "entity", "count"])
    entity_counts.to_csv(DATA_PROCESSED / "ufo_entity_counts_by_source.csv", index=False)
    ner_entities = pd.DataFrame(ner_rows)
    if ner_entities.empty:
        ner_entities = pd.DataFrame(columns=["source", "record_id", "entity_label", "entity_text", "method"])
    ner_entities.to_csv(DATA_PROCESSED / "ufo_ner_entities.csv", index=False)
    ner_summary = (
        ner_entities.groupby(["source", "entity_label", "entity_text"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        if not ner_entities.empty
        else pd.DataFrame(columns=["source", "entity_label", "entity_text", "count"])
    )
    ner_summary.to_csv(DATA_PROCESSED / "ufo_ner_summary.csv", index=False)

    language_rows = []
    for source in sorted(df["source"].dropna().unique()):
        source_terms = top_terms(df[df["source"] == source]["description_text"], STOPWORDS, 80)
        source_terms["source"] = source
        language_rows.append(source_terms)
    language = pd.concat(language_rows, ignore_index=True) if language_rows else pd.DataFrame(columns=["term", "count", "source"])
    language.to_csv(DATA_PROCESSED / "ufo_source_language_comparison.csv", index=False)

    country_counts = df[df["source"] == "kaggle"]["country"].fillna("unknown").replace("", "unknown").value_counts().head(20)
    geo = country_counts.rename_axis("country").reset_index(name="records")
    geo.to_csv(DATA_PROCESSED / "ufo_geographic_trends.csv", index=False)
    save_bar(geo.head(12), "country", "records", "Kaggle UFO Records by Country", FIGURES / "ufo_geographic_trends.png")
    write_leaflet_geo_map(df)

    rare_shapes = df[df["source"] == "kaggle"].copy()
    shape_freq = rare_shapes["object_shape"].fillna("unknown").replace("", "unknown").value_counts()
    rare_shapes["shape_count"] = rare_shapes["object_shape"].map(shape_freq).fillna(0)
    rare = rare_shapes.sort_values(["shape_count", "date"]).head(50)[
        ["record_id", "date", "city", "state", "country", "object_shape", "description_text", "shape_count"]
    ]
    rare.to_csv(DATA_PROCESSED / "ufo_rare_sightings.csv", index=False)


def write_report(df: pd.DataFrame, matches: pd.DataFrame) -> None:
    pursue = df[df["source"] == "pursue"]
    text_counts = pursue["text_kind"].value_counts().to_dict() if "text_kind" in pursue else {}
    extracted_count = int(text_counts.get("extracted_document_text", 0))
    metadata_count = int(len(pursue) - extracted_count)
    validation_path = REPORTS / "ufo_manual_validation_completed.csv"
    validation = pd.read_csv(validation_path) if validation_path.exists() else pd.DataFrame()
    all_validation = matches if not matches.empty and "manual_label" in matches else pd.DataFrame()
    label_counts = validation["manual_label"].value_counts().to_dict() if not validation.empty else {}
    all_label_counts = all_validation["manual_label"].value_counts().to_dict() if not all_validation.empty else {}
    transformer_active = (
        not matches.empty
        and "transformer_similarity" in matches
        and pd.to_numeric(matches["transformer_similarity"], errors="coerce").notna().any()
    )
    lines = [
        "# UFO/UAP Report Draft",
        "",
        f"Unified records loaded: {len(df)}.",
        f"Kaggle records: {len(df[df['source'] == 'kaggle'])}. PURSUE records: {len(df[df['source'] == 'pursue'])}.",
        f"PURSUE rows with extracted document text: {extracted_count}. Metadata-only PURSUE rows: {metadata_count}.",
        f"Transformer similarity active for this run: {transformer_active}.",
        "",
        "## Matching Method",
        "Candidate retrieval uses broad transformer-based semantic retrieval when embeddings are available, rather than strict date/location blocking. Date and location are weak or missing in many PURSUE records, so they are used as scoring evidence after retrieval instead of hard filters. If transformer embeddings are unavailable, the fallback path still uses year/entity blocking to avoid an all-pairs comparison.",
        "",
        "The base signals are transformer text similarity, TF-IDF text similarity, lexical text similarity, date, location, and entity/NER-style overlap. When `sentence-transformers` is installed, transformer cosine similarity is the primary text signal and TF-IDF/lexical overlap are secondary. If the transformer dependency is unavailable, the pipeline falls back to TF-IDF and lexical text similarity. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.",
        "",
        f"Current transformer weights are text {TEXT_WEIGHT_WITH_TRANSFORMER:.2f}, date {DATE_WEIGHT:.2f}, entity {ENTITY_WEIGHT_WITH_TRANSFORMER:.2f}, and location {LOCATION_WEIGHT_WITH_TRANSFORMER:.2f}. Date weight was deliberately reduced because PURSUE dates are often missing, broad, title-derived, or document/admin dates rather than confidently verified event dates.",
        "",
        "Rows with empty Kaggle text or empty official snippets are excluded from semantic candidate matching so identical empty embeddings cannot create false high-similarity pairs.",
        "",
        "Date similarity is based on absolute day distance, so cross-year near misses such as December 31 versus January 2 are still treated as close. Full-date gaps use tiers from exact day through 365 days; year-only official dates use a weaker same-year/plus-minus-one-year fallback.",
        "",
        f"Validation labels are relative rank bands over the exported candidate pool: top {LIKELY_SHARE:.0%} `likely same event`, next {POSSIBLE_SHARE:.0%} `possibly same event`, and the remainder `probably not same event`. These labels do not mean confirmed identity.",
        "",
        "## Candidate Matches",
    ]
    if matches.empty:
        lines.append("No candidate matches were generated. Check whether both Kaggle and PURSUE inputs are available.")
    else:
        lines.append("Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.")
        lines.append("All exported candidates include formula labels and notes.")
        lines.append(f"Validation labels among all exported candidates: {all_label_counts}.")
        lines.append("The top-20 manual-review working file is `outputs/reports/ufo_manual_validation_completed.csv`.")
        lines.append(f"Validation labels among top 20: {label_counts}.")
    lines.extend([
        "",
        "## Exploration Outputs",
        "- Common terms: `data/processed/ufo_top_terms.csv`.",
        "- Common phrases: `data/processed/ufo_common_phrases.csv`.",
        "- Entity/keyword counts by source: `data/processed/ufo_entity_counts_by_source.csv`.",
        "- Rule-based NER-style entities: `data/processed/ufo_ner_entities.csv` and `data/processed/ufo_ner_summary.csv`.",
        "- Civilian vs official language comparison: `data/processed/ufo_source_language_comparison.csv`.",
        "- Temporal trends: `data/processed/ufo_temporal_trends.csv`.",
        "- Geographic trends: `data/processed/ufo_geographic_trends.csv`.",
        "- Interactive geographic map: `outputs/figures/ufo_geographic_map.html`.",
        "- Rare sightings: `data/processed/ufo_rare_sightings.csv`.",
        "",
        "## Validation Examples",
    ])
    if validation.empty:
        lines.append("No validation rows are available.")
    else:
        example_rows = []
        for label in ["possibly same event", "probably not same event", "likely same event"]:
            subset = validation[validation["manual_label"] == label].head(3)
            example_rows.extend([row for _, row in subset.iterrows()])
        for row in example_rows[:5]:
            lines.append(
                f"- `{row['manual_label']}`: Kaggle `{row['kaggle_record_id']}` vs PURSUE `{row['pursue_record_id']}`. "
                f"Reason: {row['manual_notes']}"
            )
    lines.extend([
        "",
        "## Conclusions",
        "The strongest candidates are useful leads, but most are not strong enough to claim confirmed duplicate reports. Extracted official documents improved the evidence quality, while broad historical reports and noisy OCR still create false positives. Transformer text similarity is the strongest retrieval signal; entity overlap and date proximity are useful supporting signals only when they are specific and trustworthy. Location is only useful when the official location is specific and terrestrial.",
        "",
        "## Data Interpretation Notes",
        "- `pursue_text` in the candidate CSV is a relevant extracted-document snippet when available; otherwise it is a metadata snippet.",
        "- `transformer_similarity` is cosine similarity between the Kaggle report and the best official document chunk when embeddings are available.",
        "- `tfidf_text_similarity` is explicit TF-IDF cosine similarity over the candidate snippets; it is secondary to transformer similarity when embeddings are active.",
        "- `lexical_text_similarity` is the older token/string overlap score and remains useful as a secondary/fallback signal.",
        "- `ufo_ner_entities.csv` is a lightweight rule-based NER-style table for locations, dates, organizations/military terms, object shapes, colors, and motion terms.",
        "- `pursue_text_kind=metadata_summary` means the official file could not be matched to extracted text and should be treated as weaker evidence.",
        "- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.",
        "- Blank `location_similarity` means location was deliberately ignored rather than scored as a real match.",
        "",
        "## Limitations",
        "- Some extracted official records describe file collections, launch summaries, or long historical reports rather than single events.",
        "- OCR quality varies across scanned PDFs; some downloaded files were videos or malformed/unsupported documents.",
        "- Transformer similarity can surface semantically broad matches from long official reports, so date/entity/location support and manual validation remain important.",
        "- The earlier strict year-blocking and lexical-heavy approach could miss plausible semantic matches when official dates were missing or unreliable; the current version uses semantic retrieval first and scores date afterward.",
        "- Earlier empty-text rows could create false perfect embedding similarities; empty Kaggle or official snippets are now excluded before semantic matching.",
        "- The candidate list is a triage artifact for manual validation, not a final claim that the events match.",
        "- Rule-based NER is transparent and reproducible, but still weaker than a trained spaCy or transformer NER model.",
    ])
    (REPORTS / "ufo_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = unified_table()
    explore(df)
    matches = candidate_pairs(df)
    write_report(df, matches)


if __name__ == "__main__":
    run()
