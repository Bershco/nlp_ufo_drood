# UFO Revision Plan

Root doc: [README](../README.md)

This plan tracks the requested UFO-only review and implementation pass from July 13, 2026.

## Goals

1. Clarify where the current solution used simple tokenization versus NER.
2. Add or document NER more explicitly for the assignment requirement.
3. Improve shape/object extraction and documentation.
4. Add a map-based geographic output, not only a matplotlib bar chart.
5. Document the refined date similarity scheme and reassess official date reliability.
6. Reduce date weight in matching from `0.25` to `0.15`; move the `0.10` difference into text and entity similarity.
7. Add explicit TF-IDF similarity as a pipeline signal, while keeping sentence-transformer similarity as the primary signal.
8. Revisit blocking so weak date/location metadata does not wrongly exclude plausible matches.
9. Verify candidate CSV coverage against the assignment's required fields.
10. Create a manual-review helper file for the top 20 candidate pairs.
11. Document an actual failed/replaced method, not only dataset limitations.
12. Keep future-improvements documentation current after any implemented upgrades.

## Work Items

- [x] Add explicit NER/entity extraction outputs for UFO exploration.
- [x] Add shape extraction from official text and document how Kaggle labels are normalized.
- [x] Add map-based geographic visualization output.
- [x] Add TF-IDF candidate similarity output.
- [x] Adjust final score weights and report the new weights.
- [x] Change blocking to semantic retrieval over broad source comparisons instead of strict date/location blocking.
- [x] Rebuild UFO outputs.
- [x] Verify candidate reporting fields.
- [x] Add top-20 manual-inspection helper CSV/Markdown.
- [x] Update assignment explanation and repo markdown docs.
- [x] Run final validation checks.

## Notes

- Video and audio extraction are intentionally out of scope for this pass.
- The current transformer output can be regenerated locally from `.venv` or on the Windows GPU machine. The embedding cache is ignored by git.

## Findings

- Common words and phrases still use tokenization because the assignment asks for frequent words/phrases, not only entities. NER is now added as a separate output so both requirements are covered.
- Kaggle shape labels are normalized into canonical shapes, and official shapes are inferred from document text where no clean field exists.
- Geographic exploration now includes both a static matplotlib summary and an interactive Leaflet map HTML.
- PURSUE date reliability is mixed. In the current unified table, 96 of 162 PURSUE records have no exact date, 56 have day-level dates, and 10 have year-only dates. The day-level values come from metadata/title/document context and cannot always be confidently treated as event dates, so date is no longer a hard blocking signal and its final-score weight was reduced from `0.25` to `0.15`.
- Candidate reporting has the required fields: Kaggle ID, PURSUE ID/file, dates and locations in both sources, snippets from both reports, similarity score, and explanation.
