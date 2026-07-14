# Ambiguities and Decisions

Root doc: [README](../README.md)

## Kaggle Access

The assignment requires the Kaggle UFO dataset, but Kaggle downloads are typically credentialed. Decision: implement a local CSV loader and document the required path instead of embedding credentials or relying on an unofficial copy.

## PURSUE Access and Text

The official `war.gov` UFO page and PDF endpoints may block command-line access. Decision: support local CSV, official-shaped CSV, and a public metadata mirror while preserving official source links in `source_file_or_link`.

Manual public PURSUE downloads were added and text was extracted where possible. Most PURSUE metadata rows now use matched extracted document text. Remaining metadata-only rows are labeled, unusable locations such as `Moon` are ignored for civilian geographic matching, and exact dates are distinguished from inferred year hints.

## NER Requirement

Heavy transformer NER is avoided because it adds runtime and dependency cost. Decision: use lightweight spaCy `en_core_web_sm` NER where available, blended with structured fields and domain lexicons; this keeps the requirement explicit without requiring GPU.

## Dickens Comparison

The PDF asks to compare to previous Dickens works and gives several options. Decision: implement a default comparison to Great Expectations and allow additional Gutenberg IDs to be added.

## Final Theory

Dickens never finished the novel. Decision: produce a ranked evidence-based suspect list, not a claim of certain truth.

## Related Docs

- [Data notes](data_notes.md)
- [Requirements checklist](requirements_checklist.md)
- [Future upgrade ideas](future_upgrades.md)
