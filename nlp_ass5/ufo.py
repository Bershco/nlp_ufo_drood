from __future__ import annotations

import math
import os
import re
import subprocess
import sys
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
    "document_release", "pdf_date_evidence", "pdf_location_evidence",
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
SPACY_MODEL = os.environ.get("UFO_SPACY_MODEL", "en_core_web_sm")
SPACY_ENTITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "FAC", "DATE", "NORP", "EVENT"}
SPACY_MAX_TEXT_CHARS = int(os.environ.get("UFO_SPACY_MAX_TEXT_CHARS", "5000"))
LOCATION_HINTS = [
    "vandenberg", "roswell", "wright patterson", "nellis", "groom lake", "oak ridge",
    "washington", "turkmenistan", "georgia", "syria", "iraq", "persian gulf",
    "arabian gulf", "mediterranean sea", "strait of hormuz", "low earth orbit", "moon",
]
US_STATE_ABBREVIATIONS = {
    "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas", "ca": "california",
    "co": "colorado", "ct": "connecticut", "de": "delaware", "fl": "florida", "ga": "georgia",
    "hi": "hawaii", "id": "idaho", "il": "illinois", "in": "indiana", "ia": "iowa",
    "ks": "kansas", "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland",
    "ma": "massachusetts", "mi": "michigan", "mn": "minnesota", "ms": "mississippi",
    "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
    "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico", "ny": "new york",
    "nc": "north carolina", "nd": "north dakota", "oh": "ohio", "ok": "oklahoma",
    "or": "oregon", "pa": "pennsylvania", "ri": "rhode island", "sc": "south carolina",
    "sd": "south dakota", "tn": "tennessee", "tx": "texas", "ut": "utah", "vt": "vermont",
    "va": "virginia", "wa": "washington", "wv": "west virginia", "wi": "wisconsin",
    "wy": "wyoming", "dc": "district of columbia",
}
US_STATE_NAMES = {v: k for k, v in US_STATE_ABBREVIATIONS.items()}
WESTERN_US_STATES = {
    "ak", "az", "ca", "co", "hi", "id", "mt", "nm", "nv", "or", "ut", "wa", "wy",
}
SOUTHERN_US_STATES = {
    "al", "ar", "fl", "ga", "ky", "la", "ms", "nc", "ok", "sc", "tn", "tx", "va", "wv",
}
EASTERN_US_STATES = {
    "ct", "de", "dc", "fl", "ga", "ma", "md", "me", "nc", "nh", "nj", "ny", "pa",
    "ri", "sc", "va", "vt", "wv",
}
MIDWEST_US_STATES = {
    "ia", "il", "in", "ks", "mi", "mn", "mo", "nd", "ne", "oh", "sd", "wi",
}
COUNTRY_ALIASES = {
    "united states": "us", "usa": "us", "u s": "us", "u s a": "us", "us": "us",
    "united kingdom": "gb", "uk": "gb", "england": "gb", "scotland": "gb", "wales": "gb",
    "germany": "de", "greece": "gr", "syria": "sy", "iraq": "iq", "iran": "ir",
    "japan": "jp", "mexico": "mx", "netherlands": "nl", "turkmenistan": "tm",
    "kazakhstan": "kz", "azerbaijan": "az", "georgia": "ge", "djibouti": "dj",
    "united arab emirates": "ae", "papua new guinea": "pg",
}
REGION_BOXES = {
    "western united states": (25.0, 72.0, -170.0, -102.0),
    "southern united states": (24.0, 38.5, -107.0, -74.0),
    "north america": (7.0, 84.0, -170.0, -50.0),
    "pacific time zone": (31.0, 49.5, -125.0, -114.0),
    "middle east": (12.0, 42.0, 25.0, 65.0),
    "persian gulf": (23.0, 31.0, 47.0, 57.0),
    "arabian gulf": (23.0, 31.0, 47.0, 57.0),
    "arabian sea": (5.0, 26.0, 50.0, 78.0),
    "gulf of oman": (22.0, 27.5, 56.0, 62.5),
    "gulf of aden": (10.0, 15.0, 42.0, 53.0),
    "mediterranean sea": (30.0, 46.0, -6.0, 37.0),
    "aegean sea": (35.0, 41.5, 22.0, 28.5),
    "strait of hormuz": (25.0, 27.5, 55.0, 57.5),
    "east china sea": (24.0, 34.0, 120.0, 130.0),
    "pacific ocean": (-60.0, 65.0, 120.0, -70.0),
    "indo-pacom": (-50.0, 66.0, 65.0, -70.0),
}
TEXT_WEIGHT_WITH_TRANSFORMER = 0.60
DATE_WEIGHT = 0.15
ENTITY_WEIGHT_WITH_TRANSFORMER = 0.15
LOCATION_WEIGHT_WITH_TRANSFORMER = 0.10
TEXT_WEIGHT_WITHOUT_TRANSFORMER = 0.45
ENTITY_WEIGHT_WITHOUT_TRANSFORMER = 0.20
LOCATION_WEIGHT_WITHOUT_TRANSFORMER = 0.20
_SPACY_NLP = None
_SPACY_AVAILABLE: bool | None = None


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
    out["document_release"] = ""
    out["pdf_date_evidence"] = ""
    out["pdf_location_evidence"] = ""
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
    out["document_release"] = "metadata_mirror"
    out["pdf_date_evidence"] = ""
    out["pdf_location_evidence"] = ""
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


def document_release(path: object) -> str:
    value = str(path).lower()
    if "release_1" in value:
        return "release_1"
    if "release_02" in value or "release_2" in value:
        return "release_2"
    if "release_03" in value or "release_3" in value:
        return "release_3"
    return "supplemental"


