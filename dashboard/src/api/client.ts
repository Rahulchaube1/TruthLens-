import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE ?? "/api";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("tl_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Types
export interface ScanRecord {
  id: string;
  user_id: string;
  scan_type: "video" | "audio" | "image";
  is_fake: boolean;
  confidence: number;
  risk_level: string;
  timestamp: string;
  source_url?: string;
}

export interface VideoDetectRequest {
  url?: string;
  frames?: string[];
}

export interface VideoDetectResponse {
  is_deepfake: boolean;
  confidence: number;
  frame_scores: number[];
  detection_time_ms: number;
  risk_level: string;
}

export interface ImageDetectRequest {
  image_base64: string;
  check_metadata: boolean;
}

export interface ImageDetectResponse {
  is_ai_generated: boolean;
  confidence: number;
  gan_artifacts: boolean;
  metadata_inconsistencies: string[];
  generator_model_guess: string;
}

export const authApi = {
  register: (email: string, password: string, name: string) =>
    api.post("/auth/register", { email, password, name }),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  getApiKey: () => api.get("/auth/apikey"),
};

export const detectApi = {
  detectVideo: (body: VideoDetectRequest) =>
    api.post<VideoDetectResponse>("/detect/video", body),
  detectImage: (body: ImageDetectRequest) =>
    api.post<ImageDetectResponse>("/detect/image", body),
};

export const historyApi = {
  getHistory: (limit = 50) =>
    api.get<ScanRecord[]>(`/history?limit=${limit}`),
};
