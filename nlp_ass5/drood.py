from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from .common import DATA_PROCESSED, DATA_RAW, FIGURES, REPORTS, STOPWORDS, clean_text, download_text, ensure_dirs, save_bar, tokenize, top_terms


DROOD_URL = "https://www.gutenberg.org/files/564/564-0.txt"
GREAT_EXPECTATIONS_URL = "https://www.gutenberg.org/files/1400/1400-0.txt"

CHARACTERS = {
    "Edwin Drood": ["edwin drood", "edwin", "drood"],
    "John Jasper": ["john jasper", "jasper"],
    "Rosa Bud": ["rosa bud", "rosa", "rosebud"],
    "Neville Landless": ["neville landless", "neville"],
    "Helena Landless": ["helena landless", "helena"],
    "Mr. Crisparkle": ["mr crisparkle", "crisparkle"],
    "Durdles": ["durdles"],
    "Princess Puffer": ["princess puffer", "puffer"],
    "Dick Datchery": ["dick datchery", "datchery"],
}

MOTIVE_TERMS = {"jealousy", "jealous", "love", "rival", "rivalry", "anger", "revenge", "hate", "fear", "obsession", "passion"}
SUSPICIOUS_TERMS = {"death", "dead", "murder", "grave", "graveyard", "dark", "secret", "opium", "fear", "blood", "kill", "violence", "disappear", "strangle", "guilt"}
POSITIVE = {"good", "kind", "love", "bright", "happy", "hope", "gentle", "dear", "honest", "safe"}
NEGATIVE = {"dark", "fear", "dead", "death", "angry", "cruel", "secret", "strange", "violent", "hate", "sad", "grave", "murder"}


def strip_gutenberg(text: str) -> str:
    start = re.search(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I | re.S)
    end = re.search(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*", text, re.I | re.S)
    if start:
        text = text[start.end():]
    if end:
        text = text[:end.start()]
    return text.strip()


def split_chapters(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"(?m)^CHAPTER\s+([IVXLCDM]+|\d+)\b.*$", text))
    chapters: list[tuple[int, str]] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append((i + 1, text[start:end].strip()))
    return chapters


def sentence_split(paragraph: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", clean_text(paragraph))
    return [p.strip() for p in pieces if len(p.strip()) > 20]


def mentioned_characters(text: str) -> list[str]:
    lowered = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    found = []
    for char, aliases in CHARACTERS.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases):
            found.append(char)
    return found


def build_text_table() -> pd.DataFrame:
    ensure_dirs()
    raw = download_text(DROOD_URL, DATA_RAW / "drood" / "edwin_drood.txt")
    text = strip_gutenberg(raw)
    rows = []
    for chapter, chapter_text in split_chapters(text):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", chapter_text) if len(clean_text(p)) > 40]
        for paragraph_id, paragraph in enumerate(paragraphs, start=1):
            for sentence_id, sentence in enumerate(sentence_split(paragraph), start=1):
                chars = mentioned_characters(sentence)
                rows.append({
                    "chapter": chapter,
                    "paragraph_id": paragraph_id,
                    "sentence_id": sentence_id,
                    "text": sentence,
                    "characters_mentioned": "; ".join(chars),
                })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_PROCESSED / "drood_sentences.csv", index=False)
    return df


def character_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    mention_rows = []
    co_counts: Counter[tuple[str, str]] = Counter()
    for _, row in df.iterrows():
        chars = [c for c in str(row["characters_mentioned"]).split("; ") if c and c != "nan"]
        for char in chars:
            mention_rows.append({"character": char, "chapter": row["chapter"]})
        for i, a in enumerate(chars):
            for b in chars[i + 1:]:
                co_counts[tuple(sorted((a, b)))] += 1
    mentions = pd.DataFrame(mention_rows)
    freq = mentions["character"].value_counts().rename_axis("character").reset_index(name="mentions")
    by_chapter = mentions.groupby(["chapter", "character"]).size().reset_index(name="mentions")
    cooc = pd.DataFrame([{"character_a": a, "character_b": b, "weight": w} for (a, b), w in co_counts.items()])
    freq.to_csv(DATA_PROCESSED / "drood_character_frequency.csv", index=False)
    by_chapter.to_csv(DATA_PROCESSED / "drood_character_by_chapter.csv", index=False)
    cooc.to_csv(DATA_PROCESSED / "drood_character_cooccurrence.csv", index=False)
    return freq, by_chapter, cooc


