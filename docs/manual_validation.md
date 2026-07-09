# Manual Validation Guide

Root doc: [README](../README.md)

The UFO matcher writes:

```text
outputs/reports/ufo_candidate_matches.csv
outputs/reports/ufo_manual_validation_template.csv
outputs/reports/ufo_manual_validation_completed.csv
```

The candidate CSV contains formula labels for all exported candidates. The completed top-20 review file is generated for the assignment's manual-validation requirement.

When running on a GPU machine with `sentence-transformers` installed, rerun `python -m nlp_ass5.ufo` so `transformer_similarity` is populated and labels are recalculated from the transformer-primary score. If transformer dependencies are unavailable, `transformer_similarity` stays blank and the pipeline uses the lexical fallback.

If reviewing or changing labels by hand, use:

- `manual_label`: `likely same event`, `possibly same event`, or `probably not same event`.
- `manual_notes`: short evidence-based explanation.

Use these cues:

- Dates: exact day is strong, same month/year is weaker.
- Locations: city/state agreement or short geographic distance is strong. Blank `location_similarity` means the official location was not usable for matching.
- Text: unique objects, motion, color, military references, and rare phrases matter more than generic words like "light".
- Source differences: official records may be redacted, vague, or written in bureaucratic language.
- `pursue_text_kind=extracted_document_text` means the snippet came from a downloaded public document.
- `pursue_text_kind=metadata_summary` is weaker because no extracted document text was matched for that official row.

Discuss at least five examples in the final report.

Current labeling is rank-aware over the exported candidate pool:

- `likely same event`: top 3%.
- `possibly same event`: next 32%.
- `probably not same event`: remaining 65%.

These bands sit inside the requested ranges of 2-8%, 15-50%, and 40-80%. The label is a triage priority, not proof that the two reports describe the same event.

## Related Docs

- [Requirements checklist](requirements_checklist.md)
- [Summary](summary.md)
