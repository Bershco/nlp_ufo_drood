from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

from .common import DATA_PROCESSED, DATA_RAW, FIGURES, REPORTS, STOPWORDS, clean_text, ensure_dirs, save_bar, tokenize, top_terms


PURSUE_MIRROR = "https://raw.githubusercontent.com/DenisSergeevitch/UFO-USA/main/metadata/uap-csv.csv"
SCHEMA = [
    "source", "record_id", "date", "city", "state", "country", "latitude", "longitude",
    "location_text", "description_text", "object_shape", "duration", "source_file_or_link",
]
SHAPE_TERMS = ["light", "sphere", "triangle", "disk", "disc", "fireball", "formation", "orb", "cigar", "circle", "oval"]
ENTITY_TERMS = SHAPE_TERMS + ["military", "base", "aircraft", "weather", "radar", "pilot", "navy", "army", "fbi", "cloud", "missile"]


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def normalize_date(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).replace({"N/A": "", "nan": "", "None": ""})
    return pd.to_datetime(cleaned, errors="coerce", utc=False, format="mixed").dt.date.astype("string")


def load_kaggle(path: Path = DATA_RAW / "ufo" / "kaggle_ufo.csv") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=SCHEMA)
    df = pd.read_csv(path, low_memory=False)
    cols = {
        "date": first_existing_column(df, ["datetime", "date", "Date_time"]),
        "city": first_existing_column(df, ["city"]),
        "state": first_existing_column(df, ["state"]),
        "country": first_existing_column(df, ["country"]),
        "latitude": first_existing_column(df, ["latitude"]),
        "longitude": first_existing_column(df, ["longitude"]),
        "location_text": first_existing_column(df, ["location", "city"]),
        "description_text": first_existing_column(df, ["comments", "description", "text"]),
        "object_shape": first_existing_column(df, ["shape"]),
        "duration": first_existing_column(df, ["duration (seconds)", "duration", "duration (hours/min)"]),
    }
    out = pd.DataFrame(index=df.index)
    out["record_id"] = df.index.astype(str)
    out["source"] = "kaggle"
    for target, source in cols.items():
        out[target] = df[source] if source else ""
    out["date"] = normalize_date(out["date"])
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
    out["date"] = normalize_date(df[first_existing_column(df, ["Incident Date", "Date", "Release Date"]) or title])
    loc_col = first_existing_column(df, ["Incident Location", "Location"])
    out["location_text"] = df[loc_col].astype(str) if loc_col else ""
    out["city"] = ""
    out["state"] = ""
    out["country"] = "USA"
    out["latitude"] = np.nan
    out["longitude"] = np.nan
    desc_col = first_existing_column(df, ["Description Blurb", "Description", "Text"])
    out["description_text"] = df[desc_col].astype(str) if desc_col else df[title].astype(str)
    out["object_shape"] = out["description_text"].apply(infer_shape)
    out["duration"] = ""
    link_col = first_existing_column(df, ["PDF | Image Link", "Link", "source_file_or_link"])
    out["source_file_or_link"] = df[link_col].astype(str) if link_col else ""
    return out[SCHEMA]


def infer_shape(text: str) -> str:
    tokens = set(tokenize(text))
    hits = [term for term in SHAPE_TERMS if term in tokens]
    return "; ".join(hits)


def unified_table() -> pd.DataFrame:
    ensure_dirs()
    frames = [frame for frame in [load_kaggle(), load_pursue()] if not frame.empty]
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


def date_similarity(a: str, b: str) -> float:
    da = pd.to_datetime(a, errors="coerce")
    db = pd.to_datetime(b, errors="coerce")
    if pd.isna(da) or pd.isna(db):
        return 0.1
    days = abs((da - db).days)
    if days == 0:
        return 1.0
    if days <= 1:
        return 0.85
    if days <= 7:
        return 0.65
    if da.year == db.year and da.month == db.month:
        return 0.45
    if da.year == db.year:
        return 0.25
    return 0.0


def location_similarity(a: pd.Series, b: pd.Series) -> float:
    loc_a = " ".join(str(a.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
    loc_b = " ".join(str(b.get(c, "")) for c in ["city", "state", "country", "location_text"]).lower()
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


def candidate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    kaggle = df[df["source"] == "kaggle"].copy()
    pursue = df[df["source"] == "pursue"].copy()
    if kaggle.empty or pursue.empty:
        empty = pd.DataFrame(columns=[
            "kaggle_record_id", "pursue_record_id", "kaggle_date", "pursue_date",
            "kaggle_location", "pursue_location", "kaggle_text", "pursue_text",
            "text_similarity", "location_similarity", "date_similarity",
            "entity_similarity", "final_score", "match_explanation",
            "manual_label", "manual_notes",
        ])
        empty.drop(columns=["manual_label", "manual_notes"]).to_csv(REPORTS / "ufo_candidate_matches.csv", index=False)
        empty.to_csv(REPORTS / "ufo_manual_validation_template.csv", index=False)
        return pd.DataFrame()
    rows = []
    kaggle["year"] = pd.to_datetime(kaggle["date"], errors="coerce").dt.year
    pursue["year"] = pd.to_datetime(pursue["date"], errors="coerce").dt.year
    for _, k in kaggle.iterrows():
        block = pursue[(pursue["year"].isna()) | (k["year"] == pursue["year"]) | (abs(k["year"] - pursue["year"]) <= 1)]
        if len(block) > 500:
            block = block.sample(500, random_state=7)
        for _, p in block.iterrows():
            txt = text_similarity(k["description_text"], p["description_text"])
            loc = location_similarity(k, p)
            dat = date_similarity(k["date"], p["date"])
            ent = entity_similarity(k["description_text"], p["description_text"])
            final = 0.35 * txt + 0.25 * loc + 0.25 * dat + 0.15 * ent
            if final >= 0.25:
                rows.append({
                    "kaggle_record_id": k["record_id"],
                    "pursue_record_id": p["record_id"],
                    "kaggle_date": k["date"],
                    "pursue_date": p["date"],
                    "kaggle_location": k["location_text"] or f"{k['city']} {k['state']} {k['country']}",
                    "pursue_location": p["location_text"],
                    "kaggle_text": k["description_text"][:350],
                    "pursue_text": p["description_text"][:350],
                    "text_similarity": round(txt, 4),
                    "location_similarity": round(loc, 4),
                    "date_similarity": round(dat, 4),
                    "entity_similarity": round(ent, 4),
                    "final_score": round(final, 4),
                    "match_explanation": "Weighted score from text, location, date, and entity/keyword overlap.",
                })
    out = pd.DataFrame(rows).sort_values("final_score", ascending=False).head(100)
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
        "Candidate pairs are blocked by incident year where possible. Final score is:",
        "",
        "`0.35 * text + 0.25 * location + 0.25 * date + 0.15 * entity`",
        "",
        "## Candidate Matches",
    ]
    if matches.empty:
        lines.append("No candidate matches were generated. Add `data/raw/ufo/kaggle_ufo.csv` and rerun.")
    else:
        lines.append(matches.head(20).to_markdown(index=False))
    lines.extend([
        "",
        "## Limitations",
        "- Kaggle data access is credentialed and must be supplied locally.",
        "- Official records can be redacted or broad historical files rather than single-event reports.",
        "- Keyword entities are transparent but weaker than full NER.",
    ])
    (REPORTS / "ufo_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = unified_table()
    explore(df)
    matches = candidate_pairs(df)
    write_report(df, matches)


if __name__ == "__main__":
    run()
