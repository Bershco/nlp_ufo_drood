# Contradictions Audit

Root doc: [README](../README.md)

Audit date: 2026-07-14.

Scope reviewed: Python scripts in `nlp_ass5/`, repository markdown files in `docs/`, `README.md`, report markdown files in `outputs/reports/`, `notebooks/assignment_pipeline.ipynb`, and local-only explanation markdown under `/home/roee/Desktop/assignment_explanation/`.

## Fixed During This Audit

### 1. Repository Status Was Stale

- Side A: `README.md` said the project was a local git repository initialized for later GitHub remote setup.
- Side B: the repo is already connected to and pushed to `github.com:Bershco/nlp_ufo_drood.git`.
- Resolution: updated `README.md` to state that the repo is connected to the GitHub remote.

### 2. UFO Matching Was Described as Date/Location Blocking

- Side A: `README.md`, `docs/plan.md`, and the local UFO explanation summary described the UFO matcher as date/year or date/location blocking.
- Side B: `nlp_ass5/ufo.py` now uses broad transformer semantic top-k retrieval when embeddings are available, and only uses year/entity blocking as fallback.
- Resolution: updated the docs and local explanation summary to describe semantic retrieval first, with date/location scoring afterward.

### 3. Data Notes Claimed Metadata-Only UFO Implementation

- Side A: `docs/data_notes.md` said optional PDF extraction could be added and that the current implementation used metadata descriptions and source links.
- Side B: `nlp_ass5/manual_docs.py`, `nlp_ass5/ufo.py`, and `data/processed/pursue_document_text_index.csv` show that manual PURSUE documents are extracted and matched into the unified table.
- Resolution: updated `docs/data_notes.md` to describe the current extracted-document path and new UFO outputs.

### 4. GPU Run Doc Described Old Fallback and Old Blocking

- Side A: `docs/gpu_transformer_run.md` said the fallback was lexical similarity and that date/entity blocking narrowed Kaggle rows before transformer scoring.
- Side B: current code uses TF-IDF plus lexical fallback, and transformer runs perform broad semantic top-k retrieval.
- Resolution: updated `docs/gpu_transformer_run.md`.

### 5. UFO Report Generator Reintroduced "LLM-Assisted" Language

- Side A: `outputs/reports/ufo_report.md` had already been manually patched to say "manual-review working file."
- Side B: `nlp_ass5/ufo.py` still generated "LLM-assisted manual review."
- Resolution: updated the generator so reruns keep the corrected wording.

### 6. UFO Report Overstated Date as a Strong Signal

- Side A: `outputs/reports/ufo_report.md` said date proximity and entity overlap were the most useful automated signals.
- Side B: current top-20 UFO candidates have weak or unusable date/location support; transformer text similarity is the main retrieval signal.
- Resolution: updated `nlp_ass5/ufo.py` and `outputs/reports/ufo_report.md` to say transformer text similarity is the strongest retrieval signal, while date/entity are supporting signals only when specific and trustworthy.

### 7. Broad Terrestrial PURSUE Locations Were Ignored

- Side A: `outputs/reports/ufo_candidate_matches.csv` contained blank `location_similarity` values for rows whose PURSUE location was `Western United States` or `United States`.
- Side B: those locations are broad but still terrestrial and useful as coarse evidence when Kaggle state/country/coordinates are available.
- Resolution: updated `nlp_ass5/ufo.py` so missing and non-terrestrial locations are still ignored, but broad terrestrial regions are scored with an offline coarse geospatial matcher. The candidate CSV now includes richer Kaggle location strings with city, state, country, and coordinates where available.

## Remaining Contradictions or Tensions

### 1. UFO Manual Validation File Is Generated, Not Truly Manually Reviewed Yet

- Side A: assignment requires manual review of the top 20 candidate matches.
- Side B: `outputs/reports/ufo_manual_validation_completed.csv` is generated automatically from rank bands and notes; your own human review has not yet been applied.
- Why it matters: the file name says `completed`, but the current contents are automated starting labels.
- Current mitigation: `outputs/reports/ufo_top20_manual_review_helper.md` explicitly tells you to edit labels/notes if your judgment differs.
- Manual decision needed: manually inspect the top 20 and edit `ufo_manual_validation_completed.csv` before final submission.

### 2. Interactive Map Depends on Internet Tile Loading

- Side A: `outputs/figures/ufo_geographic_map.html` is an interactive Leaflet/OpenStreetMap map.
- Side B: the HTML loads Leaflet assets and map tiles from public CDNs; offline viewing will not fully render the base map.
- Why it matters: if the notebook/report is viewed offline, the map may not display as expected.
- Current mitigation: `outputs/figures/ufo_geographic_map_offline.png` is generated from local coordinates and works offline.
- Manual decision needed: use the offline PNG in the submitted notebook/report if the submission environment has no internet access.

## Deferred Non-UFO Tension

### Drood Numeric Suspect Ranking Conflicts With Qualitative Clues

- Side A: `outputs/reports/drood_report.md` states that Neville Landless is the strongest computational suspect.
- Side B: `outputs/reports/drood_report.md` also lists 8 clue rows supporting John Jasper and 0 supporting Neville directly in the extracted clue table.
- Supporting data: `data/processed/drood_suspect_scores.csv` ranks Neville first because opportunity dominates; `data/processed/drood_important_clues.csv` mostly supports Jasper.
- Why it matters: the final literary conclusion could look incoherent if it says Neville while the strongest displayed textual clues point to Jasper.
- Status: deferred until the Drood assignment pass.

## Manual Next Steps

1. Open `outputs/reports/ufo_top20_manual_review_helper.md`.
2. For each top-20 pair, inspect:
   - `kaggle_text` and `pursue_text`;
   - `kaggle_date` and `pursue_date`;
   - `kaggle_location` and `pursue_location`;
   - `transformer_similarity`, `tfidf_text_similarity`, `date_similarity`, `location_similarity`, and `entity_similarity`;
   - `pursue_extracted_text_path` when present.
3. Edit `outputs/reports/ufo_manual_validation_completed.csv`:
   - keep or change `manual_label`;
   - add your own reasoning to `manual_notes`;
   - mark broad semantic matches with poor date/location support as weaker unless the text details are very specific.
4. Pick at least five reviewed examples for the final report. Include both the automated view and your manual judgment.
5. Use `outputs/figures/ufo_geographic_map_offline.png` for an offline-safe geographic figure. The interactive HTML map can remain as an extra artifact.
