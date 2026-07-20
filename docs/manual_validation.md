# Manual Validation Guide

Root doc: [README](../README.md)

The UFO matcher writes:

```text
outputs/reports/ufo_candidate_matches.csv
outputs/reports/ufo_manual_validation_template.csv
outputs/reports/ufo_manual_validation_completed.csv
```

The candidate CSV contains automated rank bands for all exported candidates. The top-20 working file is initialized with blank human-review fields; rerunning the pipeline does not overwrite that file after it exists.

When running on a GPU machine or local environment with `sentence-transformers` installed, rerun `python -m nlp_ass5.ufo` so `transformer_similarity` is populated and labels are recalculated from the transformer-primary score. If transformer dependencies are unavailable and no matching embedding cache exists, `transformer_similarity` stays blank and the pipeline uses the TF-IDF/lexical fallback.

If reviewing or changing labels by hand, use:

- `automated_rank_band`: automated triage priority only; do not treat it as a human decision.
- `automated_rank_notes`: automated explanation of the rank band and scoring evidence.
- `manual_label`: `likely same event`, `possibly same event`, or `probably not same event`.
- `manual_notes`: short evidence-based explanation.

Use these cues:

- Dates: exact day is strong, same month/year is weaker.
- Locations: city/state agreement or short geographic distance is strong. Broad official locations such as `Western United States` are scored as coarse regions. Blank `location_similarity` means the official location was missing or non-terrestrial.
- Entities: `domain_entity_similarity` captures UFO-domain terms such as shape/color/motion/military words; `ner_similarity` captures lightweight spaCy named-entity overlap from text plus structured fields; `entity_similarity` is the blended score used in ranking.
- Text: unique objects, motion, color, military references, and rare phrases matter more than generic words like "light".
- Source differences: official records may be redacted, vague, or written in bureaucratic language.
- `pursue_text_kind=extracted_document_text` means the snippet came from a downloaded public document.
- `pursue_text_kind=standalone_extracted_document` means an extracted Release 1/2/3 document had no matched metadata row and was added directly as an official record.
- `pursue_text_kind=metadata_summary` is weaker because no extracted document text was matched for that official row.
- `pursue_pdf_date_evidence` and `pursue_pdf_location_evidence` contain mentions extracted from the PDF. They are review aids, not automatically asserted event metadata: a document can mention publication dates, historical dates, authors' locations, or several incidents.
- `outputs/reports/ufo_top20_manual_review_helper.csv` and `.md` provide review prompts and source pointers for the current top 20.

Discuss at least five examples in the final report.

Automated triage is rank-aware over the exported candidate pool:

- `likely same event`: top 3%.
- `possibly same event`: next 32%.
- `probably not same event`: remaining 65%.

These bands sit inside the requested ranges of 2-8%, 15-50%, and 40-80%. They are only triage priorities. The separate `manual_label` column is the assignment answer and must be filled by the student after inspecting each pair.

## Related Docs

- [Requirements checklist](requirements_checklist.md)
- [Summary](summary.md)
