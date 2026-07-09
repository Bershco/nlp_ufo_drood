from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

from .common import DATA_PROCESSED, DATA_RAW, FIGURES, REPORTS, STOPWORDS, clean_text, ensure_dirs, save_bar, tokenize, top_terms
from .manual_docs import compact_name


PURSUE_MIRROR = "https://raw.githubusercontent.com/DenisSergeevitch/UFO-USA/main/metadata/uap-csv.csv"
SCHEMA = [
    "source", "record_id", "date", "date_precision", "date_hint_start", "date_hint_end",
    "city", "state", "country", "latitude", "longitude", "location_text",
    "description_text", "text_kind", "object_shape", "duration", "source_file_or_link",
]
SHAPE_TERMS = ["light", "sphere", "triangle", "disk", "disc", "fireball", "formation", "orb", "cigar", "circle", "oval"]
ENTITY_TERMS = SHAPE_TERMS + ["military", "base", "aircraft", "weather", "radar", "pilot", "navy", "army", "fbi", "cloud", "missile"]
LOCATION_HINTS = [
    "vandenberg", "roswell", "wright patterson", "nellis", "groom lake", "oak ridge",
    "washington", "turkmenistan", "georgia", "syria", "iraq", "persian gulf",
    "arabian gulf", "mediterranean sea", "strait of hormuz", "low earth orbit", "moon",
]


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
                if not clean_text(updated.at[row_idx, "location_text"]):
                    updated.at[row_idx, "location_text"] = infer_location_from_text(text)
    return updated


def infer_shape(text: str) -> str:
    tokens = set(tokenize(text))
    hits = [term for term in SHAPE_TERMS if term in tokens]
    return "; ".join(hits)


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
    df["object_shape"] = df["object_shape"].fillna("").astype(str)
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
    if da.year == db.year and da.month == db.month:
        return 0.40
    if da.year == db.year:
        return 0.12
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


def weighted_score(text_score: float, location_score: float, date_score: float, entity_score: float, text_kind: str) -> tuple[float, str]:
    components = [
        ("text", text_score, 0.35),
        ("date", date_score, 0.25),
        ("entity", entity_score, 0.15),
    ]
    if pd.notna(location_score):
        components.append(("location", location_score, 0.25))
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
            "kaggle_record_id", "pursue_record_id", "kaggle_date", "pursue_date",
            "pursue_date_precision", "pursue_date_hint_start", "pursue_date_hint_end",
            "kaggle_location", "pursue_location", "kaggle_text", "pursue_text",
            "pursue_text_kind",
            "text_similarity", "location_similarity", "date_similarity",
            "entity_similarity", "final_score", "match_explanation",
            "manual_label", "manual_notes",
        ])
        empty.drop(columns=["manual_label", "manual_notes"]).to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
        empty.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
        return pd.DataFrame()
    rows = []
    kaggle["year"] = pd.to_datetime(kaggle["date"], errors="coerce").dt.year
    kaggle["tokens"] = kaggle["description_text"].map(token_set)
    kaggle["entities"] = kaggle["description_text"].map(entity_set)
    pursue["year"] = pd.to_datetime(pursue["date"], errors="coerce").dt.year
    pursue["tokens"] = pursue["description_text"].map(token_set)
    pursue["entities"] = pursue["description_text"].map(entity_set)
    year_ranges = pursue.apply(
        lambda r: years_in_text(r.get("date", ""), r.get("record_id", ""), r.get("description_text", "")),
        axis=1,
        result_type="expand",
    )
    pursue["year_min"] = year_ranges[0]
    pursue["year_max"] = year_ranges[1]
    for _, p in pursue.iterrows():
        if pd.notna(p["year"]):
            block = kaggle[abs(kaggle["year"] - p["year"]) <= 1]
        elif pd.notna(p["year_min"]) and pd.notna(p["year_max"]):
            block = kaggle[(p["year_min"] - 1 <= kaggle["year"]) & (kaggle["year"] <= p["year_max"] + 1)]
        else:
            block = kaggle
        if block.empty:
            continue
        if p["entities"] and len(block) > 5000:
            block = block[block["entities"].map(lambda ents: bool(ents & p["entities"]))]
        if len(block) > 3000:
            block = block.sample(3000, random_state=7)

        cheap_candidates = []
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
            ent = jaccard(k["entities"], p["entities"])
            dat = date_or_range_similarity(k["date"], p["date"], p["date_precision"], p["year_min"], p["year_max"])
            txt = text_similarity(k["description_text"], p["description_text"])
            loc = location_similarity(k, p)
            final, scoring_notes = weighted_score(txt, loc, dat, ent, p["text_kind"])
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
                    "pursue_text": p["description_text"][:350],
                    "pursue_text_kind": p["text_kind"],
                    "text_similarity": round(txt, 4),
                    "location_similarity": "" if pd.isna(loc) else round(loc, 4),
                    "date_similarity": "" if pd.isna(dat) else round(dat, 4),
                    "entity_similarity": round(ent, 4),
                    "final_score": round(final, 4),
                    "match_explanation": scoring_notes,
                })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("final_score", ascending=False).head(100)
    out.to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
    manual = out.head(20).copy()
    manual["manual_label"] = ""
    manual["manual_notes"] = ""
    manual.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
    return out


def explore(df: pd.DataFrame) -> None:
    terms = top_terms(df["description_text"], STOPWORDS, 30)
    terms.to_csv(DATA_PROCESSED / "ufo_top_terms.csv", index=False)
    save_bar(terms.head(20), "term", "count", "UFO/UAP Top Description Terms", FIGURES / "ufo_top_terms.png")

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


def write_report(df: pd.DataFrame, matches: pd.DataFrame) -> None:
    lines = [
        "# UFO/UAP Report Draft",
        "",
        f"Unified records loaded: {len(df)}.",
        f"Kaggle records: {len(df[df['source'] == 'kaggle'])}. PURSUE records: {len(df[df['source'] == 'pursue'])}.",
        "",
        "## Matching Method",
        "Candidate pairs are blocked by incident year or inferred year range where possible.",
        "",
        "The base signals are text, date, location, and entity/keyword overlap. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Repeated PURSUE metadata summaries are penalized because they are document descriptions, not extracted incident text.",
        "",
        "## Candidate Matches",
    ]
    if matches.empty:
        lines.append("No candidate matches were generated. Check whether both Kaggle and PURSUE inputs are available.")
    else:
        lines.append("Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.")
        lines.append("The top-20 manual review sheet is `outputs/reports/ufo_manual_validation_template.csv`.")
    lines.extend([
        "",
        "## Data Interpretation Notes",
        "- `pursue_text` is currently the PURSUE metadata description unless local extracted PDF text is added later.",
        "- `pursue_text_kind=metadata_repeated_summary` means several official records share the same broad description; those rows should be treated as weak leads.",
        "- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.",
        "- Blank `location_similarity` means location was deliberately ignored rather than scored as a real match.",
        "",
        "## Limitations",
        "- PURSUE matching is metadata-level unless official PDFs are downloaded and extracted.",
        "- Some official records describe file collections or historical launch summaries, not single events.",
        "- The candidate list is a triage artifact for manual validation, not a final claim that the events match.",
        "- Keyword entities are transparent but weaker than a full NER or sentence-embedding pipeline.",
    ])
    (REPORTS / "ufo_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = unified_table()
    explore(df)
    matches = candidate_pairs(df)
    write_report(df, matches)


if __name__ == "__main__":
    run()
