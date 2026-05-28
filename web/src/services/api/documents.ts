import { apiClient } from "../api-client";
import type {
  ApiResponse,
  PaginatedData,
  DocumentResponse,
  DocumentUploadResponse,
} from "@/types/api";

export async function listDocumentsByKb(kbId: string, page = 1, pageSize = 20) {
  const { data } = await apiClient.get<ApiResponse<PaginatedData<DocumentResponse>>>(
    `/api/v1/knowledge-bases/${kbId}/documents`,
    { params: { page, page_size: pageSize } },
  );
  return data;
}

export async function uploadDocument(kbId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<ApiResponse<DocumentUploadResponse>>(
    `/api/v1/knowledge-bases/${kbId}/documents`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

export async function getDocument(id: string) {
  const { data } = await apiClient.get<ApiResponse<DocumentResponse>>(
    `/api/v1/documents/${id}`,
  );
  return data;
}
