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

export interface InterviewRequest {
  answer?: string;
}

export interface InterviewProgress {
  current: number;
  total: number;
}

export interface InterviewResponse {
  question: string | null;
  done: boolean;
  progress: InterviewProgress;
}

export interface StepResult {
  id: string;
  title?: string;
  verdict: 'pass' | 'fail' | 'unclear';
  confidence: number;
  evidence_frames: number[];
  note: string;
  critical?: boolean;
  safety_critical?: boolean;
}

export interface AttemptResponse {
  id?: string;
  worker_id?: string;
  skill_id?: string;
  status: string;
  challenge_code?: string;
  interview_score?: number | null;
  video_score: number | null;
  decision: string | null;
  steps: StepResult[];
  fraud_flags: Array<{ code: string; severity?: string; detail: string }>;
  agent_log: string[];
}
