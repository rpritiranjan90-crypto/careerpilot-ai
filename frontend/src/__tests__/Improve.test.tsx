import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ImprovementPage } from "../pages/ImprovementPage";
import * as api from "../services/api";

const mockEmptyPlan: api.CareerImprovementPlan = {
  has_data: false,
  data_completeness: "no_data",
  overall_score: 0,
  target_potential_score: 85,
  summary: "Upload your resume and run a job match to generate your personalized career improvement roadmap.",
  next_best_action: {
    title: "Upload Your Resume to Establish Baseline",
    category: "resume",
    why: "We need your verified experience to identify strengths and uncover skill gaps.",
    what_to_do: "Upload your resume in PDF, DOCX, or TXT format on the Resume page.",
    expected_outcome: "Unlocks your complete personalized career readiness roadmap.",
    cta_label: "Upload Resume",
    cta_link: "/resume",
  },
  resume_enhancements: [],
  skill_gaps: [],
  action_plan: {
    today: [],
    this_week: [],
    this_month: [],
  },
  progress_tracking: {
    has_history: false,
    overall_readiness: { current: 0, previous: null, delta: null },
    resume_score: { current: 0, previous: null, delta: null },
    job_match_score: { current: 0, previous: null, delta: null },
    interview_score: { current: 0, previous: null, delta: null },
    skills_score: { current: 0, previous: null, delta: null },
  },
};

const mockPopulatedPlan: api.CareerImprovementPlan = {
  has_data: true,
  data_completeness: "complete",
  overall_score: 72,
  target_potential_score: 88,
  summary: "Your verified readiness score is 72/100. Following this personalized action plan can increase your score to 88/100.",
  next_best_action: {
    title: "Quantify Measurable Achievements on Your Resume",
    category: "resume",
    why: "Resumes with quantified business metrics receive 40% higher recruiter callback rates.",
    what_to_do: "Edit your experience section to replace generic task lists with Action-Context-Result bullets.",
    expected_outcome: "+10-15 points to Resume Quality and increased ATS interview conversion.",
    cta_label: "Improve Resume",
    cta_link: "/resume",
  },
  resume_enhancements: [
    {
      id: "resume_metrics_quantification",
      category: "Experience & Achievements",
      issue: "Bullet points lack quantified business impact and measurable outcomes",
      severity: "high",
      explanation: "Recruiters and ATS rank candidates significantly higher when responsibilities are framed with specific metrics.",
      recommended_fix: "Rewrite each role bullet point using Action-Context-Result.",
      before_example: "Responsible for maintaining backend APIs.",
      after_example: "Architected FastAPI microservice endpoints, reducing API response latency by [X]% across [N,000] daily active requests.",
      is_placeholder_example: true,
    },
  ],
  skill_gaps: [
    {
      skill_name: "Docker & Containerization",
      status: "missing",
      priority: "High",
      reason: "Required in target job qualifications.",
      prerequisites: ["Linux CLI", "Basic Networking"],
      learning_path: "1. Dockerfiles → 2. Multi-stage builds → 3. Compose clusters.",
      practical_exercise: "Containerize a FastAPI app with PostgreSQL.",
      project_idea: "Multi-container template with automated CI builds.",
    },
  ],
  action_plan: {
    today: [
      {
        task_id: "action_rewrite_summary",
        task: "Rewrite professional summary with targeted keywords",
        category: "resume",
        estimated_minutes: 20,
        is_completed: false,
        completed_at: null,
      },
    ],
    this_week: [
      {
        task_id: "action_practice_interview_star",
        task: "Practice 3 Technical mock interview questions",
        category: "interview",
        estimated_minutes: 45,
        is_completed: false,
        completed_at: null,
      },
    ],
    this_month: [
      {
        task_id: "action_build_capstone",
        task: "Build containerized portfolio project",
        category: "skills",
        estimated_minutes: 180,
        is_completed: false,
        completed_at: null,
      },
    ],
  },
  progress_tracking: {
    has_history: true,
    overall_readiness: { current: 72, previous: 58, delta: 14 },
    resume_score: { current: 75, previous: 60, delta: 15 },
    job_match_score: { current: 70, previous: 55, delta: 15 },
    interview_score: { current: 68, previous: 52, delta: 16 },
    skills_score: { current: 80, previous: 65, delta: 15 },
  },
};

