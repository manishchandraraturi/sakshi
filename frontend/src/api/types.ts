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

export interface WitnessInvite {
  token: string;
  url: string;
}

export interface WitnessPageStep {
  id: string;
  title: string;
}

export interface WitnessPageData {
  worker_first_name: string;
  skill: string;
  skill_name?: string;
  clip_url?: string | null;
  steps: WitnessPageStep[];
}

export interface VouchCreate {
  witness_name?: string;
  name?: string;
  role: string;
  institute_code?: string;
  seen_in_person: boolean;
  known_years_bucket?: string;
  known_years?: string;
  would_hire: boolean;
  verdict: string;
  device_fp?: string;
}

export interface VouchResponse {
  vouch_id: string;
  weight: number;
  attempt_id: string;
  status: string;
}

export interface CredentialResponse {
  credential_id: string;
  tier: number;
  trust_score: number;
  payload: {
    cred_id: string;
    worker_name: string;
    area: string;
    trade: string;
    skill: string;
    tier: number;
    trust_score: number;
    issued_at: string;
    evidence_sha256: string;
    witness_count: number;
    [key: string]: any;
  };
  signature: string;
  issued_at?: string;
}

export interface DirectoryItem {
  credential_id: string;
  name: string;
  trade: string;
  skill: string;
  tier: number;
  trust_score: number;
  area: string;
  issued_at?: string;
}


