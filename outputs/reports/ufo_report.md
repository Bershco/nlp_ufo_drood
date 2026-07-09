# UFO/UAP Report Draft

Unified records loaded: 80494.
Kaggle records: 80332. PURSUE records: 162.
PURSUE rows with extracted document text: 138. Metadata-only PURSUE rows: 24.

## Matching Method
Candidate pairs are blocked by incident year or inferred year range where possible.

The base signals are text, date, location, and entity/keyword overlap. The score is normalized over reliable available signals. Location is ignored when the PURSUE location is missing, non-terrestrial, or too broad. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
The top-20 manual review sheet is `outputs/reports/ufo_manual_validation_template.csv`.

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