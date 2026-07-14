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
- [x] Relative-rank validation labels and notes implemented for all exported candidates, with top-20 review exported.
- [x] Top-20 manual review helper CSV/Markdown exported.
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
- [x] Suspect scoring by motive, opportunity, and suspicious language.
- [x] Important clues table.
- [x] Comparison hook against at least one earlier Dickens novel.
- [x] Final markdown report generation.

## Submission Artifacts

- [x] README for GitHub.
- [x] Markdown documentation graph.
- [x] At least three visualizations per implemented full pipeline.
- [x] Summary for student and future assistant.
- [x] Colab-compatible notebook entry point.
- [x] Contradictions audit created for final consistency review.
