# Project Plan

Root doc: [README](../README.md)

## Feature Breakdown

1. Project foundation
   - Initialize git.
   - Add Python package, dependencies, output folders, and root documentation.
   - Keep all markdown reachable from `README.md`.

2. UFO/UAP assignment
   - Load Kaggle UFO sightings from `data/raw/ufo/kaggle_ufo.csv`.
   - Load PURSUE metadata from official/mirror CSV or user-supplied file.
   - Normalize both sources into one schema.
   - Explore words, phrases, object shapes, dates, locations, and source language.
   - Match records with blocking by date/location and weighted similarity.
   - Export top candidates and a manual validation template.

3. Edwin Drood assignment
   - Download Project Gutenberg eBook 564.
   - Strip Gutenberg boilerplate.
   - Split into chapters, paragraphs, and sentences.
   - Detect main characters through aliases.
   - Produce mention, chapter, co-occurrence, sentiment/theme, suspect, clue, and comparison outputs.

4. Reports and verification
   - Generate markdown summaries from computed outputs.
   - Re-read the PDF requirements and map every requested item to code/output.
   - Document limitations, ambiguous data-access issues, and plug-in alternatives.

## Testing Plan

- Unit-level checks are embedded as assertions in loaders where practical.
- Run `python -m nlp_ass5.run_all` for an end-to-end smoke test.
- Inspect generated CSVs and figures under `outputs/`.
- Use `docs/requirements_checklist.md` as the final coverage audit.

## Related Docs

- [Requirements checklist](requirements_checklist.md)
- [Data notes](data_notes.md)
- [Manual validation](manual_validation.md)
- [Ambiguities](ambiguities.md)
- [Summary](summary.md)
