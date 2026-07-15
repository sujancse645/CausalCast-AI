export type DatasetStatus =
  "uploading" | "validating" | "ready" | "failed" | "archived";

export interface DatasetWarning {
  code: string;
  message: string;
}
export interface DatasetSummary {
  id: string;
  original_filename: string;
  file_extension: string;
  mime_type: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  status: DatasetStatus;
  created_at: string;
  preview_available: boolean;
}
export interface DatasetDetail extends DatasetSummary {
  checksum_sha256: string;
  column_names: string[];
  delimiter: string | null;
  encoding: string | null;
  updated_at: string;
  deleted_at: string | null;
  ingestion_version: number;
  source_type: string;
  warnings: DatasetWarning[];
}
export interface DatasetUploadResponse extends DatasetDetail {
  preview_rows: Array<Record<string, string | null>>;
}
export interface DatasetPreview {
  dataset_id: string;
  columns: string[];
  rows: Array<Record<string, string | null>>;
  returned_rows: number;
  max_rows: number;
}
export interface PaginationMetadata {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}
export interface DatasetListResponse {
  items: DatasetSummary[];
  pagination: PaginationMetadata;
}
export interface DatasetArchiveResponse {
  id: string;
  status: "archived";
  deleted_at: string;
}
export interface DatasetStats {
  active_datasets: number;
  latest_filename: string | null;
  latest_upload_at: string | null;
  ingestion_status: "operational";
}
export interface DatasetApiErrorBody {
  detail: string;
  existing_dataset_id?: string;
}
