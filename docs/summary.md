# Summary

Root doc: [README](../README.md)

This project is structured as a practical assignment solution:

- `nlp_ass5.drood` runs the Edwin Drood analysis end-to-end from public Gutenberg text.
- `nlp_ass5.ufo` implements the UFO/UAP schema, exploration, matching, and manual validation exports.
- `nlp_ass5.run_all` creates folders and runs both pipelines where data is available.

Drood is fully public and runs immediately after dependencies are installed. UFO matching now uses the local Kaggle CSV at `data/raw/ufo/kaggle_ufo.csv`; PURSUE metadata from the public mirror; and manually downloaded public PURSUE documents extracted into `data/manual_extracted/`. The candidate file should still be read as triage, not final evidence of shared events, because some official documents are broad reports or noisy OCR rather than single incident records.

Submission packaging is complete: the top-20 UFO review is finalized, the Drood conclusion distinguishes Neville's surface-language score from Jasper's stronger literary case, the combined Colab presents both assignments, and concise Markdown/PDF reports contain the required figures and conclusions.

## Related Docs

- [Project plan](plan.md)
- [Manual validation](manual_validation.md)
- [Contradictions audit](contradictions_audit.md)
