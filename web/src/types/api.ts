/** API 通用响应模型 */

export interface ApiResponse<T> {
  data: T | null;
  error: ErrorDetail | null;
  request_id: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** 知识库 */
export interface KBResponse {
  id: string;
  name: string;
  description: string | null;
  embedding_model: string;
  vector_collection: string;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface KBDetailResponse extends KBResponse {
  document_count: number;
  indexed_count: number;
  failed_count: number;
}

export interface CreateKBRequest {
  name: string;
  description?: string | null;
  chunk_size?: number;
  chunk_overlap?: number;
  retrieval_top_k?: number;
}

/** 文档 */
export interface DocumentResponse {
  id: string;
  knowledge_base_id: string;
  filename: string;
  content_type: string;
  file_size: number;
  checksum: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  status: string;
  duplicate: boolean;
}

/** RAG 查询 */
export interface QueryRequest {
  knowledge_base_id: string;
  question: string;
  top_k?: number;
  temperature?: number;
  rerank_enabled?: boolean;
  hybrid_search?: boolean;
}

export interface SourceResponse {
  source_id: string;
  document_id: string;
  chunk_id: string;
  filename: string;
  page_number?: number | null;
  score: number;
  content: string;
}

export interface UsageInfo {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface QueryResponse {
  query_id: string;
  answer: string;
  sources: SourceResponse[];
  usage: UsageInfo;
  latency_ms: number;
  cache_hit: boolean;
}
