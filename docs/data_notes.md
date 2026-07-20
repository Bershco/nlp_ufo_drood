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

Current extraction summary: 6 archives and 431 extracted files. Text was extracted from all 175 genuine PDFs. The other 256 entries are 134 non-text/unsupported files (94 MP4, 22 JPG, 16 PNG, and 2 extensionless files) plus 122 macOS `__MACOSX/._*.pdf` metadata sidecars that have PDF-like names but are not PDF documents. Those sidecars account for every recorded PDF extraction error; no genuine PDF failed text extraction.

Important interpretation detail: most PURSUE rows now use extracted document text where filenames could be matched. Metadata-only descriptions remain marked as `metadata_summary` in `data/processed/ufo_unified.csv` and are penalized in matching. Blank location scores in the match CSV mean the official location was missing or non-terrestrial; broad terrestrial locations such as `Western United States` are scored as coarse regions against Kaggle state/country/coordinates. PURSUE dates are mixed-quality evidence, so date is scored after retrieval and carries reduced final-score weight.

All 175 text-bearing downloaded documents are now represented. The 114 unique Release 1 texts matched to metadata rows remain attached there; the other 61 texts are standalone PURSUE rows (`2` from Release 1, `6` from Release 2, and `53` from Release 3). Standalone records deliberately leave the primary event date/location blank when the document does not establish which mentioned date or place is the incident value. PDF-derived evidence is exposed separately in `pdf_date_evidence` and `pdf_location_evidence`, with spaCy GPE/LOC/FAC extraction supplementing the domain-location hints.

Candidate `pursue_text` is a review excerpt from the best-matching semantic chunk, not the entire document. It is capped at 900 characters to keep a 500-row CSV usable, but is now cut only at a word boundary and marked with an ellipsis. Matching reads the original extracted text from `pursue_extracted_text_path`; the excerpt limit does not determine the similarity score. The unified table keeps a 20,000-character analysis copy for routine tabular exploration, while semantic matching reloads the source text and chunks it separately.

Semantic retrieval keeps up to 120 Kaggle reports per PURSUE row. Every one of those retrieved pairs now receives the complete transformer, TF-IDF, lexical, date, location, and entity scoring calculation. There is no pre-scoring reduction to 40 and no minimum final-score cutoff. Only after the retrieved pairs have been fully scored are they sorted globally and truncated to the 500-row review export.

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

NER uses lightweight spaCy `en_core_web_sm`, plus structured fields and UFO-domain lexicons. On first use the pipeline downloads the model automatically if it is missing. Set `UFO_AUTO_DOWNLOAD_SPACY=0` to disable that network step and use the domain/structured fallback instead.

## Edwin Drood

The script downloads Project Gutenberg eBook 564 from:

```text
https://www.gutenberg.org/files/564/564-0.txt
```

For Dickens comparison, the default earlier work is Great Expectations, Project Gutenberg eBook 1400. More works can be added through the same helper.

## Related Docs

- [Project plan](plan.md)
- [Ambiguities](ambiguities.md)
