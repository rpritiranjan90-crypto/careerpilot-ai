/* CareerPilot AI - Type Definitions */

/* ---------- Resume Types ---------- */

export interface SkillAnalysis {
  name: string;
  confidence: number;
  category: "technical" | "soft" | "general";
}

export interface ResumeAnalysis {
  score: number;
  summary: string;
  skills: SkillAnalysis[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  experience_summary?: string;
  education_summary?: string;
  project_summary?: string;
}

/* ---------- Job Match Types ---------- */

export interface SkillMatch {
  skill: string;
  matched: boolean;
  priority: number;
}

export interface JobMatch {
  match_score: number;
  matched_skills: SkillMatch[];
  missing_skills: string[];
  recommendations: string[];
  summary: string;
}

/* ---------- Interview Types ---------- */

export interface EvaluationDimension {
  name: string;
  score: number;
  feedback: string;
}

export interface InterviewQuestion {
  interview_id: string;
  question: string;
  category: string;
  evaluation?: {
    score: number;
    feedback: string;
    dimensions: EvaluationDimension[];
  };
  tips: string[];
}

export type InterviewType = "general" | "hr" | "technical" | "role_specific";

/* ---------- Career Readiness Types ---------- */

export interface CareerReadiness {
  overall_score: number;
  breakdown: {
    resume: { score: number; weight: number };
    job_match: { score: number; weight: number };
    interview: { score: number; weight: number };
    skills: { score: number; weight: number };
  };
  strongest_area: { name: string; label: string; score: number };
  needs_improvement: { name: string; label: string; score: number };
  recommended_next_step: string;
}

/* ---------- API Response Types ---------- */

export interface ApiError {
  detail: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  resume_id?: string;
}

/* ---------- UI State Types ---------- */

export interface LoadingState {
  isLoading: boolean;
  message: string;
}

export interface ErrorState {
  hasError: boolean;
  message: string;
}

export interface EmptyState {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}