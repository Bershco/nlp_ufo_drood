# UFO/UAP Report Draft

Unified records loaded: 80494.
Kaggle records: 80332. PURSUE records: 162.

## Matching Method
Candidate pairs are blocked by incident year or inferred year range where possible.

The base signals are text, date, location, and entity/keyword overlap. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Repeated PURSUE metadata summaries are penalized because they are document descriptions, not extracted incident text.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
The top-20 manual review sheet is `outputs/reports/ufo_manual_validation_template.csv`.

## Data Interpretation Notes
- `pursue_text` is currently the PURSUE metadata description unless local extracted PDF text is added later.
- `pursue_text_kind=metadata_repeated_summary` means several official records share the same broad description; those rows should be treated as weak leads.
- `pursue_date_precision` distinguishes exact dates from year-only or missing dates.
- Blank `location_similarity` means location was deliberately ignored rather than scored as a real match.

## Limitations
- PURSUE matching is metadata-level unless official PDFs are downloaded and extracted.
- Some official records describe file collections or historical launch summaries, not single events.
- The candidate list is a triage artifact for manual validation, not a final claim that the events match.
- Keyword entities are transparent but weaker than a full NER or sentence-embedding pipeline.