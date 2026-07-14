# UFO/UAP Report Draft

Unified records loaded: 80494.
Kaggle records: 80332. PURSUE records: 162.
PURSUE rows with extracted document text: 138. Metadata-only PURSUE rows: 24.
Transformer similarity active for this run: True.

## Matching Method
Candidate retrieval uses broad transformer-based semantic retrieval when embeddings are available, rather than strict date/location blocking. Date and location are weak or missing in many PURSUE records, so they are used as scoring evidence after retrieval instead of hard filters. If transformer embeddings are unavailable, the fallback path still uses year/entity blocking to avoid an all-pairs comparison.

The base signals are transformer text similarity, TF-IDF text similarity, lexical text similarity, date, location, and entity overlap. Entity overlap blends UFO-domain keyword overlap with lightweight spaCy NER (`en_core_web_sm`) when the model is installed. When `sentence-transformers` is installed, transformer cosine similarity is the primary text signal and TF-IDF/lexical overlap are secondary. If the transformer dependency is unavailable, the pipeline falls back to TF-IDF and lexical text similarity. The score is normalized over reliable available signals. Location is ignored only when the PURSUE location is missing or non-terrestrial; broad terrestrial locations such as `Western United States` are scored as coarse geographic regions. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.

Current transformer weights are text 0.60, date 0.15, entity 0.15, and location 0.10. Date weight was deliberately reduced because PURSUE dates are often missing, broad, title-derived, or document/admin dates rather than confidently verified event dates.

Rows with empty Kaggle text or empty official snippets are excluded from semantic candidate matching so identical empty embeddings cannot create false high-similarity pairs.

Date similarity is based on absolute day distance, so cross-year near misses such as December 31 versus January 2 are still treated as close. Full-date gaps use tiers from exact day through 365 days; year-only official dates use a weaker same-year/plus-minus-one-year fallback.

Validation labels are relative rank bands over the exported candidate pool: top 3% `likely same event`, next 32% `possibly same event`, and the remainder `probably not same event`. These labels do not mean confirmed identity.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
All exported candidates include formula labels and notes.
Validation labels among all exported candidates: {'probably not same event': 325, 'possibly same event': 160, 'likely same event': 15}.
The top-20 manual-review working file is `outputs/reports/ufo_manual_validation_completed.csv`.
Validation labels among top 20: {'likely same event': 15, 'possibly same event': 5}.

## Exploration Outputs
- Common terms: `data/processed/ufo_top_terms.csv`.
- Common phrases: `data/processed/ufo_common_phrases.csv`.
- Entity/keyword counts by source: `data/processed/ufo_entity_counts_by_source.csv`.
- spaCy plus domain-lexicon NER entities: `data/processed/ufo_ner_entities.csv` and `data/processed/ufo_ner_summary.csv`.
- Civilian vs official language comparison: `data/processed/ufo_source_language_comparison.csv`.
- Temporal trends: `data/processed/ufo_temporal_trends.csv`.
- Geographic trends: `data/processed/ufo_geographic_trends.csv`.
- Interactive geographic map: `outputs/figures/ufo_geographic_map.html`.
- Offline geographic map image: `outputs/figures/ufo_geographic_map_offline.png`.
- Rare sightings: `data/processed/ufo_rare_sightings.csv`.

## Validation Examples
- `possibly same event`: Kaggle `45360` vs PURSUE `Western US Event`. Reason: next 32% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.970; date support is weak
- `possibly same event`: Kaggle `32454` vs PURSUE `Western US Event`. Reason: next 32% of exported candidates by final score; uses extracted official document text; score percentile 0.968; date support is weak
- `possibly same event`: Kaggle `19347` vs PURSUE `USPER Statement about UAP Sighting`. Reason: next 32% of exported candidates by final score; uses extracted official document text; location has broad geographic support; score percentile 0.966; official date is missing or only inferred
- `likely same event`: Kaggle `10290` vs PURSUE `Western US Event`. Reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 1.000; date support is weak
- `likely same event`: Kaggle `61526` vs PURSUE `Western US Event`. Reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.998; date support is weak

## Conclusions
The strongest candidates are useful leads, but most are not strong enough to claim confirmed duplicate reports. Extracted official documents improved the evidence quality, while broad historical reports and noisy OCR still create false positives. Transformer text similarity is the strongest retrieval signal; spaCy/domain entity overlap and date proximity are useful supporting signals only when they are specific and trustworthy. Location is only useful when the official location is specific and terrestrial.

## Data Interpretation Notes
- `pursue_text` in the candidate CSV is a relevant extracted-document snippet when available; otherwise it is a metadata snippet.
- `transformer_similarity` is cosine similarity between the Kaggle report and the best official document chunk when embeddings are available.
- `tfidf_text_similarity` is explicit TF-IDF cosine similarity over the candidate snippets; it is secondary to transformer similarity when embeddings are active.
- `lexical_text_similarity` is the older token/string overlap score and remains useful as a secondary/fallback signal.
- `ufo_ner_entities.csv` combines lightweight spaCy NER for people, organizations, places, facilities, events, and dates with domain lexicons for military terms, object shapes, colors, and motion terms.
- `pursue_text_kind=metadata_summary` means the official file could not be matched to extracted text and should be treated as weaker evidence.
- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.
- Blank `location_similarity` means location was deliberately ignored because the official location was missing or non-terrestrial.

## Limitations
- Some extracted official records describe file collections, launch summaries, or long historical reports rather than single events.
- OCR quality varies across scanned PDFs; some downloaded files were videos or malformed/unsupported documents.
- Transformer similarity can surface semantically broad matches from long official reports, so date/entity/location support and manual validation remain important.
- The earlier strict year-blocking and lexical-heavy approach could miss plausible semantic matches when official dates were missing or unreliable; the current version uses semantic retrieval first and scores date afterward.
- Earlier empty-text rows could create false perfect embedding similarities; empty Kaggle or official snippets are now excluded before semantic matching.
- The candidate list is a triage artifact for manual validation, not a final claim that the events match.
- Lightweight spaCy NER is stronger than the earlier rule-only extraction, but it can still miss domain-specific bases, redacted names, OCR-damaged places, and UAP-specific phrases.