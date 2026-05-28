import { apiClient } from "../api-client";
import type {
  ApiResponse,
  PaginatedData,
  KBResponse,
  KBDetailResponse,
  CreateKBRequest,
} from "@/types/api";

export async function listKnowledgeBases(page = 1, pageSize = 20) {
  const { data } = await apiClient.get<ApiResponse<PaginatedData<KBResponse>>>(
    "/api/v1/knowledge-bases",
    { params: { page, page_size: pageSize } },
  );
  return data;
}

export async function getKnowledgeBase(id: string) {
  const { data } = await apiClient.get<ApiResponse<KBDetailResponse>>(
    `/api/v1/knowledge-bases/${id}`,
  );
  return data;
}

export async function createKnowledgeBase(req: CreateKBRequest) {
  const { data } = await apiClient.post<ApiResponse<KBResponse>>(
    "/api/v1/knowledge-bases",
    req,
  );
  return data;
}
