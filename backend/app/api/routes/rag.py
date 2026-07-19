from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.core.authz import Role, UserContext
from app.core.config import Settings, get_settings
from app.rag.dependencies import get_rag_service
from app.rag.rag_service import RAGService
from app.rag.vector_store import VectorStoreIntegrityError
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    DocumentListResponse,
    DocumentResponse,
    ReindexRequest,
    ReindexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
    SourceMetadataResponse,
)

router = APIRouter(tags=["rag"])
Service = Annotated[RAGService, Depends(get_rag_service)]
Config = Annotated[Settings, Depends(get_settings)]
User = Annotated[UserContext, Depends(get_current_user)]


def _minimum(request: ChatRequest | SearchRequest, settings: Settings) -> float:
    return request.minimum_similarity if request.minimum_similarity is not None else settings.rag_minimum_similarity


def _safe_search(service: RAGService, request: SearchRequest, settings: Settings) -> SearchResponse:
    try:
        results = service.search(
            request.query,
            top_k=request.top_k,
            minimum_similarity=_minimum(request, settings),
            dataset=request.dataset,
            document_type=request.document_type,
        )
    except FileNotFoundError as exc:
        raise HTTPException(503, detail="Project document index is not available; run reindex first") from exc
    except VectorStoreIntegrityError as exc:
        raise HTTPException(503, detail="Project document index failed integrity validation") from exc
    return SearchResponse(
        query=request.query,
        results=[
            SearchResultResponse(
                content=item.chunk.content,
                similarity=round(item.similarity, 6),
                metadata=SourceMetadataResponse(
                    source=item.chunk.metadata.source,
                    section_title=item.chunk.metadata.section_title,
                    dataset_name=item.chunk.metadata.dataset_name,
                    document_type=item.chunk.metadata.document_type,
                    timestamp=item.chunk.metadata.timestamp,
                ),
            )
            for item in results
        ],
    )


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, service: Service, settings: Config) -> SearchResponse:
    return _safe_search(service, request, settings)


@router.post("/chat", response_model=None)
def chat(request: ChatRequest, service: Service, settings: Config) -> ChatResponse | StreamingResponse:
    try:
        result = service.chat(
            request.question,
            top_k=request.top_k,
            minimum_similarity=_minimum(request, settings),
            dataset=request.dataset,
            document_type=request.document_type,
        )
    except FileNotFoundError as exc:
        raise HTTPException(503, detail="Project document index is not available; run reindex first") from exc
    except VectorStoreIntegrityError as exc:
        raise HTTPException(503, detail="Project document index failed integrity validation") from exc
    if not request.stream:
        return ChatResponse(answer=result.answer, sources=result.sources)
    return StreamingResponse(_events(result.answer, result.sources), media_type="text/event-stream")


def _events(answer: str, sources: list[str]) -> Iterator[str]:
    for token in re.findall(r"\S+\s*", answer):
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
    yield 'data: {"type": "done"}\n\n'


@router.get("/documents", response_model=DocumentListResponse)
def documents(service: Service) -> DocumentListResponse:
    try:
        items = service.documents()
    except (FileNotFoundError, VectorStoreIntegrityError) as exc:
        raise HTTPException(503, detail="Project document index is not available") from exc
    return DocumentListResponse(
        items=[DocumentResponse(**item.to_dict()) for item in items],
        document_count=len(items),
        chunk_count=sum(item.chunk_count for item in items),
    )


@router.post("/reindex", response_model=ReindexResponse)
def reindex(request: ReindexRequest, service: Service, user: User) -> ReindexResponse:
    if Role.ADMIN not in user.roles and Role.DATA_SCIENTIST not in user.roles:
        raise HTTPException(403, detail="Reindex permission is required")
    result = service.reindex(force=request.force)
    return ReindexResponse(
        document_count=result.document_count,
        chunk_count=result.chunk_count,
        embedding_dimension=result.embedding_dimension,
        embedded_chunks=result.embedded_chunks,
        reused_chunks=result.reused_chunks,
    )
