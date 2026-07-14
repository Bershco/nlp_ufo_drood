# Future Upgrade Ideas

Root doc: [README](../README.md)

This file documents practical ways to make the UFO/UAP matching pipeline stronger after the assignment baseline is complete. These are not required for the current submission, but they explain where the current method is weakest and what would improve it most.

## Current Matching Limitation

The two sources do not describe events in the same style.

Kaggle rows are usually short civilian summaries: a sentence or two about lights, shapes, motion, date, and location. PURSUE records are official documents, cables, transcripts, OCR scans, file collections, launch summaries, and sometimes broad historical reports. A transformer can find semantic similarity between these texts, but it can also match general UFO language rather than the same event.

The best upgrades should therefore improve event-level evidence, not only text similarity.

## 1. Cross-Encoder or LLM Reranking

The current pipeline uses bi-encoder embeddings: each text is embedded independently, and cosine similarity ranks candidate pairs. This is fast and works well for first-pass retrieval, but it cannot deeply compare two texts in context.

A reranker would take the top candidate pairs from the current pipeline and score each pair directly. A cross-encoder, for example, reads both texts together and can judge whether the pair describes the same incident, not just similar UFO vocabulary.

Practical implementation:

- Keep the current embedding search to produce the top 300-500 candidates.
- Run a reranker only on those candidates.
- Give the reranker both snippets plus structured fields: dates, locations, shapes, motion words, witness type, and source type.
- Add a new column such as `rerank_score`.
- Sort by a blended score, for example `0.65 * rerank_score + 0.35 * current_final_score`.

Possible models:

- `cross-encoder/ms-marco-MiniLM-L-6-v2` for a lightweight baseline.
- `BAAI/bge-reranker-large` for stronger semantic reranking.
- A local or API LLM prompt that outputs structured labels and evidence notes.

Expected benefit:

This is probably the highest-value easy upgrade. It should reduce false positives where both texts discuss pilots, lights, or saucers but not the same event.

Risk:

Cross-encoders are slower than embeddings, so they should be used only after blocking and first-pass retrieval.

## 2. Structured Event Facet Extraction

Instead of comparing raw text only, extract comparable event facets from both sources. This makes the matching more explainable and less dependent on noisy OCR wording. A first lightweight version now exists through canonical shape normalization, structured fields, domain lexicons, and spaCy `en_core_web_sm` NER; the future upgrade is to make these facets richer and more reliable.

Useful facets:

- Date and date precision.
- Location and location confidence.
- Object shape: light, sphere, disk, triangle, fireball, cigar, formation.
- Color: red, orange, blue, green, white, silver.
- Motion: hovering, accelerating, turning, descending, disappearing, formation flight.
- Witness type: pilot, military, police, civilian, crew, radar operator.
- Agency or setting: Air Force, NASA, FBI, State Department, base, aircraft, launch, radar.
- Quantity: one object, multiple objects, formation, several lights.
- Sound: silent, no sound, explosion, humming.

Practical implementation:

- Add a `ufo_event_facets.csv` table with one row per record or document chunk.
- Extend the deterministic regex/keyword rules that are now in the baseline.
- Add a larger transformer-based NER model later if higher recall is needed.
- Compute separate similarities for each facet and include them in the candidate export.

Expected benefit:

This helps distinguish "same kind of sighting" from "same event." For example, two texts both saying "pilot saw a bright object" is weak; two texts sharing date, object color, motion, and witness type is much stronger.

Risk:

Rules can miss synonyms and OCR variants. Keep raw extracted facet evidence in the CSV so errors are inspectable.

## 3. Stronger Embedding Model Comparison

The current GPU run used sentence-transformer embeddings as the main text signal. A better embedding model may improve retrieval, especially for short query texts matched against long official snippets.

Models worth testing:

- `sentence-transformers/all-mpnet-base-v2`: solid general baseline, already practical.
- `BAAI/bge-large-en-v1.5`: strong general embedding model, often better for retrieval.
- `intfloat/e5-large-v2`: strong retrieval model; use the recommended `query:` and `passage:` prefixes.
- `BAAI/bge-m3`: useful if multilingual or mixed-domain records matter.

Practical implementation:

- Add a script option or environment variable for model name, already partly supported by `UFO_EMBEDDING_MODEL`.
- Run each model and export `ufo_candidate_matches_<model_slug>.csv`.
- Compare overlap among the top 20, top 100, and top 500.
- Prefer models whose top candidates have stronger date/location/facet support, not just higher cosine scores.

Expected benefit:

This can improve recall and ranking. It is easy to test on the GPU machine because the code already supports model swapping and cached embeddings.

Risk:

Bigger models are not automatically better. They may increase semantic false positives if the official documents are broad and OCR-heavy.

## 4. Query-Passage Retrieval Framing

Kaggle descriptions behave like short queries, while official chunks behave like longer passages. Some embedding models perform better when this distinction is explicit.

Practical implementation:

- For E5-style models, encode Kaggle text as `query: <text>`.
- Encode PURSUE chunks as `passage: <text>`.
- Keep the plain-text encoding path for models that do not expect prefixes.
- Document the prefixing behavior in the report.

Expected benefit:

This can make the model better at retrieving official passages that answer or correspond to short civilian reports.

Risk:

Prefixes help only for models trained that way. They should not be applied blindly to every model.

## 5. Better Official Document Chunking

