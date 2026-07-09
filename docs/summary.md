# Summary

Root doc: [README](../README.md)

This project is structured as a practical assignment solution:

- `nlp_ass5.drood` runs the Edwin Drood analysis end-to-end from public Gutenberg text.
- `nlp_ass5.ufo` implements the UFO/UAP schema, exploration, matching, and manual validation exports.
- `nlp_ass5.run_all` creates folders and runs both pipelines where data is available.

The main known limitation is official PURSUE document access. Drood is fully public and runs immediately after dependencies are installed. UFO matching now uses the local Kaggle CSV at `data/raw/ufo/kaggle_ufo.csv`; PURSUE metadata is loaded from a local CSV when available or from the public metadata mirror. The current candidate file should be read as metadata-level triage, not final evidence of shared events.

Next steps before submission:

1. Run `python -m nlp_ass5.run_all`.
2. Fill the manual validation labels for the top 20 UFO candidates.
3. Convert generated markdown/figures into the requested short report or Colab.

## Related Docs

- [Project plan](plan.md)
- [Manual validation](manual_validation.md)
