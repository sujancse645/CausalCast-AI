from functools import lru_cache

from app.core.config import get_settings
from app.rag.rag_service import RAGService


@lru_cache
def get_rag_service() -> RAGService:
    settings = get_settings()
    return RAGService(
        settings.rag_project_root,
        settings.rag_storage_root,
        model_name=settings.rag_embedding_model,
        chunk_size=settings.rag_chunk_size,
        overlap=settings.rag_chunk_overlap,
        max_file_bytes=settings.rag_max_file_size_mb * 1024 * 1024,
        max_csv_rows=settings.rag_max_csv_rows,
        embedding_batch_size=settings.rag_embedding_batch_size,
    )
