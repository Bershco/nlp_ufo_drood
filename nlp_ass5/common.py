from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "outputs" / "reports"


def ensure_dirs() -> None:
    for path in [
        DATA_RAW / "ufo",
        DATA_RAW / "drood",
        DATA_PROCESSED,
        FIGURES,
        REPORTS,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def download_text(url: str, path: Path) -> str:
    if not path.exists():
        response = requests.get(url, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        path.write_text(response.text, encoding="utf-8")
    return path.read_text(encoding="utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z']+", str(text).lower())


def top_terms(texts: Iterable[str], stopwords: set[str], n: int = 30) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(t for t in tokenize(text) if t not in stopwords and len(t) > 2)
    return pd.DataFrame(counts.most_common(n), columns=["term", "count"])


def save_bar(df: pd.DataFrame, x: str, y: str, title: str, path: Path, rotate: int = 45) -> None:
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df[x].astype(str), df[y])
    ax.set_title(title)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.tick_params(axis="x", rotation=rotate)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


STOPWORDS = {
    "the", "and", "that", "with", "was", "his", "her", "for", "you", "not", "but",
    "had", "him", "she", "all", "this", "from", "they", "are", "have", "were",
    "one", "there", "what", "when", "which", "would", "could", "their", "been",
    "into", "out", "about", "upon", "then", "than", "them", "some", "any", "its",
    "did", "who", "has", "our", "your", "said", "very", "more", "will", "can",
    "see", "saw", "like", "over", "after", "before", "light", "object",
}