def sentiment_theme_by_character(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for char in CHARACTERS:
        char_text = " ".join(df[df["characters_mentioned"].str.contains(re.escape(char), na=False)]["text"])
        tokens = tokenize(char_text)
        total = max(len(tokens), 1)
        pos = sum(t in POSITIVE for t in tokens)
        neg = sum(t in NEGATIVE for t in tokens)
        suspicious = sum(t in SUSPICIOUS_TERMS for t in tokens)
        rows.append({
            "character": char,
            "positive_rate": pos / total,
            "negative_rate": neg / total,
            "suspicious_rate": suspicious / total,
            "net_sentiment": (pos - neg) / total,
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA_PROCESSED / "drood_character_sentiment_themes.csv", index=False)
    return out


def suspect_scores(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    edwin_chapters = set(df[df["characters_mentioned"].str.contains("Edwin Drood", na=False)]["chapter"])
    for char in [c for c in CHARACTERS if c != "Edwin Drood"]:
        subset = df[df["characters_mentioned"].str.contains(re.escape(char), na=False)]
        text = " ".join(subset["text"])
        tokens = tokenize(text)
        total = max(len(tokens), 1)
        motive_score = 100 * sum(t in MOTIVE_TERMS for t in tokens) / total
        suspicious_language_score = 100 * sum(t in SUSPICIOUS_TERMS for t in tokens) / total
        chapters = set(subset["chapter"])
        opportunity_score = 10 * len(chapters & edwin_chapters) / max(len(edwin_chapters), 1)
        same_sentence = df[df["characters_mentioned"].str.contains("Edwin Drood", na=False) & df["characters_mentioned"].str.contains(re.escape(char), na=False)]
        opportunity_score += min(len(same_sentence), 10)
        rows.append({
            "suspect": char,
            "motive_score": round(motive_score, 3),
            "opportunity_score": round(opportunity_score, 3),
            "suspicious_language_score": round(suspicious_language_score, 3),
            "suspicion_score": round(motive_score + opportunity_score + suspicious_language_score, 3),
        })
    out = pd.DataFrame(rows).sort_values("suspicion_score", ascending=False)
    out.to_csv(DATA_PROCESSED / "drood_suspect_scores.csv", index=False)
    return out


def extract_clues(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        tokens = tokenize(row["text"])
        suspicious_hits = sorted(set(tokens) & SUSPICIOUS_TERMS)
        motive_hits = sorted(set(tokens) & MOTIVE_TERMS)
        chars = row["characters_mentioned"]
        score = len(suspicious_hits) * 2 + len(motive_hits) + (2 if "John Jasper" in chars else 0)
        if score:
            rows.append({
                "chapter": row["chapter"],
                "quote": row["text"][:350],
                "characters_involved": chars,
                "why_important": f"Contains motif terms: {', '.join(suspicious_hits + motive_hits)}",
                "supports_suspect": "John Jasper" if "John Jasper" in chars else str(chars).split("; ")[0],
                "clue_score": score,
            })
    out = pd.DataFrame(rows).sort_values("clue_score", ascending=False).head(top_n)
    out.to_csv(DATA_PROCESSED / "drood_important_clues.csv", index=False)
    return out


def compare_to_great_expectations(df: pd.DataFrame) -> pd.DataFrame:
    ge = strip_gutenberg(download_text(GREAT_EXPECTATIONS_URL, DATA_RAW / "drood" / "great_expectations.txt"))
    drood_tokens = tokenize(" ".join(df["text"]))
    ge_tokens = tokenize(ge)
    motif_sets = {
        "secrecy": {"secret", "hidden", "mystery", "unknown", "disguise"},
        "crime": {"crime", "murder", "guilt", "convict", "prison", "grave"},
        "emotion": {"love", "fear", "jealous", "anger", "shame", "hope"},
        "identity": {"name", "identity", "orphan", "stranger", "gentleman"},
    }
    rows = []
    for motif, terms in motif_sets.items():
        rows.append({
            "motif": motif,
            "drood_rate_per_1000": round(1000 * sum(t in terms for t in drood_tokens) / max(len(drood_tokens), 1), 3),
            "great_expectations_rate_per_1000": round(1000 * sum(t in terms for t in ge_tokens) / max(len(ge_tokens), 1), 3),
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA_PROCESSED / "drood_dickens_comparison.csv", index=False)
    return out


def make_visuals(freq: pd.DataFrame, by_chapter: pd.DataFrame, cooc: pd.DataFrame, sentiment: pd.DataFrame, suspects: pd.DataFrame) -> None:
    save_bar(freq, "character", "mentions", "Character Mention Frequency", FIGURES / "drood_character_mentions.png")
    top_suspects = suspects.sort_values("suspicion_score", ascending=False)
    save_bar(top_suspects, "suspect", "suspicion_score", "Ranked Suspect Scores", FIGURES / "drood_suspect_scores.png")
    save_bar(sentiment, "character", "suspicious_rate", "Suspicious Language Rate Around Characters", FIGURES / "drood_suspicious_language.png")

    if not cooc.empty:
        graph = nx.Graph()
        for _, row in cooc.iterrows():
            graph.add_edge(row["character_a"], row["character_b"], weight=row["weight"])
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(graph, seed=7)
        weights = [max(1, graph[u][v]["weight"] / 2) for u, v in graph.edges]
        nx.draw_networkx(graph, pos=pos, ax=ax, width=weights, node_color="#9ecae1", edge_color="#666", font_size=8)
        ax.set_title("Character Co-occurrence Network")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(FIGURES / "drood_cooccurrence_network.png", dpi=160)
        plt.close(fig)

    if not by_chapter.empty:
        pivot = by_chapter.pivot_table(index="chapter", columns="character", values="mentions", fill_value=0)
        fig, ax = plt.subplots(figsize=(11, 5))
        pivot.plot(ax=ax)
        ax.set_title("Character Mentions by Chapter")
        ax.set_xlabel("Chapter")
        ax.set_ylabel("Mentions")
        fig.tight_layout()
        fig.savefig(FIGURES / "drood_mentions_by_chapter.png", dpi=160)
        plt.close(fig)


def write_report(suspects: pd.DataFrame, clues: pd.DataFrame, comparison: pd.DataFrame) -> None:
    top = suspects.iloc[0]
    lines = [
        "# Edwin Drood NLP Report",
        "",
        f"Main theory: `{top['suspect']}` is the strongest computational suspect in this scoring model.",
        f"Confidence: medium-low. The novel is unfinished, and the scores are evidence aids rather than proof.",
        "",
        "## Ranked Suspects",
        suspects.to_markdown(index=False),
        "",
        "## Important Clues",
        clues[["chapter", "quote", "characters_involved", "why_important", "supports_suspect"]].to_markdown(index=False),
        "",
        "## Dickens Comparison",
        comparison.to_markdown(index=False),
        "",
        "## Limitations",
        "- Alias matching can over-count common first names.",
        "- Sentiment/theme scoring uses transparent lexicons, not a trained literary model.",
        "- Dickens left the mystery unfinished, so the output supports a theory rather than proving one.",
    ]
    (REPORTS / "drood_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = build_text_table()
    freq, by_chapter, cooc = character_tables(df)
    sentiment = sentiment_theme_by_character(df)
    suspects = suspect_scores(df)
    clues = extract_clues(df)
    comparison = compare_to_great_expectations(df)
    terms = top_terms(df["text"], STOPWORDS, 40)
    terms.to_csv(DATA_PROCESSED / "drood_top_terms.csv", index=False)
    save_bar(terms.head(20), "term", "count", "Drood Top Terms", FIGURES / "drood_top_terms.png")
    make_visuals(freq, by_chapter, cooc, sentiment, suspects)
    write_report(suspects, clues, comparison)


if __name__ == "__main__":
    run()
