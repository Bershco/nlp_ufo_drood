# NLP Assignment 5: UFO/UAP and Edwin Drood

This repository contains a compact, reproducible solution scaffold for the two NLP assignments in `nlp_assignments_ufo_edwin_drood.pdf`.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m nlp_ass5.run_all
```

Outputs are written to:

- `data/raw/` for downloaded or manually supplied source files.
- `data/processed/` for structured CSV tables.
- `outputs/figures/` for visualizations.
- `outputs/reports/` for generated markdown/CSV summaries.

The pipeline downloads spaCy's lightweight `en_core_web_sm` model on first use if it is not already installed. Set `UFO_AUTO_DOWNLOAD_SPACY=0` to skip the download and use the structured/domain-entity fallback.

## Assignment Coverage

- UFO/UAP pipeline: unified schema, NLP exploration, lightweight spaCy/domain NER, semantic retrieval/matching, weighted scoring, and manual-validation template.
- Manual PURSUE document bundles: extracted locally, indexed, and used for official document text where matched.
- Edwin Drood pipeline: text preparation, character analysis, suspect scoring, clue extraction, Dickens comparison hooks, visualizations, and generated report.

Kaggle normally requires credentials. In this workspace the zip has been extracted to the expected local CSV path:

```text
data/raw/ufo/kaggle_ufo.csv
```

The PURSUE collector uses the official schema when available and can also ingest a local CSV mirror.
The current run uses PURSUE metadata records. If you obtain an official PURSUE CSV export, place it at `data/raw/ufo/pursue_metadata.csv`.

For Colab submission, open [notebooks/assignment_pipeline.ipynb](notebooks/assignment_pipeline.ipynb). It presents both completed assignments and can clone the repository automatically when opened as a standalone notebook.

Final short reports are available as both Markdown and paginated PDF:

- [UFO/UAP submission report](outputs/reports/ufo_submission_report.pdf)
- [Edwin Drood submission report](outputs/reports/drood_submission_report.pdf)

To rebuild the PDFs locally, run `python3 scripts/render_submission_reports.py` (LibreOffice is required only for this packaging step).

## Documentation Graph

Start here and follow links:

- [Project plan](docs/plan.md)
- [Assignment requirements checklist](docs/requirements_checklist.md)
- [Data notes](docs/data_notes.md)
- [Manual validation guide](docs/manual_validation.md)
- [Ambiguities and decisions](docs/ambiguities.md)
- [GPU transformer run guide](docs/gpu_transformer_run.md)
- [Future upgrade ideas](docs/future_upgrades.md)
- [UFO revision plan](docs/ufo_revision_plan.md)
- [Contradictions audit](docs/contradictions_audit.md)
- [Edwin Drood assignment explanation](docs/drood_assignment_explained.md)
- [Final summary](docs/summary.md)

## Repository Status

This repository is connected to the GitHub remote used for the assignment.
