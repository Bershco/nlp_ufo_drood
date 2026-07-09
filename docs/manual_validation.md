# Manual Validation Guide

Root doc: [README](../README.md)

The UFO matcher writes:

```text
outputs/reports/ufo_candidate_matches.csv
outputs/reports/ufo_manual_validation_template.csv
```

Review the top 20 rows and fill:

- `manual_label`: `likely same event`, `possibly same event`, or `probably not same event`.
- `manual_notes`: short evidence-based explanation.

Use these cues:

- Dates: exact day is strong, same month/year is weaker.
- Locations: city/state agreement or short geographic distance is strong. Blank `location_similarity` means the official location was not usable for matching.
- Text: unique objects, motion, color, military references, and rare phrases matter more than generic words like "light".
- Source differences: official records may be redacted, vague, or written in bureaucratic language.
- `pursue_text_kind=metadata_repeated_summary` is a weak signal because the same official metadata description appears on multiple files.

Discuss at least five examples in the final report.

## Related Docs

- [Requirements checklist](requirements_checklist.md)
- [Summary](summary.md)