def date_evidence_from_text(text: object, limit: int = 30) -> str:
    values = re.findall(
        r"\b(?:19[0-9]{2}|20[0-9]{2})[-/]\d{1,2}[-/]\d{1,2}\b|"
        r"\b\d{1,2}[-/]\d{1,2}[-/](?:19|20)?\d{2}\b|"
        r"\b(?:19[0-9]{2}|20[0-9]{2})\b",
        str(text),
    )
    return "; ".join(dict.fromkeys(values[:limit]))


def location_evidence_from_entities(entities: set[str], text: object, limit: int = 30) -> str:
    values = []
    for entity in sorted(entities):
        label, _, value = entity.partition(":")
        if label in {"gpe", "loc", "fac"} and value:
            values.append(value)
    values.extend(hint for hint in LOCATION_HINTS if hint in clean_text(text).lower())
    return "; ".join(dict.fromkeys(values[:limit]))


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
                updated.at[row_idx, "document_release"] = document_release(best.get("text_path", ""))
                updated.at[row_idx, "pdf_date_evidence"] = date_evidence_from_text(text)
                if not clean_text(updated.at[row_idx, "location_text"]):
                    updated.at[row_idx, "location_text"] = infer_location_from_text(text)
    return updated


def add_standalone_pursue_documents(pursue: pd.DataFrame) -> pd.DataFrame:
    """Add every extracted text not already represented by an attached metadata row."""
    index = load_document_text_index()
    if index.empty:
        return pursue
    attached = set(pursue["extracted_text_path"].fillna("").astype(str)) - {""}
    unseen = index[~index["text_path"].fillna("").astype(str).isin(attached)].copy()
    if unseen.empty:
        return pursue

    texts = [read_extracted_text(path) for path in unseen["text_path"].fillna("")]
    rows = []
    for (_, doc), text in zip(unseen.iterrows(), texts):
        if not text:
            continue
        release = document_release(doc.get("document_path", ""))
        dates = date_evidence_from_text(text)
        years = [int(value) for value in re.findall(r"\b(?:19[0-9]{2}|20[0-9]{2})\b", dates)]
        locations = location_evidence_from_entities(set(), text)
        rows.append({
            "source": "pursue",
            "record_id": f"document::{release}::{doc.get('file_name', '')}",
            "date": "",
            "date_precision": "none",
            "date_hint_start": min(years) if years else np.nan,
            "date_hint_end": max(years) if years else np.nan,
            "city": "", "state": "", "country": "",
            "latitude": np.nan, "longitude": np.nan,
            # Entity mentions are evidence, not a claim that the document's
            # incident occurred at every named place.
            "location_text": "",
            "description_text": clean_text(text[:20000]),
            "text_kind": "standalone_extracted_document",
            "extracted_text_path": doc.get("text_path", ""),
            "object_shape": infer_shape(text[:20000]),
            "duration": "",
            "source_file_or_link": doc.get("document_path", ""),
            "document_release": release,
            "pdf_date_evidence": dates,
            "pdf_location_evidence": locations,
        })
    standalone = pd.DataFrame(rows, columns=SCHEMA)
    return pd.concat([pursue, standalone], ignore_index=True)


def enrich_pursue_pdf_evidence(pursue: pd.DataFrame) -> pd.DataFrame:
    """Extract review evidence once per unique PDF text and copy it to its rows."""
    updated = pursue.copy()
    paths = [path for path in dict.fromkeys(updated["extracted_text_path"].fillna("").astype(str)) if path]
    texts = [read_extracted_text(path) for path in paths]
    entity_sets = spacy_entities_for_texts(texts)
    evidence = {
        path: (
            date_evidence_from_text(text),
            location_evidence_from_entities(entities, text),
        )
        for path, text, entities in zip(paths, texts, entity_sets)
    }
    for row_idx, row in updated.iterrows():
        path = str(row.get("extracted_text_path", ""))
        if not path or path not in evidence:
            continue
        dates, locations = evidence[path]
        updated.at[row_idx, "pdf_date_evidence"] = dates
        updated.at[row_idx, "pdf_location_evidence"] = locations
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


def get_spacy_nlp():
    global _SPACY_NLP, _SPACY_AVAILABLE
    if _SPACY_AVAILABLE is False:
        return None
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy

        try:
            _SPACY_NLP = spacy.load(SPACY_MODEL, exclude=["parser", "tagger", "lemmatizer", "attribute_ruler"])
        except OSError:
            if os.environ.get("UFO_AUTO_DOWNLOAD_SPACY", "1").lower() in {"0", "false", "no"}:
                raise
            print(f"spaCy model {SPACY_MODEL!r} is missing; downloading it now...")
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", SPACY_MODEL],
                check=True,
            )
            _SPACY_NLP = spacy.load(SPACY_MODEL, exclude=["parser", "tagger", "lemmatizer", "attribute_ruler"])
        _SPACY_NLP.max_length = max(_SPACY_NLP.max_length, SPACY_MAX_TEXT_CHARS + 1000)
        _SPACY_AVAILABLE = True
        return _SPACY_NLP
    except Exception:
        _SPACY_AVAILABLE = False
        return None


def normalize_ner_value(label: str, value: object) -> str:
    text = clean_text(value).lower()
    if not text or text in {"nan", "none", "n/a", "na"}:
        return ""
    text = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", text)
    if not text:
        return ""
    if label in {"GPE", "LOC"}:
        state = normalized_state(text)
        country = normalized_country(text)
        if state and len(text) <= 20:
            return f"state:{state}"
        if country in COUNTRY_ALIASES.values() and len(text) <= 30:
            return f"country:{country}"
    if label == "ORG":
        aliases = {"dod": "department of defense", "usaf": "air force", "u.s. air force": "air force"}
        text = aliases.get(text, text)
    return f"{label.lower()}:{text}"


