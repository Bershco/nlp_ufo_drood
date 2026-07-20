# UFO/UAP Final Report

Unified records loaded: 80555.
Kaggle records: 80332. PURSUE records: 223.
PURSUE rows with extracted document text: 199 (138 metadata-attached rows and 61 standalone documents). Metadata-only PURSUE rows: 24.
Transformer similarity active for this run: True.

## Matching Method
Candidate retrieval uses broad transformer-based semantic retrieval when embeddings are available, rather than strict date/location blocking. Date and location are weak or missing in many PURSUE records, so they are used as scoring evidence after retrieval instead of hard filters. If transformer embeddings are unavailable, the fallback path still uses year/entity blocking to avoid an all-pairs comparison.

The base signals are transformer text similarity, TF-IDF text similarity, lexical text similarity, date, location, and entity overlap. Entity overlap blends UFO-domain keyword overlap with lightweight spaCy NER (`en_core_web_sm`) when the model is installed. When `sentence-transformers` is installed, transformer cosine similarity is the primary text signal and TF-IDF/lexical overlap are secondary. If the transformer dependency is unavailable, the pipeline falls back to TF-IDF and lexical text similarity. The score is normalized over reliable available signals. Location is ignored only when the PURSUE location is missing or non-terrestrial; broad terrestrial locations such as `Western United States` are scored as coarse geographic regions. Metadata-only PURSUE rows are penalized because they are document descriptions rather than extracted incident text.

Current transformer weights are text 0.60, date 0.15, entity 0.15, and location 0.10. Date weight was deliberately reduced because PURSUE dates are often missing, broad, title-derived, or document/admin dates rather than confidently verified event dates.

Rows with empty Kaggle text or empty official snippets are excluded from semantic candidate matching so identical empty embeddings cannot create false high-similarity pairs.

Date similarity is based on absolute day distance, so cross-year near misses such as December 31 versus January 2 are still treated as close. Full-date gaps use tiers from exact day through 365 days; year-only official dates use a weaker same-year/plus-minus-one-year fallback.

Automated rank bands divide the exported candidate pool into the top 3%, next 32%, and remaining candidates. Their text resembles the three requested review labels for prioritization, but they are not human judgments or claims of event identity. Human decisions belong only in `manual_label` and `manual_notes`.

## Candidate Matches
Candidate matches are exported to `outputs/reports/ufo_candidate_matches.csv`.
All exported candidates include automated rank bands and notes, plus separate blank fields for human review.
Automated rank bands among all exported candidates: {'probably not same event': 325, 'possibly same event': 160, 'likely same event': 15}.
The top-20 manual-review working file is `outputs/reports/ufo_manual_validation_completed.csv`.
Completed human labels among top 20: {'possibly same event': 19, 'probably not same event': 1}.

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

### Rank 1: Kaggle `10290` vs PURSUE `Western US Event`
**Manual classification:** possibly same event.
Both texts describe combinations of orange/red orb-like lights, and Santa Cruz is compatible with the official record's broad Western United States location. This makes the pair thematically plausible. However, the official 2023 value cannot be verified as the event date, while the Kaggle report is from 2012, and the color/orb pattern is common across many sightings. The pair is therefore possible, not verified.

### Rank 3: Kaggle `68270` vs PURSUE `38_143685_box_Incident_Summaries_101-172`
**Manual classification:** possibly same event.
The descriptions share a similar sequence of unidentified lights or objects, but the official incident-summary collection supplies neither a usable location nor a reliable event date for this particular passage. The semantic model retrieved a comparable event description, yet the low direct TF-IDF and NER overlap show that the wording and specific entities are not distinctive enough to establish identity.

### Rank 6: Kaggle `26520` vs PURSUE `Western US Event`
**Manual classification:** possibly same event.
The descriptions again share orange/red orb characteristics, but the Kaggle location is East Glastonbury, Connecticut, whereas the official location is Western United States. The deliberately low location score of 0.15 captures this conflict. Because PURSUE dates may be administrative and the visual description remains similar, the pair is retained as possible, although geographic evidence argues against it.

### Rank 9: Kaggle `68579` vs PURSUE `38_143685_box_Incident_Summaries_101-172`
**Manual classification:** probably not same event.
This is the clearest negative example. The Kaggle report is from Cabo San Lucas, Mexico, while the PURSUE passage has no usable location. The reported durations and event descriptions differ, TF-IDF overlap is zero, and named-entity overlap is zero. Semantic similarity alone appears to have retrieved the same broad class of sighting rather than the same incident, so the pair is classified as probably not the same event.

### Rank 18: Kaggle `19347` vs PURSUE `USPER Statement about UAP Sighting`
**Manual classification:** possibly same event.
Both reports concern orb-like phenomena and the Kaggle sighting occurred in Friday Harbor, Washington, which is compatible with the official record's very broad United States label. Nevertheless, that location covers the entire country and the official date is unavailable. The shared orb vocabulary makes this a useful lead, but it does not provide enough specificity for a likely-match claim.

## Conclusions
The system found several plausible thematic correspondences, especially reports involving orange or red orbs, but insufficient date, location, and distinctive-event evidence prevents confidently establishing a cross-source duplicate. Manual review classified 19 pairs as possibly the same event and one as probably not the same event; none met a defensible threshold for likely identity. This is a substantive result rather than a pipeline failure: redaction, missing incident dates, broad released locations, and other limits of the declassified PURSUE material remove precisely the evidence needed to confirm identity across sources. Transformer similarity was effective for retrieving comparable sighting narratives, while TF-IDF, NER, location, and cautious date evidence helped reveal when semantic similarity represented a shared event type rather than one historical occurrence.

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
- Semantic retrieval is performed before date scoring because official dates are frequently missing or cannot be identified confidently as incident dates.
- Rows with empty Kaggle or official text are excluded before semantic matching.
- The candidate list is a triage artifact for manual validation, not a final claim that the events match.
- Lightweight spaCy NER can miss domain-specific bases, redacted names, OCR-damaged places, and UAP-specific phrases.
- Declassified releases may redact or omit precise dates, locations, names, units, sensor details, and other identifying context; this directly weakens date, location, and entity comparison.
