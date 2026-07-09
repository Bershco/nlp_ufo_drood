# Ambiguities and Decisions

Root doc: [README](../README.md)

## Kaggle Access

The assignment requires the Kaggle UFO dataset, but Kaggle downloads are typically credentialed. Decision: implement a local CSV loader and document the required path instead of embedding credentials or relying on an unofficial copy.

## PURSUE Access and Text

The official `war.gov` UFO page and PDF endpoints may block command-line access. Decision: support local CSV, official-shaped CSV, and a public metadata mirror while preserving official source links in `source_file_or_link`.

The current text used for matching is PURSUE metadata, not full document text. That is weaker than the assignment ideal, so the matcher now labels repeated metadata summaries, ignores unusable locations such as `Moon` for civilian geographic matching, and distinguishes exact dates from inferred year hints.

## NER Requirement

Full spaCy NER is optional because model downloads are heavy for a timed assignment. Decision: implement lightweight regex/entity keyword extraction and keep the design modular so spaCy can be plugged in later.

## Dickens Comparison

The PDF asks to compare to previous Dickens works and gives several options. Decision: implement a default comparison to Great Expectations and allow additional Gutenberg IDs to be added.

## Final Theory

Dickens never finished the novel. Decision: produce a ranked evidence-based suspect list, not a claim of certain truth.

## Related Docs

- [Data notes](data_notes.md)
- [Requirements checklist](requirements_checklist.md)
