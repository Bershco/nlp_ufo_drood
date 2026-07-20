# Requirements Checklist

Root doc: [README](../README.md)

## Assignment 1: UFO/UAP

- [x] Unified schema implemented in `nlp_ass5.ufo`.
- [x] Kaggle loader supports local CSV input.
- [x] PURSUE loader supports local/remote metadata CSV.
- [x] PURSUE public document zip bundles extracted locally and indexed.
- [x] Successfully extracted public document zips removed after extraction at user request.
- [x] Extracted PURSUE PDF text used where matched to metadata rows.
- [x] Text, date, location, and entity/keyword similarity signals implemented.
- [x] Explicit TF-IDF text similarity implemented as a secondary/fallback signal.
- [x] Lightweight spaCy NER implemented and blended with domain entity extraction for places/locations, dates, organizations/military terms, shapes, colors, and motion terms.
- [x] Date scoring distinguishes exact day, near days, weeks, months, and same-year distance.
- [x] Blocking/retrieval implemented to avoid naive all-pairs comparison; transformer runs use broad semantic top-k retrieval because official date/location metadata is weak.
- [x] Weighted final score implemented.
- [x] Date score weight reduced because PURSUE dates are not always confidently event dates.
- [x] Candidate match export implemented.
- [x] Candidate export includes all required reporting fields plus source pointers for manual inspection.
- [x] Automated relative-rank bands and notes implemented for all exported candidates, with a separate blank manual-label field in the top-20 review export.
- [x] Top-20 manual review helper CSV/Markdown exported.
- [x] Top 20 candidates manually labeled and annotated by the student.
- [x] At least five manually reviewed candidate pairs discussed in the final report.
- [x] Visualization hooks implemented.
- [x] Interactive geographic map exported in addition to static figures.
- [x] Offline geographic PNG exported for submissions without internet access.
- [x] Full run completed with local Kaggle CSV and PURSUE metadata mirror.
- [x] Common words, phrases, source-language comparison, entity counts, temporal trends, geographic trends, and rare sightings exported.

## Assignment 2: Edwin Drood

- [x] Gutenberg download and boilerplate stripping.
- [x] Chapter, paragraph, sentence table.
- [x] Character aliases and mentions.
- [x] Character frequency by chapter.
- [x] Co-occurrence network export and visualization.
- [x] Sentiment/theme analysis around characters.
- [x] Frequent contextual words near each character exported.
- [x] Normalized suspect scoring by motive, opportunity, suspicious language, and semantic narrative relevance, with raw features retained.
- [x] Hybrid embedding/TF-IDF clue retrieval, scene clustering, and audited 12-clue table.
- [x] Comparison against all six Dickens works listed in the assignment across motifs, sentiment arcs, plot progression, character roles, and network structure.
- [x] Final theory, confidence, strongest clues, alternatives, and limitations documented.
- [x] Final markdown and concise submission reports generated.
- [x] Drood notebook narrative, tables, figures, comparison, and conclusion completed.

## Submission Artifacts

- [x] README for GitHub.
- [x] Markdown documentation graph.
- [x] At least three visualizations per implemented full pipeline.
- [x] Summary for student and future assistant.
- [x] Colab-compatible notebook entry point.
- [x] UFO notebook narrative includes methods, selected outputs, figures, manual validation, conclusion, and limitations.
- [x] Contradictions audit created for final consistency review.
- [x] Combined Colab notebook covers both completed assignments and includes standalone repository setup.
- [x] UFO/UAP concise report exported as a paginated PDF with three figures.
- [x] Edwin Drood 2–4 page report exported as a paginated PDF with three figures, ranked suspects, important clues, and Dickens comparison.
