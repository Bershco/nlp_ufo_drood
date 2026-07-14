# Data Notes

Root doc: [README](../README.md)

## UFO/UAP

Kaggle datasets usually require an authenticated download. The local Kaggle CSV is expected at:

```text
data/raw/ufo/kaggle_ufo.csv
```

PURSUE data can be loaded from:

```text
data/raw/ufo/pursue_metadata.csv
```

If no local PURSUE CSV is present, the script tries a public metadata mirror that preserves links to the official `war.gov` files. The official `war.gov` shell endpoint returned HTTP 403 during setup, so this fallback is documented rather than hidden. Public PURSUE document bundles were downloaded manually, extracted, indexed, and joined back to metadata rows where filenames could be matched.

Manual PURSUE downloads were added under `data/manual_raw/` and extracted into `data/manual_extracted/`. After successful extraction, the original zip archives were deleted at the user's request; extracted files and extracted text remain. Text extraction results are indexed in:

```text
data/processed/pursue_document_text_index.csv
outputs/reports/manual_archive_extraction.csv
outputs/reports/manual_raw_inventory.csv
outputs/reports/manual_zip_cleanup.csv
```

Current extraction summary: 6 archives, 431 extracted files, 175 files with extracted text. Some files are videos, unsupported formats, or malformed/non-PDF files despite a PDF extension; these are inventoried and left in place.

Important interpretation detail: most PURSUE rows now use extracted document text where filenames could be matched. Metadata-only descriptions remain marked as `metadata_summary` in `data/processed/ufo_unified.csv` and are penalized in matching. Blank location scores in the match CSV mean the official location was missing or non-terrestrial; broad terrestrial locations such as `Western United States` are scored as coarse regions against Kaggle state/country/coordinates. PURSUE dates are mixed-quality evidence, so date is scored after retrieval and carries reduced final-score weight.

Current UFO revision outputs also include:

```text
data/processed/ufo_ner_entities.csv
data/processed/ufo_ner_summary.csv
outputs/figures/ufo_geographic_map.html
outputs/figures/ufo_geographic_map_offline.png
outputs/reports/ufo_top20_manual_review_helper.csv
outputs/reports/ufo_top20_manual_review_helper.md
```

Transformer matching is supported and documented in [GPU transformer run](gpu_transformer_run.md). Embedding caches are stored under `data/processed/embedding_cache/` and can be regenerated safely.

NER uses lightweight spaCy `en_core_web_sm` when installed, plus structured fields and UFO-domain lexicons. Fresh environments should run `python -m spacy download en_core_web_sm` after installing `requirements.txt`; without that model the code falls back to the domain/structured entity path.

## Edwin Drood

The script downloads Project Gutenberg eBook 564 from:

```text
https://www.gutenberg.org/files/564/564-0.txt
```

For Dickens comparison, the default earlier work is Great Expectations, Project Gutenberg eBook 1400. More works can be added through the same helper.

## Related Docs

- [Project plan](plan.md)
- [Ambiguities](ambiguities.md)
