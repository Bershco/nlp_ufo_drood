# Summary

Root doc: [README](../README.md)

This project is structured as a practical assignment solution:

- `nlp_ass5.drood` runs the Edwin Drood analysis end-to-end from public Gutenberg text.
- `nlp_ass5.ufo` implements the UFO/UAP schema, exploration, matching, and manual validation exports.
- `nlp_ass5.run_all` creates folders and runs both pipelines where data is available.

The main known limitation is external data access. Drood is fully public and should run immediately after dependencies are installed. UFO matching requires the Kaggle CSV at `data/raw/ufo/kaggle_ufo.csv`; PURSUE metadata can be loaded from a local CSV or public metadata mirror.

Next steps before submission:

1. Download the Kaggle UFO CSV.
2. Run `python -m nlp_ass5.run_all`.
3. Fill the manual validation labels for the top 20 UFO candidates.
4. Convert generated markdown/figures into the requested short report or Colab.

## Related Docs

- [Project plan](plan.md)
- [Manual validation](manual_validation.md)
