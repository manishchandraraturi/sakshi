export interface ApiError {
  code: string;
  message: string;
  hint?: string;
}

export interface ApiResponse<T> {
  ok: boolean;
  data: T | null;
  error: ApiError | null;
}

export interface HealthData {
  status: string;
  demo_mode: boolean;
}
