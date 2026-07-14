# GPU Transformer Run

Root doc: [README](../README.md)

The UFO matcher can use transformer embeddings as the primary text signal. It falls back to TF-IDF and lexical similarity if `sentence-transformers` is unavailable and no matching embedding cache exists.

## Windows GPU Setup

Use a Python environment with CUDA-enabled PyTorch. Example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python -m nlp_ass5.ufo
```

The default embedding model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Override it if desired:

```powershell
$env:UFO_EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
$env:UFO_EMBEDDING_BATCH_SIZE="256"
$env:UFO_EMBEDDING_DEVICE="cuda"
python -m nlp_ass5.ufo
```

Disable transformer matching and use TF-IDF/lexical fallback:

```powershell
$env:UFO_USE_TRANSFORMERS="0"
python -m nlp_ass5.ufo
```

## Outputs

Embedding caches are written to:

```text
data/processed/embedding_cache/
```

Candidate outputs include:

- `transformer_similarity`: cosine similarity between Kaggle text and the best official document chunk.
- `tfidf_text_similarity`: explicit TF-IDF cosine similarity over the candidate snippets.
- `lexical_text_similarity`: the older token/string overlap score.
- `text_similarity`: equals transformer similarity when available, otherwise lexical similarity.

## Matching Design

The pipeline embeds:

- all Kaggle sighting descriptions;
- chunked PURSUE extracted document text;
- metadata text for PURSUE rows without extracted documents.

For each official record, transformer runs retrieve broad semantic top-k Kaggle candidates first because PURSUE date/location metadata is often weak. Date, location, TF-IDF, lexical, and entity signals are scored after retrieval. If transformer embeddings are unavailable, the fallback path still uses year/entity blocking to avoid naive all-pairs comparison.

## Related Docs

- [Data notes](data_notes.md)
- [Manual validation](manual_validation.md)
