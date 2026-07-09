# Manual Validation Guide

Root doc: [README](../README.md)

The UFO matcher writes:

```text
outputs/reports/ufo_candidate_matches.csv
outputs/reports/ufo_manual_validation_template.csv
outputs/reports/ufo_manual_validation_completed.csv
```

The candidate CSV contains formula labels for all exported candidates. The completed top-20 review file is generated for the assignment's manual-validation requirement.

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

Current labeling is rank-aware. `likely same event` is reserved for the strongest candidates relative to the exported pool when they also have extracted official text and multiple supporting signals such as close date, entity overlap, or usable location. It does not mean the match is confirmed.

## Related Docs

- [Requirements checklist](requirements_checklist.md)
- [Summary](summary.md)
