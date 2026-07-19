# Retrieval-Augmented Generation

## Architecture

The RAG subsystem is independent from forecasting and indexes only project knowledge. `DocumentRegistry` allowlists `README.md`, `docs/`, and `reports/` Markdown, text, JSON, and CSV files. It excludes environments, dependencies, models, raw/processed/features datasets, vector storage, caches, oversized files, and its own RAG validation reports.

`ProjectDocumentLoader` parses Markdown sections and bounded JSON/CSV records. `SemanticChunker` creates semantic-boundary chunks of at most 800 characters with 150-character overlap. Every chunk retains source, section, dataset (when represented by the report path), document type, timestamp, and checksum.

`SentenceTransformerEmbedder` loads `sentence-transformers/all-MiniLM-L6-v2`, preferring local-only files before an optional normal model load. It produces normalized 384-dimensional vectors. FAISS `IndexFlatIP` therefore implements cosine similarity.

`FaissVectorStore` persists `index.faiss`, `metadata.pkl`, `embeddings_cache.pkl`, and a checksum manifest under `backend/storage/vector_db/`. Rebuilds reuse unchanged chunk embeddings and atomically replace verified artifacts. Pickle metadata is loaded only after application-created file checksums pass.

`Retriever` returns five results by default, applies a configurable minimum similarity, and supports exact dataset/document-type filters.

## Grounded answers

The active provider is `DeterministicGroundedGenerator`. It extracts relevant retrieved sentences and reads retrieved, allowlisted model-comparison/report structures for reproducible metric and dataset summaries. If evidence is insufficient, it returns exactly:

```text
I could not find that information in the project.
```

Generated validation reports are excluded from RAG retrieval to prevent self-referential answer feedback. A local FLAN-T5 model is not integrated into the active runtime; no FLAN-T5 result is claimed.

## API

- `POST /api/v1/chat`: JSON answer with source citations or an SSE token/source stream.
- `POST /api/v1/search`: raw Top-K results and metadata.
- `GET /api/v1/documents`: indexed document/chunk inventory.
- `POST /api/v1/reindex`: admin/data-scientist incremental or forced rebuild.

All routes require authentication. Reindex additionally enforces a server-side role check.

Example request:

```json
{
  "question": "Which model performs best for Tourism Quarterly?",
  "stream": false
}
```

The source metadata identifies Tourism as yearly even when a question calls it quarterly.

## Index and validate

```powershell
Set-Location backend
..\.venv\Scripts\python.exe scripts\index_rag.py
Set-Location ..
.\.venv\Scripts\python.exe scripts\validate_integration.py
```

The executed integration report records the discovered/indexed document counts, chunk count, embedding dimension, real retrieval sources, and exact unavailable-answer test. Counts change when eligible project documents change; never hardcode them as runtime guarantees.
