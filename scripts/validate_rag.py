import sys
from pathlib import Path

# Add backend to PYTHONPATH
sys.path.insert(0, str(Path("backend").resolve()))

from app.rag.document_registry import DocumentRegistry
from app.rag.loader import ProjectDocumentLoader


def run_validation():
    print("==================================================")
    print("3. RUN REINDEXING")
    print("==================================================")

    project_root = Path(".").resolve()
    registry = DocumentRegistry(project_root)

    # 1. Discover all candidate files
    candidates = []
    if (project_root / "README.md").is_file():
        candidates.append(project_root / "README.md")
    for d in ["docs", "reports"]:
        directory = project_root / d
        if directory.is_dir():
            candidates.extend(path for path in directory.rglob("*") if path.is_file())

    discovered = len(candidates)

    # 2. Load only registry-approved documents.
    loader = ProjectDocumentLoader(registry)
    documents = loader.load_all()
    successfully_parsed = len(set(doc.metadata.source for doc in documents))

    # 3. Total skipped
    total_skipped = discovered - successfully_parsed

    print(f"Number of discovered documents: {discovered}")
    print(f"Number of successfully parsed documents: {successfully_parsed}")
    print(f"Number of skipped documents: {total_skipped}")

    print("\n==================================================")
    print("4. RUNNING ACTUAL FAISS REINDEX")
    print("==================================================")
    from app.rag.rag_service import RAGService

    service = RAGService(project_root, project_root / "backend" / "storage" / "vector_db")
    result = service.reindex(force=True)

    print("\nReindex Results:")
    print(f"- Documents embedded: {result.document_count}")
    print(f"- Chunks generated: {result.chunk_count}")
    print(f"- Embedding dimension: {result.embedding_dimension}")
    print(f"- New embeddings computed: {result.embedded_chunks}")
    print(f"- Vectors reused: {result.reused_chunks}")


if __name__ == "__main__":
    run_validation()
