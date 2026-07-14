# Summary

Root doc: [README](../README.md)

This project is structured as a practical assignment solution:

- `nlp_ass5.drood` runs the Edwin Drood analysis end-to-end from public Gutenberg text.
- `nlp_ass5.ufo` implements the UFO/UAP schema, exploration, matching, and manual validation exports.
- `nlp_ass5.run_all` creates folders and runs both pipelines where data is available.

Drood is fully public and runs immediately after dependencies are installed. UFO matching now uses the local Kaggle CSV at `data/raw/ufo/kaggle_ufo.csv`; PURSUE metadata from the public mirror; and manually downloaded public PURSUE documents extracted into `data/manual_extracted/`. The candidate file should still be read as triage, not final evidence of shared events, because some official documents are broad reports or noisy OCR rather than single incident records.

Next steps before submission:

1. Review the UFO top-20 helper and manually edit labels/notes where your judgment differs.
2. Reconcile the Drood final interpretation if you want the literary conclusion to favor Jasper rather than the current computational top suspect.
3. Convert generated markdown/figures into the requested short report or Colab.

## Related Docs

- [Project plan](plan.md)
- [Manual validation](manual_validation.md)
- [Contradictions audit](contradictions_audit.md)