The current method chunks official document text for embedding, but OCR documents often contain headers, page numbers, form labels, repeated release text, and unrelated pages. Better chunking would improve the quality of `pursue_text`.

Practical implementation:

- Remove repeated boilerplate before chunking.
- Split on page boundaries and form sections when available.
- Prefer chunks that contain event-like terms: dates, shapes, motion, witness words, location words.
- Penalize chunks that are mostly metadata, release stamps, page headers, or OCR garbage.
- Keep the best chunk per candidate in `pursue_text`.

Expected benefit:

This should reduce cases where a Kaggle report is matched to a broad official file but the selected snippet is not a clear event description.

Risk:

Aggressive cleanup can remove useful text. Keep the original extracted text and only clean a derived field.

## 6. OCR Cleanup and Text Quality Scoring

Some official snippets are noisy scans. OCR noise can create bad token overlap, weak entity extraction, and misleading embeddings.

Practical implementation:

- Add a text quality score per official chunk.
- Detect high OCR noise using unusual character ratio, very short token ratio, repeated punctuation, and low alphabetic-token density.
- Normalize common OCR artifacts where safe.
- Downweight chunks below a quality threshold.
- Add `pursue_text_quality` to candidate outputs.

Expected benefit:

This makes the ranking more robust and gives a clear reason when a candidate is weak because official text quality is poor.

Risk:

OCR quality metrics are approximate. They should downweight, not delete, unless text is clearly empty or unusable.

## 7. Better Location Handling

The current location logic deliberately ignores unusable official locations such as `Moon`, `Low Earth Orbit`, or missing values. Broad terrestrial official locations such as `Western United States`, `United States`, and several named sea/region labels are now scored with an offline coarse geospatial matcher against Kaggle state/country/coordinates. The exploration also includes both an interactive Leaflet map and an offline PNG map. The remaining upgrade is better extraction and scoring of more specific official locations from document text.

Practical implementation:

- Geocode reliable official place names when they exist.
- Extract locations from official document text, not only metadata.
- Treat countries, states, cities, bases, and airspace differently.
- Add distance bands: same city, same region, same country, far away.
- Penalize strong location contradictions instead of merely giving low similarity.

Expected benefit:

This would make "same event" claims more credible. Date and text similarity alone are often insufficient.

Risk:

Geocoding can introduce errors, especially with old place names, military bases, and vague locations.

## 8. Better Date Reasoning

The current date score handles exact days, near-day gaps, month-scale gaps, year ranges, and missing dates, and date weight has been reduced because official dates are mixed-quality evidence. A stronger version could reason about publication dates versus event dates.

Practical implementation:

- Separate event date, report date, release date, document date, and inferred date.
- Extract dates from official text chunks, not only metadata titles.
- Prefer dates near the matched chunk over dates elsewhere in a long document.
- Add candidate notes when a date is inferred rather than explicit.

Expected benefit:

This would reduce false confidence from official files whose metadata date is not the sighting date.

Risk:

Official documents often mention many dates. The pipeline must distinguish event dates from administrative dates.

## 9. Negative Evidence and Contradiction Features

The current score mostly rewards positive evidence. It does not strongly penalize contradictions unless location/date similarity is low.

Useful contradictions:

- Dates are far apart and both exact.
- Locations are far apart and both specific.
- One report says multiple objects while the other says one object.
- Colors or shapes are incompatible.
- One source describes a launch/spacecraft event while the other describes a ground-level civilian sighting.

Practical implementation:

- Add `contradiction_score`.
- Subtract it from the final score after positive evidence is calculated.
- Include contradiction notes in `manual_notes`.

Expected benefit:

This makes the label "likely same event" harder to reach for broadly similar but factually incompatible pairs.

Risk:

Contradiction extraction can be brittle. Start with conservative high-confidence contradictions only.

## 10. Cluster-Based Event Discovery

Instead of scoring only pairwise matches, cluster reports by date window, location, and text/facet similarity. Then look for clusters containing both Kaggle and PURSUE records.

Practical implementation:

- Build clusters within date windows.
- Use embeddings plus structured facets inside each window.
- Mark mixed-source clusters as high-interest.
- Export cluster summaries with representative texts and records.

Expected benefit:

This can reveal events with multiple civilian reports and one official record, which is stronger than one pair alone.

Risk:

Clustering adds complexity and can be harder to explain than pairwise matching. It should be an optional analysis layer.

## 11. Human-in-the-Loop Calibration

The current labels are relative rank bands, which satisfies the assignment requirement and avoids pretending the formulas prove identity. A stronger version would use a small manually reviewed set to calibrate thresholds.

Practical implementation:

- Manually label 50-100 pairs.
- Track which signals were persuasive or misleading.
- Fit simple thresholds or a logistic regression model.
- Keep the model interpretable and report feature weights.

Expected benefit:

This turns subjective ranking bands into empirically calibrated labels.

Risk:

Manual labels may be inconsistent. The labeling guide should define "likely", "possible", and "probably not" clearly.

## Recommended Upgrade Order

1. Expand structured event facets beyond the current lightweight spaCy/domain NER and shape baseline.
2. Improve official chunking and OCR quality scoring.
3. Run a stronger embedding model comparison.
4. Add cross-encoder or LLM reranking for top candidates.
5. Add contradiction penalties.
6. Add better location/date extraction from official chunks.
7. Try cluster-based discovery.
8. Calibrate with more manual labels.

This order improves evidence quality before adding more complex model layers.
