# UFO/UAP Report Draft

Unified records loaded: 162.
Kaggle records: 0. PURSUE records: 162.

## Matching Method
Candidate pairs are blocked by incident year where possible. Final score is:

`0.35 * text + 0.25 * location + 0.25 * date + 0.15 * entity`

## Candidate Matches
No candidate matches were generated. Add `data/raw/ufo/kaggle_ufo.csv` and rerun.

## Limitations
- Kaggle data access is credentialed and must be supplied locally.
- Official records can be redacted or broad historical files rather than single-event reports.
- Keyword entities are transparent but weaker than full NER.