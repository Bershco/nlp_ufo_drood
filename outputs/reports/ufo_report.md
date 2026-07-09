# UFO/UAP Report Draft

Unified records loaded: 80494.
Kaggle records: 80332. PURSUE records: 162.
PURSUE rows with extracted document text: 138. Metadata-only PURSUE rows: 24.
Transformer similarity active for this run: False.

## Matching Method
Candidate pairs are blocked by incident year or inferred year range where possible.

The base signals are transformer text similarity, lexical text similarity, date, location, and entity/keyword overlap. When `sentence-transformers` is installed, transformer cosine similarity is the primary text signal and lexical overlap is secondary. If the transformer dependency is unavailable, the pipeline falls back to lexical text similarity. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.

Date similarity is based on absolute day distance, so cross-year near misses such as December 31 versus January 2 are still treated as close. Full-date gaps use tiers from exact day through 365 days; year-only official dates use a weaker same-year/plus-minus-one-year fallback.

Validation labels are relative rank bands over the exported candidate pool: top 3% `likely same event`, next 32% `possibly same event`, and the remainder `probably not same event`. These labels do not mean confirmed identity.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
All exported candidates include formula labels and notes.
Validation labels among all exported candidates: {'probably not same event': 216, 'possibly same event': 106, 'likely same event': 10}.
The top-20 LLM-assisted manual review is `outputs/reports/ufo_manual_validation_completed.csv`.
Validation labels among top 20: {'likely same event': 10, 'possibly same event': 10}.

## Exploration Outputs
- Common terms: `data/processed/ufo_top_terms.csv`.
- Common phrases: `data/processed/ufo_common_phrases.csv`.
- Entity/keyword counts by source: `data/processed/ufo_entity_counts_by_source.csv`.
- Civilian vs official language comparison: `data/processed/ufo_source_language_comparison.csv`.
- Temporal trends: `data/processed/ufo_temporal_trends.csv`.
- Geographic trends: `data/processed/ufo_geographic_trends.csv`.
- Rare sightings: `data/processed/ufo_rare_sightings.csv`.

## Validation Examples
- `possibly same event`: Kaggle `74332` vs PURSUE `State Department UAP Cable 5, Mexico, September 16, 2003`. Reason: next 32% of exported candidates by final score; uses extracted official document text; date is exact or within a few days; score percentile 0.970; direct text similarity is low
- `possibly same event`: Kaggle `73873` vs PURSUE `State Department UAP Cable 5, Mexico, September 16, 2003`. Reason: next 32% of exported candidates by final score; uses extracted official document text; date is exact or within a few days; score percentile 0.967; direct text similarity is low
- `possibly same event`: Kaggle `45969` vs PURSUE `38_143685_box_Incident_Summaries_173-233`. Reason: next 32% of exported candidates by final score; uses extracted official document text; entity/keyword overlap is meaningful; score percentile 0.964; official date is missing or only inferred; official location was not usable
- `likely same event`: Kaggle `59561` vs PURSUE `59_64634_711.5612[7-2852`. Reason: top 3% of exported candidates by final score; uses extracted official document text; date is in a moderately close window; entity/keyword overlap is meaningful; score percentile 1.000; official location was not usable; direct text similarity is low
- `likely same event`: Kaggle `72778` vs PURSUE `DOW-UAP-D48, Department of the Air Force Report, 1996`. Reason: top 3% of exported candidates by final score; uses extracted official document text; date is exact or within a few days; score percentile 0.997; official location was not usable; direct text similarity is low

## Conclusions
The strongest candidates are useful leads, but most are not strong enough to claim confirmed duplicate reports. Extracted official documents improved the evidence quality, while broad historical reports and noisy OCR still create false positives. Date proximity and entity overlap are the most useful automated signals; location is only useful when the official location is specific and terrestrial.

## Data Interpretation Notes
- `pursue_text` in the candidate CSV is a relevant extracted-document snippet when available; otherwise it is a metadata snippet.
- `transformer_similarity` is cosine similarity between the Kaggle report and the best official document chunk when embeddings are available.
- `lexical_text_similarity` is the older token/string overlap score and remains useful as a secondary/fallback signal.
- `pursue_text_kind=metadata_summary` means the official file could not be matched to extracted text and should be treated as weaker evidence.
- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.
- Blank `location_similarity` means location was deliberately ignored rather than scored as a real match.

## Limitations
- Some extracted official records describe file collections, launch summaries, or long historical reports rather than single events.
- OCR quality varies across scanned PDFs; some downloaded files were videos or malformed/unsupported documents.
- The candidate list is a triage artifact for manual validation, not a final claim that the events match.
- Keyword entities are transparent but weaker than a full NER or sentence-embedding pipeline.