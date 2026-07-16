export type QualityReportStatus =
  "pending" | "running" | "completed" | "failed" | "superseded";
export type QualityReadinessStatus =
  | "not_analyzed"
  | "blocked"
  | "needs_attention"
  | "conditionally_ready"
  | "quality_ready";
export type QualitySeverity = "blocker" | "error" | "warning" | "info";
export interface QualityDimensionScores {
  completeness: number;
  uniqueness: number;
  validity: number;
  consistency: number;
  temporal: number;
  integrity: number;
  leakage_safety: number;
}
export interface QualityFinding {
  id: string;
  rule_code: string;
  category: string;
  severity: QualitySeverity;
  title: string;
  description: string;
  affected_column: string | null;
  related_columns: string[];
  affected_row_count: number | null;
  affected_ratio: number | null;
  sample_row_indices: number[];
  evidence: Record<string, string | number | boolean | null>;
  threshold: Record<string, string | number | boolean | null>;
  recommendation: string;
  blocking: boolean;
  confidence: number;
}
export interface QualityReportDetail {
  id: string;
  dataset_id: string;
  dataset_filename: string;
  report_version: number;
  schema_version: number;
  quality_engine_version: string;
  status: QualityReportStatus;
  readiness_status: QualityReadinessStatus;
  overall_score: number;
  dimension_scores: QualityDimensionScores;
  total_findings: number;
  blocker_count: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  scanned_rows: number;
  total_rows: number;
  scan_coverage_ratio: number;
  analyzed_columns: number;
  created_at: string;
  completed_at: string | null;
  duration_ms: number;
  summary: {
    temporal?: {
      available: boolean;
      column?: string;
      frequency?: string;
      date_min?: string | null;
      date_max?: string | null;
      gap_count?: number;
      duplicate_dates?: number;
      out_of_order?: number;
      future_dates?: number;
    };
    scan_mode?: string;
  };
  recommendations: Array<{ message: string; rule_code: string }>;
  findings: QualityFinding[];
}
export interface QualityHistoryItem {
  id: string;
  report_version: number;
  schema_version: number;
  status: QualityReportStatus;
  readiness_status: QualityReadinessStatus;
  overall_score: number;
  blocker_count: number;
  created_at: string;
}
export interface QualityFindingListResponse {
  items: QualityFinding[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}
export interface QualityStats {
  datasets_not_analyzed: number;
  blocked_datasets: number;
  needs_attention: number;
  conditionally_ready: number;
  quality_ready: number;
  total_blockers: number;
  average_quality_score: number | null;
}
export interface QualityRuleDefinition {
  code: string;
  category: string;
  title: string;
  description: string;
}