describe("ImprovementPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty onboarding state when user has no data", async () => {
    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      data: mockEmptyPlan,
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    expect(await screen.findByText("Career Improvement Plan")).toBeInTheDocument();
    expect(
      screen.getByText(/Your personalized AI career coaching plan will appear here/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Upload Resume/i })).toBeInTheDocument();
  });

  it("renders populated improvement plan with Next Best Action, resume rewrites, and skill gaps", async () => {
    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      data: mockPopulatedPlan,
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    // Next Best Action
    expect(
      await screen.findByText("Quantify Measurable Achievements on Your Resume")
    ).toBeInTheDocument();
    expect(screen.getByText(/Next Best Action/i)).toBeInTheDocument();

    // Resume Enhancements
    expect(screen.getByText("Experience & Achievements")).toBeInTheDocument();
    expect(screen.getByText(/"Responsible for maintaining backend APIs."/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Architected FastAPI microservice endpoints/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Placeholder Template")).toBeInTheDocument();

    // Skill Gaps
    expect(screen.getByText("Docker & Containerization")).toBeInTheDocument();
    expect(screen.getByText(/1. Dockerfiles → 2. Multi-stage builds/i)).toBeInTheDocument();

    // Action plan
    expect(screen.getByText("Rewrite professional summary with targeted keywords")).toBeInTheDocument();
  });

  it("toggles action item completion with DB persistence", async () => {
    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      data: mockPopulatedPlan,
    });
    vi.spyOn(api, "toggleActionItem").mockResolvedValueOnce({
      data: {
        task_id: "action_rewrite_summary",
        is_completed: true,
        completed_at: new Date().toISOString(),
      },
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    const checkboxes = await screen.findAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThan(0);
    const checkbox = checkboxes[0];
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    expect(api.toggleActionItem).toHaveBeenCalledWith("action_rewrite_summary");
  });

  it("renders verified historical progress deltas when history exists", async () => {
    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      data: mockPopulatedPlan,
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    expect(await screen.findByText(/Verified Historical Progress/i)).toBeInTheDocument();
    expect(screen.getByText("+14 pts")).toBeInTheDocument();
    expect(screen.getByText("Prev: 58")).toBeInTheDocument();
  });

  it("renders 'No previous assessment yet' when no historical snapshot exists", async () => {
    const planNoHistory: api.CareerImprovementPlan = {
      ...mockPopulatedPlan,
      progress_tracking: {
        has_history: false,
        overall_readiness: { current: 72, previous: null, delta: null },
        resume_score: { current: 75, previous: null, delta: null },
        job_match_score: { current: 70, previous: null, delta: null },
        interview_score: { current: 68, previous: null, delta: null },
        skills_score: { current: 80, previous: null, delta: null },
      },
    };

    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      data: planNoHistory,
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    expect(await screen.findByText(/Verified Historical Progress/i)).toBeInTheDocument();
    const noPrevElements = screen.getAllByText("No previous assessment yet");
    expect(noPrevElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("+14 pts")).not.toBeInTheDocument();
  });

  it("renders error state when API fails with retry button", async () => {
    vi.spyOn(api, "getImprovementPlan").mockResolvedValueOnce({
      error: "Network error fetching plan",
    });

    render(
      <BrowserRouter>
        <ImprovementPage />
      </BrowserRouter>
    );

    expect(await screen.findByText("Unable to Load Improvement Plan")).toBeInTheDocument();
    expect(screen.getByText("Network error fetching plan")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Try Again/i })).toBeInTheDocument();
  });
});
