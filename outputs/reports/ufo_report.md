# UFO/UAP Report Draft

Unified records loaded: 80494.
Kaggle records: 80332. PURSUE records: 162.
PURSUE rows with extracted document text: 138. Metadata-only PURSUE rows: 24.

## Matching Method
Candidate pairs are blocked by incident year or inferred year range where possible.

The base signals are text, date, location, and entity/keyword overlap. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
The top-20 LLM-assisted manual review is `outputs/reports/ufo_manual_validation_completed.csv`.
Validation labels among top 20: {'probably not same event': 11, 'possibly same event': 9}.

## Exploration Outputs
- Common terms: `data/processed/ufo_top_terms.csv`.
- Common phrases: `data/processed/ufo_common_phrases.csv`.
- Entity/keyword counts by source: `data/processed/ufo_entity_counts_by_source.csv`.
- Civilian vs official language comparison: `data/processed/ufo_source_language_comparison.csv`.
- Temporal trends: `data/processed/ufo_temporal_trends.csv`.
- Geographic trends: `data/processed/ufo_geographic_trends.csv`.
- Rare sightings: `data/processed/ufo_rare_sightings.csv`.

## Validation Examples
- `possibly same event`: Kaggle `59561` vs PURSUE `59_64634_711.5612[7-2852`. Reason: uses extracted official document text; date is in a moderately close window; entity/keyword overlap is meaningful; official location was not usable; direct text similarity is low
- `possibly same event`: Kaggle `72778` vs PURSUE `DOW-UAP-D48, Department of the Air Force Report, 1996`. Reason: uses extracted official document text; date is exact or within a few days; official location was not usable; direct text similarity is low
- `possibly same event`: Kaggle `57484` vs PURSUE `59_214434_SP 16 [7.18.1963]`. Reason: uses extracted official document text; date is exact or within a few days; official location was not usable; direct text similarity is low
- `probably not same event`: Kaggle `19618` vs PURSUE `State Department UAP Cable 4, Ashgabat, Turkmenistan, November 5, 2004`. Reason: uses extracted official document text; date is in a moderately close window; entity/keyword overlap is meaningful; direct text similarity is low
- `probably not same event`: Kaggle `27343` vs PURSUE `38_143685_box_Incident_Summaries_173-233`. Reason: uses extracted official document text; entity/keyword overlap is meaningful; official date is missing or only inferred; official location was not usable

## Conclusions
The strongest candidates are useful leads, but most are not strong enough to claim confirmed duplicate reports. Extracted official documents improved the evidence quality, while broad historical reports and noisy OCR still create false positives. Date proximity and entity overlap are the most useful automated signals; location is only useful when the official location is specific and terrestrial.

## Data Interpretation Notes
- `pursue_text` in the candidate CSV is a relevant extracted-document snippet when available; otherwise it is a metadata snippet.
- `pursue_text_kind=metadata_summary` means the official file could not be matched to extracted text and should be treated as weaker evidence.
- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.
- Blank `location_similarity` means location was deliberately ignored rather than scored as a real match.

## Limitations
- Some extracted official records describe file collections, launch summaries, or long historical reports rather than single events.
- OCR quality varies across scanned PDFs; some downloaded files were videos or malformed/unsupported documents.
- The candidate list is a triage artifact for manual validation, not a final claim that the events match.
- Keyword entities are transparent but weaker than a full NER or sentence-embedding pipeline.