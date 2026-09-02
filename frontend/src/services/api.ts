/**
 * CareerPilot AI - API Service
 *
 * Handles all API communication with the backend.
 * Uses environment variables for configuration and Bearer JWT for auth.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : "http://localhost:8000";

const TOKEN_STORAGE_KEY = "careerpilot.access_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAccessToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status?: number;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  // Only set Content-Type when there's a non-FormData body
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let detail = `Request failed: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData?.error?.message) {
          detail = errorData.error.message;
        } else if (typeof errorData?.detail === "string") {
          detail = errorData.detail;
        }
      } catch {
        // response body wasn't JSON
      }
      if (response.status === 401) {
        setAccessToken(null);
        window.dispatchEvent(new Event("auth:logout"));
      }
      return { error: detail, status: response.status };
    }

    if (response.status === 204) {
      return { data: undefined as unknown as T, status: 204 };
    }
    const data = (await response.json()) as T;
    return { data, status: response.status };
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      return { error: "Unable to connect to the server." };
    }
    return {
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

// ---------------------------------------------------------------------------
// Resume
// ---------------------------------------------------------------------------

export interface ResumeAnalysis {
  score: number;
  summary: string;
  skills: Array<{ name: string; confidence: number; category: string }>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  experience_summary?: string;
  education_summary?: string;
  project_summary?: string;
}

export interface ResumeSummary {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string | null;
  created_at: string;
}

export async function analyzeResume(
  resumeText: string,
  jobDescription?: string
): Promise<ApiResponse<ResumeAnalysis>> {
  return apiRequest<ResumeAnalysis>("/api/resumes/analyze", {
    method: "POST",
    body: JSON.stringify({
      resume_text: resumeText,
      job_description: jobDescription,
    }),
  });
}

export async function uploadResumeFile(
  file: File
): Promise<ApiResponse<{ resume_id: string; filename: string; size: number }>> {
  const form = new FormData();
  form.append("file", file);
  return apiRequest<{ resume_id: string; filename: string; size: number }>(
    "/api/resumes/upload",
    { method: "POST", body: form }
  );
}

export async function analyzeUploadedResume(
  resumeId: string
): Promise<ApiResponse<ResumeAnalysis>> {
  return apiRequest<ResumeAnalysis>(`/api/resumes/${resumeId}/analyze`, {
    method: "POST",
  });
}

export async function listResumes(): Promise<ApiResponse<ResumeSummary[]>> {
  return apiRequest<ResumeSummary[]>("/api/resumes");
}

// ---------------------------------------------------------------------------
// Job match
// ---------------------------------------------------------------------------

export interface JobMatch {
  match_score: number;
  matched_skills: Array<{ skill: string; matched: boolean; priority: number }>;
  missing_skills: string[];
  recommendations: string[];
  summary: string;
}

export async function matchJob(
  resumeSkills: string[],
  jobRequirements: string
): Promise<ApiResponse<JobMatch>> {
  return apiRequest<JobMatch>("/api/job-matches", {
    method: "POST",
    body: JSON.stringify({
      resume_skills: resumeSkills,
      job_requirements: jobRequirements,
    }),
  });
}

// ---------------------------------------------------------------------------
// Interview
// ---------------------------------------------------------------------------

export interface InterviewQuestion {
  interview_id: string;
  question: string;
  category: string;
  tips: string[];
}

export interface InterviewEvaluation {
  interview_id: string;
  score: number;
  feedback: string;
  dimensions: Array<{ name: string; score: number; feedback: string }>;
  improvements: string[];
}

export async function startInterview(
  interviewType: string,
  question?: string
): Promise<ApiResponse<InterviewQuestion>> {
  return apiRequest<InterviewQuestion>("/api/interviews", {
    method: "POST",
    body: JSON.stringify({ interview_type: interviewType, question }),
  });
}

export async function submitInterviewAnswer(
  interviewId: string,
  answer: string,
  context: string
): Promise<ApiResponse<InterviewEvaluation>> {
  return apiRequest<InterviewEvaluation>(
    `/api/interviews/${interviewId}/answers`,
    {
      method: "POST",
      body: JSON.stringify({ answer, context }),
    }
  );
}

// ---------------------------------------------------------------------------
// User & Dashboard
// ---------------------------------------------------------------------------

export interface CareerReadinessBreakdown {
  score: number;
  weight: number;
}

export interface CareerReadinessData {
  overall_score: number;
  breakdown: {
    resume: CareerReadinessBreakdown;
    job_match: CareerReadinessBreakdown;
    interview: CareerReadinessBreakdown;
    skills: CareerReadinessBreakdown;
  };
  strongest_area: {
    name: string;
    label: string;
    score: number;
  };
  needs_improvement: {
    name: string;
    label: string;
    score: number;
  };
  recommended_next_step: string;
}

export interface DashboardResponse {
  has_data: boolean;
  career_readiness: CareerReadinessData;
  resume_count: number;
  job_match_count: number;
  interview_count: number;
}

export async function getUserDashboard(): Promise<ApiResponse<DashboardResponse>> {
  return apiRequest<DashboardResponse>("/api/users/me/dashboard");
}

export async function deleteAccount(): Promise<ApiResponse<{ message: string; deleted_user_id: string }>> {
  return apiRequest<{ message: string; deleted_user_id: string }>("/api/users/me", {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Career Improvement Engine
// ---------------------------------------------------------------------------

export interface NextBestAction {
  title: string;
  category: "resume" | "skills" | "interview";
  why: string;
  what_to_do: string;
  expected_outcome: string;
  cta_label: string;
  cta_link: string;
}

export interface ResumeEnhancementItem {
  id: string;
  category: string;
  issue: string;
  severity: "high" | "medium" | "low";
  explanation: string;
  recommended_fix: string;
  before_example: string;
  after_example: string;
  is_placeholder_example: boolean;
}

export interface SkillGapItem {
  skill_name: string;
  status: "missing" | "improve" | "strong";
  priority: "High" | "Medium" | "Low";
  reason: string;
  prerequisites: string[];
  learning_path: string;
  practical_exercise: string;
  project_idea: string;
}

export interface ActionItem {
  task_id: string;
  task: string;
  category: "resume" | "skills" | "interview";
  estimated_minutes: number;
  is_completed: boolean;
  completed_at: string | null;
}

export interface ActionPlanTimeline {
  today: ActionItem[];
  this_week: ActionItem[];
  this_month: ActionItem[];
}

export interface ScoreProgressItem {
  current: number;
  previous: number | null;
  delta: number | null;
}

export interface ProgressTracking {
  has_history: boolean;
  overall_readiness: ScoreProgressItem;
  resume_score: ScoreProgressItem;
  job_match_score: ScoreProgressItem;
  interview_score: ScoreProgressItem;
  skills_score: ScoreProgressItem;
}

export interface CareerImprovementPlan {
  has_data: boolean;
  data_completeness: "complete" | "resume_only" | "no_data" | "partial";
  overall_score: number;
  target_potential_score: number;
  summary: string;
  next_best_action: NextBestAction | null;
  resume_enhancements: ResumeEnhancementItem[];
  skill_gaps: SkillGapItem[];
  action_plan: ActionPlanTimeline;
  progress_tracking: ProgressTracking;
}

export async function getImprovementPlan(): Promise<ApiResponse<CareerImprovementPlan>> {
  return apiRequest<CareerImprovementPlan>("/api/improvement-plan");
}

export async function refreshImprovementPlan(): Promise<ApiResponse<CareerImprovementPlan>> {
  return apiRequest<CareerImprovementPlan>("/api/improvement-plan/refresh", {
    method: "POST",
  });
}

export async function toggleActionItem(
  taskId: string
): Promise<ApiResponse<{ task_id: string; is_completed: boolean; completed_at: string | null }>> {
  return apiRequest<{ task_id: string; is_completed: boolean; completed_at: string | null }>(
    `/api/improvement-plan/actions/${taskId}/toggle`,
    { method: "POST" }
  );
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
