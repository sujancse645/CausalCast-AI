export type RagDocumentType = "markdown" | "text" | "json" | "csv";

export interface RagRetrievalOptions {
  dataset?: string;
  document_type?: RagDocumentType;
  top_k?: number;
  minimum_similarity?: number;
}

export interface RagChatRequest extends RagRetrievalOptions {
  question: string;
  stream?: boolean;
}

export interface RagChatResponse {
  answer: string;
  sources: string[];
}

export interface RagSearchRequest extends RagRetrievalOptions {
  query: string;
}

export interface RagSourceMetadata {
  source: string;
  section_title: string;
  dataset_name: string | null;
  document_type: RagDocumentType;
  timestamp: string;
}

export interface RagSearchResult {
  content: string;
  similarity: number;
  metadata: RagSourceMetadata;
}

export interface RagSearchResponse {
  query: string;
  results: RagSearchResult[];
}

export interface RagDocument {
  source: string;
  dataset_name: string | null;
  document_type: RagDocumentType;
  timestamp: string;
  checksum: string;
  chunk_count: number;
}

export interface RagDocumentListResponse {
  items: RagDocument[];
  document_count: number;
  chunk_count: number;
}

export type RagStreamEvent =
  | { type: "token"; content: string }
  | { type: "sources"; sources: string[] }
  | { type: "done" };
