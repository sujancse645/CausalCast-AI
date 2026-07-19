from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RetrievalRequest(BaseModel):
    dataset: str | None = Field(default=None, max_length=200)
    document_type: Literal["markdown", "text", "json", "csv"] | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    minimum_similarity: float | None = Field(default=None, ge=-1, le=1)


class ChatRequest(RetrievalRequest):
    question: str = Field(min_length=2, max_length=2000)
    stream: bool = False

    @model_validator(mode="after")
    def question_is_not_blank(self) -> "ChatRequest":
        if not self.question.strip():
            raise ValueError("Question cannot be blank")
        return self


class SearchRequest(RetrievalRequest):
    query: str = Field(min_length=2, max_length=2000)


class SourceMetadataResponse(BaseModel):
    source: str
    section_title: str
    dataset_name: str | None
    document_type: str
    timestamp: str


class SearchResultResponse(BaseModel):
    content: str
    similarity: float
    metadata: SourceMetadataResponse


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultResponse]


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class DocumentResponse(BaseModel):
    source: str
    dataset_name: str | None
    document_type: str
    timestamp: str
    checksum: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    document_count: int
    chunk_count: int


class ReindexRequest(BaseModel):
    force: bool = False


class ReindexResponse(BaseModel):
    document_count: int
    chunk_count: int
    embedding_dimension: int
    embedded_chunks: int
    reused_chunks: int
