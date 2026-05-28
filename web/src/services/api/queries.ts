import { apiClient } from "../api-client";
import type { ApiResponse, QueryRequest, QueryResponse } from "@/types/api";

export async function submitQuery(req: QueryRequest) {
  const { data } = await apiClient.post<ApiResponse<QueryResponse>>(
    "/api/v1/queries",
    req,
  );
  return data;
}
