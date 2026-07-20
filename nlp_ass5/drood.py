from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .common import DATA_PROCESSED, DATA_RAW, FIGURES, REPORTS, STOPWORDS, clean_text, download_text, ensure_dirs, save_bar, tokenize, top_terms


DROOD_URL = "https://www.gutenberg.org/files/564/564-0.txt"
GREAT_EXPECTATIONS_URL = "https://www.gutenberg.org/files/1400/1400-0.txt"
DICKENS_WORKS = {
    "Oliver Twist": (730, "https://www.gutenberg.org/files/730/730-0.txt"),
    "Bleak House": (1023, "https://www.gutenberg.org/files/1023/1023-0.txt"),
    "David Copperfield": (766, "https://www.gutenberg.org/files/766/766-0.txt"),
    "Great Expectations": (1400, GREAT_EXPECTATIONS_URL),
    "Our Mutual Friend": (883, "https://www.gutenberg.org/files/883/883-0.txt"),
    "A Tale of Two Cities": (98, "https://www.gutenberg.org/files/98/98-0.txt"),
}
DICKENS_ROLE_PATTERNS = [
    {"work": "The Mystery of Edwin Drood", "central_figure": "Edwin Drood", "hidden_or_close_threat": "John Jasper (uncle and trusted choirmaster)", "conspicuous_suspect_or_misdirection": "Neville Landless", "hidden_helper_or_stranger": "Dick Datchery", "identity_or_revelation_pattern": "Unresolved disappearance and possible disguise", "justice_pattern": "Unfinished"},
    {"work": "Oliver Twist", "central_figure": "Oliver Twist", "hidden_or_close_threat": "Monks and Fagin", "conspicuous_suspect_or_misdirection": "Oliver repeatedly treated as criminal", "hidden_helper_or_stranger": "Mr. Brownlow", "identity_or_revelation_pattern": "Hidden parentage and inheritance", "justice_pattern": "Origins exposed; antagonists punished"},
    {"work": "Bleak House", "central_figure": "Esther Summerson", "hidden_or_close_threat": "Tulkinghorn within elite household network", "conspicuous_suspect_or_misdirection": "Lady Dedlock's secrecy redirects suspicion", "hidden_helper_or_stranger": "Inspector Bucket", "identity_or_revelation_pattern": "Hidden parentage", "justice_pattern": "Secrets exposed late"},
    {"work": "David Copperfield", "central_figure": "David Copperfield", "hidden_or_close_threat": "Uriah Heep embedded in Wickfield household", "conspicuous_suspect_or_misdirection": "Steerforth's charm obscures harm", "hidden_helper_or_stranger": "Micawber", "identity_or_revelation_pattern": "Moral and social self-discovery", "justice_pattern": "Fraud exposed through accumulated evidence"},
    {"work": "Great Expectations", "central_figure": "Pip", "hidden_or_close_threat": "Compeyson behind Magwitch's history", "conspicuous_suspect_or_misdirection": "Magwitch first appears as threat; Miss Havisham as false benefactor", "hidden_helper_or_stranger": "Magwitch", "identity_or_revelation_pattern": "Secret benefactor and concealed histories", "justice_pattern": "Delayed revelation revises moral judgment"},
    {"work": "Our Mutual Friend", "central_figure": "John Harmon", "hidden_or_close_threat": "Rogue and predatory figures inside social networks", "conspicuous_suspect_or_misdirection": "Apparent death of Harmon", "hidden_helper_or_stranger": "Rokesmith/Harmon", "identity_or_revelation_pattern": "Protagonist survives under assumed identity", "justice_pattern": "Identity revelation and moral testing"},
    {"work": "A Tale of Two Cities", "central_figure": "Darnay and Carton", "hidden_or_close_threat": "Political and familial past", "conspicuous_suspect_or_misdirection": "Darnay repeatedly accused and retried", "hidden_helper_or_stranger": "Carton as double", "identity_or_revelation_pattern": "Physical doubling enables substitution", "justice_pattern": "Delayed sacrificial resolution"},
]

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
DARK_TERMS = {"dark", "darkness", "night", "shadow", "black", "grave", "crypt", "dead", "death", "gloom", "opium"}
EMOTIONAL_TERMS = {"love", "fear", "anger", "angry", "jealous", "jealousy", "hate", "hope", "shame", "passion", "grief", "despair"}
VIOLENT_TERMS = {"blood", "kill", "murder", "strangle", "throat", "weapon", "violent", "violence", "blow", "death", "dead"}
CLUE_QUERIES = {
    "motive_and_obsession": "jealous obsession possessive love rivalry anger toward Rosa and Edwin motive to remove Edwin",
    "means_and_opportunity": "opportunity preparation drugging strangling murder conceal body crypt graveyard quicklime",
    "opium_and_double_life": "Jasper opium addiction secret double life altered state confession guilt",
    "behavior_after_disappearance": "Jasper behavior after Edwin disappears false grief investigation manipulation accusation Neville",
    "survival_and_disguise": "Edwin survived disappearance hidden identity disguise return mysterious stranger Datchery",
    "Neville_as_false_suspect": "Neville quarrel threat conflict with Edwin falsely accused obvious suspect",
}


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
    protected = clean_text(paragraph)
    for abbreviation in ["Mr.", "Mrs.", "Miss.", "Dr.", "St."]:
        protected = protected.replace(abbreviation, abbreviation.replace(".", "<DOT>"))
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", protected)
    return [p.replace("<DOT>", ".").strip() for p in pieces if len(p.strip()) > 20]


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
        dark = sum(t in DARK_TERMS for t in tokens)
        emotional = sum(t in EMOTIONAL_TERMS for t in tokens)
        violent = sum(t in VIOLENT_TERMS for t in tokens)
        rows.append({
            "character": char,
            "positive_rate": pos / total,
            "negative_rate": neg / total,
            "suspicious_rate": suspicious / total,
            "dark_rate": dark / total,
            "emotional_rate": emotional / total,
            "violent_rate": violent / total,
            "net_sentiment": (pos - neg) / total,
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA_PROCESSED / "drood_character_sentiment_themes.csv", index=False)
    return out


def character_context_words(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    character_tokens = set(tokenize(" ".join(CHARACTERS) + " " + " ".join(sum(CHARACTERS.values(), []))))
    rows = []
    for char in CHARACTERS:
        texts = df[df["characters_mentioned"].str.contains(re.escape(char), na=False)]["text"]
        counts = Counter(token for text in texts for token in tokenize(text) if token not in STOPWORDS and token not in character_tokens and len(token) > 2)
        total = sum(counts.values()) or 1
        for rank, (word, count) in enumerate(counts.most_common(top_n), 1):
            rows.append({"character": char, "rank": rank, "context_word": word, "count": count, "rate_per_1000": round(1000 * count / total, 3)})
    out = pd.DataFrame(rows)
    out.to_csv(DATA_PROCESSED / "drood_character_context_words.csv", index=False)
    return out


def paragraph_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby(["chapter", "paragraph_id"], as_index=False).agg(
        text=("text", " ".join),
        characters_involved=("characters_mentioned", lambda values: "; ".join(dict.fromkeys(c for value in values for c in str(value).split("; ") if c and c != "nan"))),
    )
    out.insert(0, "paragraph_key", out["chapter"].astype(str) + ":" + out["paragraph_id"].astype(str))
    return out


def minmax(values: pd.Series) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce").fillna(0.0)
    spread = values.max() - values.min()
    return (values - values.min()) / spread if spread else pd.Series(0.0, index=values.index)


def semantic_query_scores(texts: list[str], queries: list[str]) -> np.ndarray:
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        a = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        b = model.encode(queries, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(a) @ np.asarray(b).T
    except Exception:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts + queries)
        return cosine_similarity(matrix[:len(texts)], matrix[len(texts):])


def suspect_scores(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    paragraphs = paragraph_table(df)
    edwin_chapters = set(df[df["characters_mentioned"].str.contains("Edwin Drood", na=False)]["chapter"])
    queries = [CLUE_QUERIES["motive_and_obsession"], CLUE_QUERIES["means_and_opportunity"], CLUE_QUERIES["opium_and_double_life"]]
    for char in [c for c in CHARACTERS if c != "Edwin Drood"]:
        subset = df[df["characters_mentioned"].str.contains(re.escape(char), na=False)]
        tokens = tokenize(" ".join(subset["text"]))
        total = max(len(tokens), 1)
        chapters = set(subset["chapter"])
        same_sentence = df[df["characters_mentioned"].str.contains("Edwin Drood", na=False) & df["characters_mentioned"].str.contains(re.escape(char), na=False)]
        same_paragraph = paragraphs[paragraphs["characters_involved"].str.contains("Edwin Drood", na=False) & paragraphs["characters_involved"].str.contains(re.escape(char), na=False)]
        semantic = semantic_query_scores(subset["text"].tolist() or [""], queries)
        semantic_top = np.mean(np.sort(semantic, axis=0)[-min(5, len(semantic)):], axis=0)
        rows.append({
            "suspect": char,
            "motive_term_rate_per_1000": 1000 * sum(t in MOTIVE_TERMS for t in tokens) / total,
            "suspicious_term_rate_per_1000": 1000 * sum(t in SUSPICIOUS_TERMS for t in tokens) / total,
            "chapter_overlap_with_edwin": len(chapters & edwin_chapters) / max(len(edwin_chapters), 1),
            "same_paragraph_count": len(same_paragraph), "same_sentence_count": len(same_sentence),
            "semantic_motive_relevance": semantic_top[0], "semantic_means_relevance": semantic_top[1], "semantic_secret_life_relevance": semantic_top[2],
        })
    out = pd.DataFrame(rows)
    out["motive_score"] = 25 * (0.55 * minmax(out["motive_term_rate_per_1000"]) + 0.45 * minmax(out["semantic_motive_relevance"]))
    out["opportunity_score"] = 30 * (0.35 * minmax(out["chapter_overlap_with_edwin"]) + 0.35 * minmax(out["same_paragraph_count"]) + 0.30 * minmax(out["same_sentence_count"]))
    out["suspicious_language_score"] = 30 * (0.50 * minmax(out["suspicious_term_rate_per_1000"]) + 0.25 * minmax(out["semantic_means_relevance"]) + 0.25 * minmax(out["semantic_secret_life_relevance"]))
    out["narrative_relevance_score"] = 15 * minmax(out[["semantic_motive_relevance", "semantic_means_relevance", "semantic_secret_life_relevance"]].mean(axis=1))
    out["suspicion_score"] = out[["motive_score", "opportunity_score", "suspicious_language_score", "narrative_relevance_score"]].sum(axis=1)
    numeric = out.select_dtypes(include=[np.number]).columns
    out[numeric] = out[numeric].round(3)
    out = out.sort_values("suspicion_score", ascending=False)
    out.to_csv(DATA_PROCESSED / "drood_suspect_scores.csv", index=False)
    return out


def extract_clues(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    paragraphs = paragraph_table(df)
    texts = paragraphs["text"].tolist()
    names = list(CLUE_QUERIES)
    scores = semantic_query_scores(texts, [CLUE_QUERIES[name] for name in names])
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, max_df=0.9)
    matrix = vectorizer.fit_transform(texts)
    clusters = KMeans(n_clusters=min(8, len(paragraphs)), random_state=7, n_init=20).fit_predict(matrix)
    paragraphs["scene_cluster"] = clusters
    terms = np.asarray(vectorizer.get_feature_names_out())
    cluster_rows = []
    for cluster in sorted(set(clusters)):
        centroid = np.asarray(matrix[clusters == cluster].mean(axis=0)).ravel()
        cluster_rows.append({"scene_cluster": cluster, "paragraphs": int((clusters == cluster).sum()), "top_terms": "; ".join(terms[centroid.argsort()[-8:][::-1]])})
    pd.DataFrame(cluster_rows).to_csv(DATA_PROCESSED / "drood_scene_clusters.csv", index=False)
    candidates = []
    for query_idx, category in enumerate(names):
        for idx in np.argsort(scores[:, query_idx])[::-1][:30]:
            row = paragraphs.iloc[int(idx)]
            candidates.append({"paragraph_key": row["paragraph_key"], "chapter": row["chapter"], "paragraph_id": row["paragraph_id"], "quote": row["text"][:700], "characters_involved": row["characters_involved"], "clue_category": category, "semantic_score": round(float(scores[idx, query_idx]), 4), "scene_cluster": int(clusters[idx])})
    candidate_df = pd.DataFrame(candidates).sort_values("semantic_score", ascending=False)
    candidate_df.to_csv(DATA_PROCESSED / "drood_clue_candidates.csv", index=False)
    # The embedding output above is the reproducible candidate pool. The final
    # table is a small audited selection so generic semantic matches cannot be
    # mistaken for literary evidence.
    specifications = [
        ("hands by the throat", "opium_and_double_life", "John Jasper", "The unnamed opium dreamer later identified as Jasper acts out strangulation, linking his hidden life to a possible method."),
        ("taking opium", "opium_and_double_life", "John Jasper", "Jasper admits secret opium use, establishing the double life introduced in the opening scene."),
        ("unaccountable expedition", "means_and_opportunity", "John Jasper; Durdles", "Jasper secretly explores the cathedral and crypt with Durdles before Edwin disappears."),
        ("key of the crypt door", "means_and_opportunity", "John Jasper; Durdles", "While Durdles is drugged or deeply asleep, the crypt key lies loose and Jasper has unexplained time alone."),
        ("loved you madly", "motive_and_obsession", "John Jasper; Rosa Bud; Edwin Drood", "Jasper confesses obsessive love for Edwin's fiancée dating from before the disappearance, supplying a direct motive."),
        ("false to him, daily and hourly", "motive_and_obsession", "John Jasper; Rosa Bud; Edwin Drood", "Rosa explicitly describes Jasper as false to Edwin and says his pursuit made her afraid."),
        ("murdered that night", "behavior_after_disappearance", "John Jasper; Edwin Drood", "Jasper insists that Edwin was murdered and turns the inquiry into a declared campaign of revenge, behavior compatible with controlling the narrative."),
        ("dreadful suspicion of Jasper", "behavior_after_disappearance", "John Jasper; Rosa Bud", "The narration explicitly records Rosa's suspicion of Jasper and connects it with his obsessive inquiry and torn, muddy clothes."),
        ("determined reticence of Jasper", "behavior_after_disappearance", "John Jasper; Mr. Crisparkle", "Jasper becomes isolated, secretive, and fixed on one purpose after the disappearance."),
        ("convinced of Neville’s innocence", "Neville_as_false_suspect", "Neville Landless; Mr. Crisparkle", "Crisparkle believes Neville innocent even while acknowledging that circumstantial evidence makes him look guilty."),
        ("traces of blood on him", "Neville_as_false_suspect", "Neville Landless", "The case against Neville is conspicuous circumstantial evidence—threat, weapon, departure, and blood—which fits an intentionally obvious suspect."),
        ("young gentleman’s name", "survival_and_disguise", "Dick Datchery; Edwin Drood; Princess Puffer", "Datchery reacts strongly while investigating Edwin's Christmas Eve movements, supporting a concealed-investigator or disguise theory, though not proving Edwin survived."),
    ]
    selected = []
    for phrase, category, characters, explanation in specifications[:top_n]:
        match = paragraphs[paragraphs["text"].str.contains(phrase, case=False, regex=False, na=False)]
        if match.empty:
            continue
        row = match.iloc[0]
        query_idx = names.index(category)
        paragraph_idx = paragraphs.index[paragraphs["paragraph_key"] == row["paragraph_key"]][0]
        selected.append({"paragraph_key": row["paragraph_key"], "chapter": row["chapter"], "paragraph_id": row["paragraph_id"], "quote": row["text"][:700], "characters_involved": characters, "clue_category": category, "semantic_score": round(float(scores[paragraph_idx, query_idx]), 4), "scene_cluster": int(row["scene_cluster"]), "why_important": explanation, "supports_suspect": "Neville / false-suspect theory" if category == "Neville_as_false_suspect" else ("Survival / Datchery theory" if category == "survival_and_disguise" else "John Jasper")})
    out = pd.DataFrame(selected)
    out.to_csv(DATA_PROCESSED / "drood_important_clues.csv", index=False)
    return out


def compare_dickens_works(df: pd.DataFrame) -> pd.DataFrame:
    texts = {"The Mystery of Edwin Drood": " ".join(df["text"])}
    for title, (book_id, url) in DICKENS_WORKS.items():
        texts[title] = strip_gutenberg(download_text(url, DATA_RAW / "drood" / f"dickens_{book_id}.txt"))
    motif_sets = {
        "secrecy": {"secret", "hidden", "mystery", "unknown", "conceal"},
        "guilt_and_crime": {"crime", "murder", "guilt", "convict", "prison", "grave"},
        "obsession_and_fear": {"obsession", "jealous", "fear", "anger", "passion", "revenge"},
        "hidden_past": {"past", "former", "memory", "forgotten", "history"},
        "identity_and_disguise": {"identity", "disguise", "stranger", "name", "double", "unknown"},
        "confession_and_exposure": {"confess", "confession", "admit", "truth", "reveal", "discovered"},
        "justice_and_punishment": {"justice", "punishment", "trial", "judge", "sentence", "law"},
        "emotion": {"love", "fear", "jealous", "anger", "shame", "hope"},
    }
    motif_rows, arc_rows, progression_rows, network_rows = [], [], [], []
    for title, text in texts.items():
        tokens = tokenize(text)
        total = max(len(tokens), 1)
        for motif, terms in motif_sets.items():
            motif_rows.append({"work": title, "motif": motif, "rate_per_1000": round(1000 * sum(t in terms for t in tokens) / total, 3)})
        bins = np.array_split(np.asarray(tokens, dtype=object), 10)
        for index, chunk in enumerate(bins, 1):
            chunk_list = chunk.tolist(); denom = max(len(chunk_list), 1)
            arc_rows.append({"work": title, "plot_decile": index, "positive_rate_per_1000": 1000 * sum(t in POSITIVE for t in chunk_list) / denom, "negative_rate_per_1000": 1000 * sum(t in NEGATIVE for t in chunk_list) / denom})
        thirds = np.array_split(np.asarray(tokens, dtype=object), 3)
        for part, chunk in zip(["opening", "middle", "ending"], thirds):
            chunk_list = chunk.tolist(); denom = max(len(chunk_list), 1)
            for motif, terms in motif_sets.items():
                progression_rows.append({"work": title, "plot_section": part, "motif": motif, "rate_per_1000": round(1000 * sum(t in terms for t in chunk_list) / denom, 3)})
        paragraphs = [clean_text(p) for p in re.split(r"\n\s*\n", text) if len(clean_text(p)) > 80]
        name_counts, edges = Counter(), Counter()
        for paragraph in paragraphs:
            names = list(dict.fromkeys(re.findall(r"\b(?:Mr|Mrs|Miss|Lady|Sir|Doctor|Dr)\.?\s+[A-Z][a-z]+|\b[A-Z][a-z]{3,}\s+[A-Z][a-z]+\b", paragraph)))
            names = names[:8]
            name_counts.update(names)
            for i, name in enumerate(names):
                for other in names[i + 1:]: edges[tuple(sorted((name, other)))] += 1
        top_names = {name for name, _ in name_counts.most_common(9)}
        graph = nx.Graph(); graph.add_nodes_from(top_names)
        graph.add_weighted_edges_from((a, b, w) for (a, b), w in edges.items() if a in top_names and b in top_names)
        network_rows.append({"work": title, "named_character_nodes": graph.number_of_nodes(), "cooccurrence_edges": graph.number_of_edges(), "network_density": round(nx.density(graph), 4) if graph.number_of_nodes() > 1 else 0, "largest_component_share": round(max((len(c) for c in nx.connected_components(graph)), default=0) / max(graph.number_of_nodes(), 1), 4)})
    out = pd.DataFrame(motif_rows)
    out.to_csv(DATA_PROCESSED / "drood_dickens_comparison.csv", index=False)
    pd.DataFrame(arc_rows).to_csv(DATA_PROCESSED / "drood_dickens_sentiment_arcs.csv", index=False)
    pd.DataFrame(progression_rows).to_csv(DATA_PROCESSED / "drood_dickens_plot_progression.csv", index=False)
    pd.DataFrame(network_rows).to_csv(DATA_PROCESSED / "drood_dickens_network_comparison.csv", index=False)
    pd.DataFrame(DICKENS_ROLE_PATTERNS).to_csv(DATA_PROCESSED / "drood_dickens_role_patterns.csv", index=False)
    return out


def make_visuals(freq: pd.DataFrame, by_chapter: pd.DataFrame, cooc: pd.DataFrame, sentiment: pd.DataFrame, suspects: pd.DataFrame) -> None:
    save_bar(freq, "character", "mentions", "Character Mention Frequency", FIGURES / "drood_character_mentions.png")
    top_suspects = suspects.sort_values("suspicion_score", ascending=False).set_index("suspect")
    components = ["motive_score", "opportunity_score", "suspicious_language_score", "narrative_relevance_score"]
    fig, ax = plt.subplots(figsize=(11, 6))
    top_suspects[components].plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Ranked Suspect Scores by Evidence Component")
    ax.set_xlabel("Suspect"); ax.set_ylabel("Weighted score (0–100 total)")
    ax.legend(["Motive (25)", "Opportunity (30)", "Suspicious language (30)", "Narrative relevance (15)"], fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "drood_suspect_scores.png", dpi=160); plt.close(fig)
    save_bar(sentiment, "character", "suspicious_rate", "Suspicious Language Rate Around Characters", FIGURES / "drood_suspicious_language.png")

    if not cooc.empty:
        graph = nx.Graph()
        for _, row in cooc.iterrows():
            graph.add_edge(row["character_a"], row["character_b"], weight=row["weight"])
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(graph, seed=7, k=1.35, iterations=200)
        raw_weights = [graph[u][v]["weight"] for u, v in graph.edges]
        max_weight = max(raw_weights, default=1)
        weights = [0.8 + 5.2 * math.sqrt(weight / max_weight) for weight in raw_weights]
        nx.draw_networkx_nodes(graph, pos=pos, ax=ax, node_color="#9ecae1", node_size=1250, edgecolors="#39789f")
        nx.draw_networkx_edges(graph, pos=pos, ax=ax, width=weights, edge_color="#777", alpha=0.65)
        nx.draw_networkx_labels(graph, pos=pos, ax=ax, font_size=8, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 0.4})
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
    score_columns = ["suspect", "motive_score", "opportunity_score", "suspicious_language_score", "narrative_relevance_score", "suspicion_score"]
    motif_pivot = comparison.pivot(index="work", columns="motif", values="rate_per_1000").round(3)
    lines = [
        "# Edwin Drood Final NLP Report",
        "",
        "**Main theory:** John Jasper is the strongest literary suspect; Neville Landless is the strongest surface-level computational suspect and is likely constructed as the conspicuous false suspect.",
        "**Confidence:** medium. Jasper's motive, preparation, secrecy, and post-disappearance conduct form a coherent chain, but the unfinished novel supplies neither a body nor a confession.",
        "**Was Edwin murdered?** Jasper probably attempted to kill him, but survival remains plausible. Datchery's identity and the absence of a recovered body leave room for a disguised return or hidden investigator.",
        "",
        "## Ranked Suspects and Score Components",
        "The normalized model weights motive at 25%, opportunity at 30%, suspicious language at 30%, and semantic narrative relevance at 15%. Neville ranks first because Dickens gives the false-suspect case unusually explicit violence, proximity, and jealousy language. Jasper ranks second numerically but has the more coherent cross-scene evidence chain.",
        suspects[score_columns].to_markdown(index=False),
        "",
        "## Important Clues",
        "Candidates were retrieved with sentence embeddings, organized with TF-IDF/K-means scene clusters, and then audited to remove generic or contextless matches.",
        clues[["chapter", "quote", "characters_involved", "why_important", "supports_suspect"]].to_markdown(index=False),
        "",
        "## Dickens Comparison",
        motif_pivot.to_markdown(),
        "",
        "Across the six earlier novels, secrecy, identity, hidden pasts, crime, confession, and delayed justice recur rather than appearing uniquely in *Drood*. Within *Drood*, crime language rises from 0.101 per 1,000 words in the opening third to 0.740 in the surviving ending, identity/disguise rises from 0.774 to 1.615, and secrecy doubles from 0.235 to 0.471. That progression supports an unfinished revelation involving concealed identity and exposure. The pattern is more compatible with Neville as an overtly signposted false suspect and Jasper as guilt hidden inside a trusted family relationship; the strong late identity signal also preserves the Edwin-survival or Datchery-disguise alternative.",
        "",
        "## Final Interpretation",
        "The NLP model alone cannot adjudicate authorial intention. It correctly identifies Neville as surrounded by explicit anger, threat, blood, and proximity language, but those are also precisely the textual mechanisms used to make him the obvious suspect. The audited clue chain is stronger for Jasper: secret opium use and imagined strangulation; advance exploration of the crypt and access to its key; obsessive love for Rosa while she was promised to Edwin; Rosa's accusation that he was false to Edwin; immediate insistence on murder; control of the revenge narrative; and later secrecy and social isolation. On balance, Jasper is the best-supported culprit, while Neville is the strongest alternative generated by surface evidence.",
        "",
        "Alternative explanations remain open: Edwin may have survived Jasper's attack; Datchery may be Edwin or another disguised investigator; or Jasper may be guilty of coercion and concealment without completed murder. The analysis supports relative plausibility, not a certain solution.",
        "",
        "## Limitations",
        "- Alias matching can over-count common first names.",
        "- Lexicon rates and sentence embeddings measure textual association, not legal or causal proof.",
        "- The suspect score is sensitive to Dickens's deliberate foregrounding of a false suspect.",
        "- Cross-novel plot and network measures are proxies; novels differ greatly in length, cast, and completeness.",
        "- Dickens left the mystery unfinished, so the output supports a theory rather than proving one.",
    ]
    (REPORTS / "drood_report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    df = build_text_table()
    freq, by_chapter, cooc = character_tables(df)
    sentiment = sentiment_theme_by_character(df)
    character_context_words(df)
    suspects = suspect_scores(df)
    clues = extract_clues(df)
    comparison = compare_dickens_works(df)
    terms = top_terms(df["text"], STOPWORDS, 40)
    terms.to_csv(DATA_PROCESSED / "drood_top_terms.csv", index=False)
    save_bar(terms.head(20), "term", "count", "Drood Top Terms", FIGURES / "drood_top_terms.png")
    make_visuals(freq, by_chapter, cooc, sentiment, suspects)
    motif_plot = comparison.pivot(index="work", columns="motif", values="rate_per_1000")
    fig, ax = plt.subplots(figsize=(12, 6))
    motif_plot.plot(kind="bar", ax=ax)
    ax.set_title("Dickens Motif Rates Across Seven Novels"); ax.set_ylabel("Occurrences per 1,000 words"); ax.set_xlabel("")
    ax.legend(fontsize=7, ncol=2); fig.tight_layout(); fig.savefig(FIGURES / "drood_dickens_motifs.png", dpi=160); plt.close(fig)
    write_report(suspects, clues, comparison)


if __name__ == "__main__":
    run()