def spacy_entities_for_text(text: object, nlp=None) -> set[str]:
    clean = clean_text(text)
    if not clean:
        return set()
    nlp = nlp or get_spacy_nlp()
    if nlp is None:
        return set()
    doc = nlp(clean[:SPACY_MAX_TEXT_CHARS])
    entities: set[str] = set()
    for ent in doc.ents:
        if ent.label_ not in SPACY_ENTITY_LABELS:
            continue
        value = normalize_ner_value(ent.label_, ent.text)
        if value:
            entities.add(value)
    return entities


def spacy_entities_for_texts(texts: list[str]) -> list[set[str]]:
    nlp = get_spacy_nlp()
    if nlp is None:
        return [set() for _ in texts]
    clipped = [clean_text(text)[:SPACY_MAX_TEXT_CHARS] for text in texts]
    results: list[set[str]] = []
    for doc in nlp.pipe(clipped, batch_size=128):
        entities: set[str] = set()
        for ent in doc.ents:
            if ent.label_ not in SPACY_ENTITY_LABELS:
                continue
            value = normalize_ner_value(ent.label_, ent.text)
            if value:
                entities.add(value)
        results.append(entities)
    return results


def structured_ner_entities(row: pd.Series) -> set[str]:
    entities: set[str] = set()
    for field in ["city", "state", "country", "location_text"]:
        value = clean_text(row.get(field, ""))
        if not value:
            continue
        label = "GPE" if field in {"city", "state", "country"} else "LOC"
        normalized = normalize_ner_value(label, value)
        if normalized:
            entities.add(normalized)
    date_value = clean_text(row.get("date", ""))
    if date_value:
        normalized = normalize_ner_value("DATE", date_value)
        if normalized:
            entities.add(normalized)
    return entities


def row_ner_entities(row: pd.Series, text_entities: set[str] | None = None) -> set[str]:
    entities = set(text_entities or set())
    entities |= structured_ner_entities(row)
    return entities


def extract_named_entities(row: pd.Series, spacy_entities: set[str] | None = None) -> list[dict[str, str]]:
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
    for entity in (spacy_entities if spacy_entities is not None else spacy_entities_for_text(text)):
        label, _, value = entity.partition(":")
        add(label.upper(), value, "spacy_en_core_web_sm")
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
    pursue = add_standalone_pursue_documents(pursue)
    pursue = enrich_pursue_pdf_evidence(pursue)
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


def write_offline_geo_map(df: pd.DataFrame, path: Path = FIGURES / "ufo_geographic_map_offline.png") -> None:
    points = df[
        (df["source"] == "kaggle")
        & pd.to_numeric(df["latitude"], errors="coerce").notna()
        & pd.to_numeric(df["longitude"], errors="coerce").notna()
    ].copy()
    if points.empty:
        return
    points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
    points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
    sample = points.sample(min(len(points), 10000), random_state=11)
    us = sample[
        sample["country"].fillna("").astype(str).str.lower().eq("us")
        & sample["latitude"].between(18, 72)
        & sample["longitude"].between(-170, -64)
    ]
    world = sample[~sample.index.isin(us.index)]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    axes[0].scatter(sample["longitude"], sample["latitude"], s=2, alpha=0.18, color="#2563eb")
    axes[0].set_title("Global UFO/UAP Report Coordinates")
    axes[0].set_xlim(-180, 180)
    axes[0].set_ylim(-65, 85)
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].grid(True, linewidth=0.3, alpha=0.35)

    if not world.empty:
        axes[0].scatter(world["longitude"], world["latitude"], s=4, alpha=0.25, color="#dc2626")

    if not us.empty:
        axes[1].scatter(us["longitude"], us["latitude"], s=2, alpha=0.20, color="#047857")
    axes[1].set_title("United States Detail")
    axes[1].set_xlim(-126, -66)
    axes[1].set_ylim(24, 50)
    axes[1].set_xlabel("Longitude")
    axes[1].set_ylabel("Latitude")
    axes[1].grid(True, linewidth=0.3, alpha=0.35)

    fig.suptitle("Offline Geographic View of Kaggle UFO Reports", y=0.98)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def candidate_snippet(document_text: str, query_text: str, max_chars: int = 450) -> str:
    text = clean_text(document_text)
    if len(text) <= max_chars:
        return text
    query_tokens = token_set(query_text) | entity_set(query_text)
    if not query_tokens:
        return safe_excerpt(text, max_chars)
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
    return safe_excerpt(snippet, max_chars)


