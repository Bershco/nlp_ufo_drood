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
- [x] Date scoring distinguishes exact day, near days, weeks, months, and same-year distance.
- [x] Blocking implemented to avoid full all-pairs comparison.
- [x] Weighted final score implemented.
- [x] Candidate match export implemented.
- [x] Relative-rank validation labels and notes implemented for all exported candidates, with top-20 review exported.
- [x] Visualization hooks implemented.
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
