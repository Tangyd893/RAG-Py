import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = process.env.NEXT_PUBLIC_DEV_AUTH_TOKEN;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.error;
    const message = detail?.message ?? error.message ?? "请求失败";
    return Promise.reject(new Error(message));
  },
);