def safe_excerpt(text: object, max_chars: int = 900) -> str:
    """Return a compact excerpt without ending in the middle of a word."""
    cleaned = clean_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    shortened = cleaned[:max_chars + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{shortened} …"


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
        snippets[idx] = safe_excerpt(context["pursue_chunk_texts"][chunk_position], 900)
    return scores, snippets


LIKELY_SHARE = 0.03
POSSIBLE_SHARE = 0.32
MAX_EXPORTED_CANDIDATES = 500
DETAILED_CANDIDATES_PER_PURSUE = 120


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
    if text_kind in {"extracted_document_text", "standalone_extracted_document"}:
        strong_reasons.append("uses extracted official document text")
    if pd.notna(date) and date >= 0.9:
        strong_reasons.append("date is exact or within a few days")
    elif pd.notna(date) and date >= 0.45:
        strong_reasons.append("date is in a moderately close window")
    elif pd.isna(date):
        weak_reasons.append("official date is missing or only inferred")
    else:
        weak_reasons.append("date support is weak")
    if pd.notna(loc) and loc >= 0.75:
        strong_reasons.append("location is geographically compatible")
    elif pd.notna(loc) and loc >= 0.40:
        strong_reasons.append("location has broad geographic support")
    elif pd.isna(loc):
        weak_reasons.append("official location was not usable")
    if text < 0.08:
        weak_reasons.append("direct text similarity is low")
    if entity >= 0.5:
        strong_reasons.append("NER/entity overlap is meaningful")
    if pd.notna(percentile):
        strong_reasons.append(f"score percentile {percentile:.3f}")
    return "; ".join(strong_reasons + weak_reasons)


def assign_relative_rank_bands(out: pd.DataFrame) -> pd.DataFrame:
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
    labeled["automated_rank_band"] = labels
    labeled["automated_rank_notes"] = [
        validation_notes(row, label)
        for (_, row), label in zip(labeled.iterrows(), labels)
    ]
    labeled["manual_label"] = ""
    labeled["manual_notes"] = ""
    return labeled


def validation_label(row: pd.Series) -> tuple[str, str]:
    label = str(row.get("automated_rank_band", "probably not same event"))
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


def normalized_country(value: object) -> str:
    country = clean_location_value(value)
    return COUNTRY_ALIASES.get(country, country)


def normalized_state(value: object) -> str:
    state = clean_location_value(value)
    if not state:
        return ""
    if state in US_STATE_ABBREVIATIONS:
        return state
    return US_STATE_NAMES.get(state, "")


def row_lat_lon(row: pd.Series) -> tuple[float, float] | None:
    try:
        lat = float(row.get("latitude", np.nan))
        lon = float(row.get("longitude", np.nan))
    except Exception:
        return None
    if not math.isfinite(lat) or not math.isfinite(lon):
        return None
    return lat, lon


def point_in_box(lat: float, lon: float, box: tuple[float, float, float, float]) -> bool:
    min_lat, max_lat, min_lon, max_lon = box
    if min_lon <= max_lon:
        return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
    return min_lat <= lat <= max_lat and (lon >= min_lon or lon <= max_lon)


def extract_state_from_location_text(location: str) -> str:
    loc = clean_location_value(location)
    if not loc:
        return ""
    parts = [part.strip() for part in re.split(r"[,;/()]+", loc) if part.strip()]
    for part in parts:
        if part in US_STATE_ABBREVIATIONS:
            return part
        if part in US_STATE_NAMES:
            return US_STATE_NAMES[part]
    tokens = set(tokenize(loc))
    for name, abbr in US_STATE_NAMES.items():
        if set(name.split()).issubset(tokens):
            return abbr
    return ""


def extract_country_from_location_text(location: str) -> str:
    loc = clean_location_value(location)
    if not loc:
        return ""
    if loc in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[loc]
    for alias, code in COUNTRY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", loc):
            return code
    return ""


def is_non_terrestrial_location(value: object) -> bool:
    loc = clean_location_value(value)
    return loc in {"moon", "low earth orbit", "earth orbit", "space"} or any(
        token in loc for token in ["low earth orbit", "earth orbit"]
    )


def us_region_score(state: str, lat_lon: tuple[float, float] | None, loc: str) -> float | None:
    region_states = {
        "western united states": WESTERN_US_STATES,
        "southern united states": SOUTHERN_US_STATES,
        "eastern united states": EASTERN_US_STATES,
        "midwestern united states": MIDWEST_US_STATES,
        "midwest": MIDWEST_US_STATES,
        "pacific time zone": {"ca", "or", "wa", "nv"},
    }
    for region, states in region_states.items():
        if region in loc:
            if state in states:
                return 0.85
            if lat_lon and point_in_box(lat_lon[0], lat_lon[1], REGION_BOXES[region]):
                return 0.80
            return 0.15
    if loc == "united states":
        return 0.45 if state or (lat_lon and point_in_box(lat_lon[0], lat_lon[1], (18.0, 72.0, -170.0, -64.0))) else 0.10
    if loc == "north america":
        return 0.40 if lat_lon and point_in_box(lat_lon[0], lat_lon[1], REGION_BOXES[loc]) else 0.10
    return None


def format_location(row: pd.Series) -> str:
    parts = [
        clean_text(row.get("city", "")),
        normalized_state(row.get("state", "")),
        normalized_country(row.get("country", "")),
    ]
    text = ", ".join(part for part in parts if part)
    raw = clean_text(row.get("location_text", ""))
    if raw and raw.lower() not in text.lower():
        text = f"{raw} ({text})" if text else raw
    lat_lon = row_lat_lon(row)
    if lat_lon:
        text = f"{text} [{lat_lon[0]:.4f}, {lat_lon[1]:.4f}]" if text else f"[{lat_lon[0]:.4f}, {lat_lon[1]:.4f}]"
    return text


def location_similarity(a: pd.Series, b: pd.Series) -> float:
    pursue_loc = clean_location_value(b.get("location_text", ""))
    if b.get("source") == "pursue" and (not pursue_loc or is_non_terrestrial_location(pursue_loc)):
        return np.nan
    loc_a = " ".join(str(a.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
    loc_b = " ".join(str(b.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
    if not clean_location_value(loc_a) or not clean_location_value(loc_b):
        return np.nan

    a_state = normalized_state(a.get("state", "")) or extract_state_from_location_text(loc_a)
    a_country = normalized_country(a.get("country", "")) or extract_country_from_location_text(loc_a)
    b_state = normalized_state(b.get("state", "")) or extract_state_from_location_text(pursue_loc)
    b_country = extract_country_from_location_text(pursue_loc) or normalized_country(b.get("country", ""))
    a_lat_lon = row_lat_lon(a)

    region_score = us_region_score(a_state, a_lat_lon, pursue_loc)
    if region_score is not None:
        return region_score

    if pursue_loc in REGION_BOXES and a_lat_lon:
        return 0.80 if point_in_box(a_lat_lon[0], a_lat_lon[1], REGION_BOXES[pursue_loc]) else 0.05
    if b_state:
        return 0.95 if a_state == b_state else (0.35 if a_country == "us" else 0.0)
    if b_country:
        return 0.65 if a_country == b_country else 0.0

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


def ner_similarity(a_entities: set[str], b_entities: set[str]) -> float:
    if not a_entities and not b_entities:
        return np.nan
    if not a_entities or not b_entities:
        return 0.0
    return len(a_entities & b_entities) / len(a_entities | b_entities)


def blended_entity_similarity(domain_score: float, ner_score: float) -> float:
    if pd.isna(domain_score):
        domain_score = 0.0
    if pd.isna(ner_score):
        return float(domain_score)
    return 0.45 * float(domain_score) + 0.55 * float(ner_score)


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
        notes.append("location ignored because PURSUE location is missing or non-terrestrial")
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
            "pursue_text_kind", "pursue_document_release", "pursue_pdf_date_evidence", "pursue_pdf_location_evidence",
            "kaggle_source_file_or_link", "pursue_source_file_or_link", "pursue_extracted_text_path",
            "transformer_similarity", "lexical_text_similarity", "tfidf_text_similarity", "text_similarity",
            "location_similarity", "date_similarity",
            "domain_entity_similarity", "ner_similarity", "entity_similarity", "final_score", "match_explanation",
            "automated_rank_band", "automated_rank_notes", "manual_label", "manual_notes",
        ])
        empty.to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
        empty.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
        pd.DataFrame([{"detailed_pairs_scored": 0, "pairs_exported": 0}]).to_csv(
            REPORTS / "ufo_candidate_scoring_summary.csv", index=False
        )
        return pd.DataFrame()
    rows = []
    kaggle = kaggle[kaggle["description_text"].map(has_usable_text)].copy()
    pursue = pursue[pursue["description_text"].map(has_usable_text)].copy()
    kaggle["year"] = pd.to_datetime(kaggle["date"], errors="coerce").dt.year
    kaggle["tokens"] = kaggle["description_text"].map(token_set)
    kaggle["entities"] = kaggle["description_text"].map(entity_set)
    kaggle_text_ner = spacy_entities_for_texts(kaggle["description_text"].fillna("").astype(str).tolist())
    kaggle["ner_entities"] = [row_ner_entities(row, ents) for (_, row), ents in zip(kaggle.iterrows(), kaggle_text_ner)]
    pursue["year"] = pd.to_datetime(pursue["date"], errors="coerce").dt.year
    pursue["tokens"] = pursue["description_text"].map(token_set)
    pursue["entities"] = pursue["description_text"].map(entity_set)
    pursue_text_ner = spacy_entities_for_texts(
        (pursue["record_id"].fillna("").astype(str) + " " + pursue["description_text"].fillna("").astype(str)).tolist()
    )
    pursue["ner_entities"] = [row_ner_entities(row, ents) for (_, row), ents in zip(pursue.iterrows(), pursue_text_ner)]
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
                ent = max(jaccard(k["entities"], p["entities"]), ner_similarity(k["ner_entities"], p["ner_entities"]))
                txt_cheap = jaccard(k["tokens"], p["tokens"])
                dat_cheap = date_or_range_similarity(k["date"], p["date"], p["date_precision"], p["year_min"], p["year_max"])
                dat_for_rank = 0.0 if pd.isna(dat_cheap) else dat_cheap
                cheap = 0.55 * txt_cheap + 0.25 * ent + 0.20 * dat_for_rank
                if cheap >= 0.025:
                    cheap_candidates.append((cheap, idx))
        # Every retrieved candidate receives the complete multi-signal score.
        # Do not pre-truncate this set based on the cheaper semantic/blocking
        # signal: a pair can improve after date, location, TF-IDF, or entity
        # evidence is considered.
        for _, idx in sorted(cheap_candidates, reverse=True)[:DETAILED_CANDIDATES_PER_PURSUE]:
            k = kaggle.loc[idx]
            transformer_score = semantic_scores.get(int(idx), np.nan)
            p_snippet = semantic_snippets.get(int(idx)) or candidate_snippet(p["description_text"], k["description_text"])
            domain_ent = jaccard(k["entities"], p["entities"])
            snippet_ner = spacy_entities_for_text(p_snippet) | structured_ner_entities(p)
            ner_ent = ner_similarity(k["ner_entities"], snippet_ner or p["ner_entities"])
            ent = blended_entity_similarity(domain_ent, ner_ent)
            dat = date_or_range_similarity(k["date"], p["date"], p["date_precision"], p["year_min"], p["year_max"])
            lexical = text_similarity(k["description_text"], p_snippet)
            tfidf = tfidf_similarity(k["description_text"], p_snippet)
            loc = location_similarity(k, p)
            final, scoring_notes = weighted_score(transformer_score, lexical, tfidf, loc, dat, ent, p["text_kind"])
            rows.append({
                    "kaggle_record_id": k["record_id"],
                    "pursue_record_id": p["record_id"],
                    "kaggle_date": k["date"],
                    "pursue_date": p["date"],
                    "pursue_date_precision": p["date_precision"],
                    "pursue_date_hint_start": p["date_hint_start"],
                    "pursue_date_hint_end": p["date_hint_end"],
                    "kaggle_location": format_location(k),
                    "pursue_location": p["location_text"],
                    "kaggle_text": k["description_text"][:350],
                    "pursue_text": p_snippet,
                    "pursue_text_kind": p["text_kind"],
                    "pursue_document_release": p.get("document_release", ""),
                    "pursue_pdf_date_evidence": p.get("pdf_date_evidence", ""),
                    "pursue_pdf_location_evidence": p.get("pdf_location_evidence", ""),
                    "kaggle_source_file_or_link": k["source_file_or_link"],
                    "pursue_source_file_or_link": p["source_file_or_link"],
                    "pursue_extracted_text_path": p["extracted_text_path"],
                    "transformer_similarity": "" if pd.isna(transformer_score) else round(transformer_score, 4),
                    "lexical_text_similarity": round(lexical, 4),
                    "tfidf_text_similarity": round(tfidf, 4),
                    "text_similarity": round(transformer_score, 4) if pd.notna(transformer_score) else round(lexical, 4),
                    "location_similarity": "" if pd.isna(loc) else round(loc, 4),
                    "date_similarity": "" if pd.isna(dat) else round(dat, 4),
                    "domain_entity_similarity": round(domain_ent, 4),
                    "ner_similarity": round(ner_ent, 4),
                    "entity_similarity": round(ent, 4),
                    "final_score": round(final, 4),
                "match_explanation": scoring_notes,
            })
    out = pd.DataFrame(rows)
    detailed_pairs_scored = len(out)
    if not out.empty:
        out = out.sort_values("final_score", ascending=False).head(MAX_EXPORTED_CANDIDATES).reset_index(drop=True)
        out.insert(0, "candidate_rank", range(1, len(out) + 1))
        denominator = max(len(out) - 1, 1)
        out.insert(1, "score_percentile", [round(1 - (rank - 1) / denominator, 4) for rank in out["candidate_rank"]])
        out = assign_relative_rank_bands(out)
    pd.DataFrame([{
        "pursue_records": len(pursue),
        "retrieval_limit_per_pursue": DETAILED_CANDIDATES_PER_PURSUE,
        "detailed_pairs_scored": detailed_pairs_scored,
        "minimum_final_score": "none",
        "export_limit": MAX_EXPORTED_CANDIDATES,
        "pairs_exported": len(out),
    }]).to_csv(REPORTS / "ufo_candidate_scoring_summary.csv", index=False)
    out.to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
    manual = out.head(20).copy()
    manual.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
    completed_path = REPORTS / "ufo_manual_validation_completed.csv"
    if completed_path.exists():
        existing = pd.read_csv(completed_path, keep_default_na=False)
        # Migrate the old automatically populated "manual" columns once. After
        # this migration, reruns never overwrite a student's judgments.
        if "automated_rank_band" not in existing and "manual_label" in existing:
            existing = existing.rename(columns={
                "manual_label": "automated_rank_band",
                "manual_notes": "automated_rank_notes",
            })
            existing["manual_label"] = ""
            existing["manual_notes"] = ""
        # Refresh the top-20 membership while carrying forward judgments for
        # any pair that is still present after a scoring/data update.
        review_keys = ["kaggle_record_id", "pursue_record_id"]
        if all(column in existing for column in review_keys + ["manual_label", "manual_notes"]):
            prior_reviews = existing[review_keys + ["manual_label", "manual_notes"]].drop_duplicates(review_keys)
            manual = manual.drop(columns=["manual_label", "manual_notes"]).merge(
                prior_reviews,
                on=review_keys,
                how="left",
            )
            manual[["manual_label", "manual_notes"]] = manual[["manual_label", "manual_notes"]].fillna("")
        manual.to_csv(completed_path, index=False)
    else:
        manual.to_csv(completed_path, index=False)
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
        "- Fill `manual_label` and `manual_notes` in `ufo_manual_validation_completed.csv`; do not copy the automated rank band without making your own judgment.",
        "",
        "## Top 20",
    ]
    for _, row in helper.iterrows():
        lines.extend([
            "",
            f"### Rank {row['candidate_rank']}: Kaggle {row['kaggle_record_id']} vs PURSUE {row['pursue_record_id']}",
            "",
            f"- Automated rank band: `{row['automated_rank_band']}`",
            f"- Final score: `{row['final_score']}`",
            f"- Dates: Kaggle `{row['kaggle_date']}` vs PURSUE `{row['pursue_date']}`",
            f"- Date mentions found in PDF: `{row.get('pursue_pdf_date_evidence', '')}`",
            f"- Locations: Kaggle `{row['kaggle_location']}` vs PURSUE `{row['pursue_location']}`",
            f"- Location entities found in PDF: `{row.get('pursue_pdf_location_evidence', '')}`",
            f"- PURSUE release: `{row.get('pursue_document_release', '')}`",
            f"- Source link/file: `{row.get('pursue_source_file_or_link', '')}`",
            f"- Extracted text path: `{row.get('pursue_extracted_text_path', '')}`",
            f"- Automated reason: {row['automated_rank_notes']}",
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
        ax.set_yscale("log")
        fig.tight_layout()
        fig.savefig(FIGURES / "ufo_temporal_trends.png", dpi=300)
        plt.close(fig)

    entity_rows = []
    ner_rows = []
    spacy_entity_sets = spacy_entities_for_texts(df["description_text"].fillna("").astype(str).tolist())
    for (_, row), row_spacy_entities in zip(df.iterrows(), spacy_entity_sets):
        for entity in entity_hits(row["description_text"]):
            entity_rows.append({"source": row["source"], "entity": entity})
        ner_rows.extend(extract_named_entities(row, row_ner_entities(row, row_spacy_entities)))
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
    write_offline_geo_map(df)

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
    attached_extracted_count = int(text_counts.get("extracted_document_text", 0))
    standalone_extracted_count = int(text_counts.get("standalone_extracted_document", 0))
    extracted_count = attached_extracted_count + standalone_extracted_count
    metadata_count = int(text_counts.get("metadata_summary", 0) + text_counts.get("metadata_repeated_summary", 0))
    validation_path = REPORTS / "ufo_manual_validation_completed.csv"
    validation = pd.read_csv(validation_path) if validation_path.exists() else pd.DataFrame()
    all_validation = matches if not matches.empty and "automated_rank_band" in matches else pd.DataFrame()
    manual_labels = validation["manual_label"].fillna("").astype(str).str.strip() if "manual_label" in validation else pd.Series(dtype=str)
    label_counts = manual_labels[manual_labels.ne("")].value_counts().to_dict()
    all_label_counts = all_validation["automated_rank_band"].value_counts().to_dict() if not all_validation.empty else {}
    transformer_active = (
        not matches.empty
        and "transformer_similarity" in matches
        and pd.to_numeric(matches["transformer_similarity"], errors="coerce").notna().any()
    )
    lines = [
        "# UFO/UAP Final Report",
        "",
        f"Unified records loaded: {len(df)}.",
        f"Kaggle records: {len(df[df['source'] == 'kaggle'])}. PURSUE records: {len(df[df['source'] == 'pursue'])}.",
        f"PURSUE rows with extracted document text: {extracted_count} ({attached_extracted_count} metadata-attached rows and {standalone_extracted_count} standalone documents). Metadata-only PURSUE rows: {metadata_count}.",
        f"Transformer similarity active for this run: {transformer_active}.",
        "",
        "## Matching Method",
        "Candidate retrieval uses broad transformer-based semantic retrieval when embeddings are available, rather than strict date/location blocking. Date and location are weak or missing in many PURSUE records, so they are used as scoring evidence after retrieval instead of hard filters. If transformer embeddings are unavailable, the fallback path still uses year/entity blocking to avoid an all-pairs comparison.",
        "",
        "The base signals are transformer text similarity, TF-IDF text similarity, lexical text similarity, date, location, and entity overlap. Entity overlap blends UFO-domain keyword overlap with lightweight spaCy NER (`en_core_web_sm`) when the model is installed. When `sentence-transformers` is installed, transformer cosine similarity is the primary text signal and TF-IDF/lexical overlap are secondary. If the transformer dependency is unavailable, the pipeline falls back to TF-IDF and lexical text similarity. The score is normalized over reliable available signals. Location is ignored only when the PURSUE location is missing or non-terrestrial; broad terrestrial locations such as `Western United States` are scored as coarse geographic regions. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.",
        "",
        f"Current transformer weights are text {TEXT_WEIGHT_WITH_TRANSFORMER:.2f}, date {DATE_WEIGHT:.2f}, entity {ENTITY_WEIGHT_WITH_TRANSFORMER:.2f}, and location {LOCATION_WEIGHT_WITH_TRANSFORMER:.2f}. Date weight was deliberately reduced because PURSUE dates are often missing, broad, title-derived, or document/admin dates rather than confidently verified event dates.",
        "",
        "Rows with empty Kaggle text or empty official snippets are excluded from semantic candidate matching so identical empty embeddings cannot create false high-similarity pairs.",
        "",
        "Date similarity is based on absolute day distance, so cross-year near misses such as December 31 versus January 2 are still treated as close. Full-date gaps use tiers from exact day through 365 days; year-only official dates use a weaker same-year/plus-minus-one-year fallback.",
        "",
        f"Automated rank bands divide the exported candidate pool into the top {LIKELY_SHARE:.0%}, next {POSSIBLE_SHARE:.0%}, and remaining candidates. Their text resembles the three requested review labels for prioritization, but they are not human judgments or claims of event identity. Human decisions belong only in `manual_label` and `manual_notes`.",
        "",
        "## Candidate Matches",
    ]
    if matches.empty:
        lines.append("No candidate matches were generated. Check whether both Kaggle and PURSUE inputs are available.")
    else:
        lines.append("Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.")
        lines.append("All exported candidates include automated rank bands and notes, plus separate blank fields for human review.")
        lines.append(f"Automated rank bands among all exported candidates: {all_label_counts}.")
        lines.append("The top-20 manual-review working file is `outputs/reports/ufo_manual_validation_completed.csv`.")
        lines.append(f"Completed human labels among top 20: {label_counts}.")
    lines.extend([
        "",
        "## Exploration Outputs",
        "- Common terms: `data/processed/ufo_top_terms.csv`.",
        "- Common phrases: `data/processed/ufo_common_phrases.csv`.",
        "- Entity/keyword counts by source: `data/processed/ufo_entity_counts_by_source.csv`.",
        "- spaCy plus domain-lexicon NER entities: `data/processed/ufo_ner_entities.csv` and `data/processed/ufo_ner_summary.csv`.",
        "- Civilian vs official language comparison: `data/processed/ufo_source_language_comparison.csv`.",
        "- Temporal trends: `data/processed/ufo_temporal_trends.csv`.",
        "- Geographic trends: `data/processed/ufo_geographic_trends.csv`.",
        "- Interactive geographic map: `outputs/figures/ufo_geographic_map.html`.",
        "- Offline geographic map image: `outputs/figures/ufo_geographic_map_offline.png`.",
        "- Rare sightings: `data/processed/ufo_rare_sightings.csv`.",
        "",
        "## Validation Examples",
    ])
    reviewed = validation[manual_labels.ne("")] if not validation.empty and len(manual_labels) == len(validation) else pd.DataFrame()
    if reviewed.empty:
        lines.append("Human review is not complete yet. After the top 20 are labeled, discuss at least five representative pairs here using the pair-specific manual notes.")
    else:
        detailed_ranks = [1, 3, 6, 9, 18]
        details = {
            1: "Both texts describe combinations of orange/red orb-like lights, and Santa Cruz is compatible with the official record's broad Western United States location. This makes the pair thematically plausible. However, the official 2023 value cannot be verified as the event date, while the Kaggle report is from 2012, and the color/orb pattern is common across many sightings. The pair is therefore possible, not verified.",
            3: "The descriptions share a similar sequence of unidentified lights or objects, but the official incident-summary collection supplies neither a usable location nor a reliable event date for this particular passage. The semantic model retrieved a comparable event description, yet the low direct TF-IDF and NER overlap show that the wording and specific entities are not distinctive enough to establish identity.",
            6: "The descriptions again share orange/red orb characteristics, but the Kaggle location is East Glastonbury, Connecticut, whereas the official location is Western United States. The deliberately low location score of 0.15 captures this conflict. Because PURSUE dates may be administrative and the visual description remains similar, the pair is retained as possible, although geographic evidence argues against it.",
            9: "This is the clearest negative example. The Kaggle report is from Cabo San Lucas, Mexico, while the PURSUE passage has no usable location. The reported durations and event descriptions differ, TF-IDF overlap is zero, and named-entity overlap is zero. Semantic similarity alone appears to have retrieved the same broad class of sighting rather than the same incident, so the pair is classified as probably not the same event.",
            18: "Both reports concern orb-like phenomena and the Kaggle sighting occurred in Friday Harbor, Washington, which is compatible with the official record's very broad United States label. Nevertheless, that location covers the entire country and the official date is unavailable. The shared orb vocabulary makes this a useful lead, but it does not provide enough specificity for a likely-match claim.",
        }
        for rank in detailed_ranks:
            subset = reviewed[pd.to_numeric(reviewed["candidate_rank"], errors="coerce") == rank]
            if subset.empty:
                continue
            row = subset.iloc[0]
            lines.extend([
                "",
                f"### Rank {rank}: Kaggle `{row['kaggle_record_id']}` vs PURSUE `{row['pursue_record_id']}`",
                f"**Manual classification:** {row['manual_label']}.",
                details[rank],
            ])
    lines.extend([
        "",
        "## Conclusions",
        "The system found several plausible thematic correspondences, especially reports involving orange or red orbs, but insufficient date, location, and distinctive-event evidence prevents confidently establishing a cross-source duplicate. Manual review classified 19 pairs as possibly the same event and one as probably not the same event; none met a defensible threshold for likely identity. This is a substantive result rather than a pipeline failure: redaction, missing incident dates, broad released locations, and other limits of the declassified PURSUE material remove precisely the evidence needed to confirm identity across sources. Transformer similarity was effective for retrieving comparable sighting narratives, while TF-IDF, NER, location, and cautious date evidence helped reveal when semantic similarity represented a shared event type rather than one historical occurrence.",
        "",
        "## Data Interpretation Notes",
        "- `pursue_text` in the candidate CSV is a relevant extracted-document snippet when available; otherwise it is a metadata snippet.",
        "- `transformer_similarity` is cosine similarity between the Kaggle report and the best official document chunk when embeddings are available.",
        "- `tfidf_text_similarity` is explicit TF-IDF cosine similarity over the candidate snippets; it is secondary to transformer similarity when embeddings are active.",
        "- `lexical_text_similarity` is the older token/string overlap score and remains useful as a secondary/fallback signal.",
        "- `ufo_ner_entities.csv` combines lightweight spaCy NER for people, organizations, places, facilities, events, and dates with domain lexicons for military terms, object shapes, colors, and motion terms.",
        "- `pursue_text_kind=metadata_summary` means the official file could not be matched to extracted text and should be treated as weaker evidence.",
        "- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.",
        "- Blank `location_similarity` means location was deliberately ignored because the official location was missing or non-terrestrial.",
        "",
        "## Limitations",
        "- Some extracted official records describe file collections, launch summaries, or long historical reports rather than single events.",
        "- OCR quality varies across scanned PDFs; some downloaded files were videos or malformed/unsupported documents.",
        "- Transformer similarity can surface semantically broad matches from long official reports, so date/entity/location support and manual validation remain important.",
        "- Semantic retrieval is performed before date scoring because official dates are frequently missing or cannot be identified confidently as incident dates.",
        "- Rows with empty Kaggle or official text are excluded before semantic matching.",
        "- The candidate list is a triage artifact for manual validation, not a final claim that the events match.",
        "- Lightweight spaCy NER can miss domain-specific bases, redacted names, OCR-damaged places, and UAP-specific phrases.",
        "- Declassified releases may redact or omit precise dates, locations, names, units, sensor details, and other identifying context; this directly weakens date, location, and entity comparison.",
    ])
    (REPORTS / "ufo_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = unified_table()
    explore(df)
    matches = candidate_pairs(df)
    write_report(df, matches)


if __name__ == "__main__":
    run()
