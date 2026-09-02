import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { DashboardPage } from "../pages/DashboardPage";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    getUserDashboard: vi.fn(),
  };
});

describe("DashboardPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    vi.mocked(api.getUserDashboard).mockReturnValue(new Promise(() => {}));

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/loading career readiness data/i)).toBeInTheDocument();
  });

  it("renders empty state guidance cards when user has no data", async () => {
    vi.mocked(api.getUserDashboard).mockResolvedValue({
      data: {
        has_data: false,
        career_readiness: {
          overall_score: 0,
          breakdown: {
            resume: { score: 0, weight: 0.3 },
            job_match: { score: 0, weight: 0.25 },
            interview: { score: 0, weight: 0.25 },
            skills: { score: 0, weight: 0.2 },
          },
          strongest_area: { name: "resume", label: "Resume", score: 0 },
          needs_improvement: { name: "interview", label: "Interview", score: 0 },
          recommended_next_step: "Practice more interview questions.",
        },
        resume_count: 0,
        job_match_count: 0,
        interview_count: 0,
      },
      status: 200,
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /career readiness dashboard/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("link", { name: /analyze resume/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /match job description/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /practice interview/i })).toBeInTheDocument();
  });

  it("renders populated career readiness score and breakdown when user has data", async () => {
    vi.mocked(api.getUserDashboard).mockResolvedValue({
      data: {
        has_data: true,
        career_readiness: {
          overall_score: 84,
          breakdown: {
            resume: { score: 85, weight: 0.3 },
            job_match: { score: 90, weight: 0.25 },
            interview: { score: 80, weight: 0.25 },
            skills: { score: 78, weight: 0.2 },
          },
          strongest_area: { name: "job_match", label: "Job Match", score: 90 },
          needs_improvement: { name: "skills", label: "Skills", score: 78 },
          recommended_next_step: "Identify and develop key skills required for target role.",
        },
        resume_count: 3,
        job_match_count: 5,
        interview_count: 2,
      },
      status: 200,
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("84")).toBeInTheDocument();
    });

    expect(screen.getByText(/career readiness score/i)).toBeInTheDocument();
    expect(screen.getByText(/identify and develop key skills/i)).toBeInTheDocument();
  });

  it("renders error state with retry button when API fails", async () => {
    vi.mocked(api.getUserDashboard).mockResolvedValueOnce({
      error: "Could not reach server.",
      status: 500,
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/unable to load dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/could not reach server/i)).toBeInTheDocument();
    });

    // Mock successful retry
    vi.mocked(api.getUserDashboard).mockResolvedValueOnce({
      data: {
        has_data: false,
        career_readiness: {
          overall_score: 0,
          breakdown: {
            resume: { score: 0, weight: 0.3 },
            job_match: { score: 0, weight: 0.25 },
            interview: { score: 0, weight: 0.25 },
            skills: { score: 0, weight: 0.2 },
          },
          strongest_area: { name: "resume", label: "Resume", score: 0 },
          needs_improvement: { name: "interview", label: "Interview", score: 0 },
          recommended_next_step: "Practice questions.",
        },
        resume_count: 0,
        job_match_count: 0,
        interview_count: 0,
      },
      status: 200,
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /try again/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /career readiness dashboard/i })).toBeInTheDocument();
    });
  });
});
