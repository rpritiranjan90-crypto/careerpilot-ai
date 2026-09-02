import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ResumePage } from "../pages/ResumePage";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    analyzeResume: vi.fn(),
    uploadResumeFile: vi.fn(),
    analyzeUploadedResume: vi.fn(),
  };
});

describe("ResumePage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders upload and paste forms", () => {
    render(<ResumePage />);

    expect(screen.getByRole("heading", { name: /resume analysis/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/paste your resume content here/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze resume/i })).toBeInTheDocument();
  });

  it("disables analyze button when resume text is under 50 characters", async () => {
    render(<ResumePage />);
    const user = userEvent.setup();

    const textarea = screen.getByPlaceholderText(/paste your resume content here/i);
    await user.type(textarea, "Short text");
    const button = screen.getByRole("button", { name: /analyze resume/i });

    expect(button).toBeDisabled();
    expect(api.analyzeResume).not.toHaveBeenCalled();
  });

  it("analyzes pasted text and displays score and results", async () => {
    vi.mocked(api.analyzeResume).mockResolvedValue({
      data: {
        score: 88,
        summary: "Strong full stack profile with relevant engineering experience.",
        skills: [
          { name: "TypeScript", confidence: 0.95, category: "Languages" },
          { name: "React", confidence: 0.9, category: "Frontend" },
        ],
        strengths: ["Solid framework expertise", "Clear project achievements"],
        weaknesses: ["Add metrics to past roles"],
        recommendations: ["Include cloud certification"],
      },
      status: 200,
    });

    render(<ResumePage />);
    const user = userEvent.setup();

    const textarea = screen.getByPlaceholderText(/paste your resume content here/i);
    const validResume =
      "Senior Full Stack Software Engineer with 6 years experience building React and TypeScript applications with Python backends.";
    await user.type(textarea, validResume);
    await user.click(screen.getByRole("button", { name: /analyze resume/i }));

    await waitFor(() => {
      expect(screen.getByText("88")).toBeInTheDocument();
      expect(screen.getByText(/strong full stack profile/i)).toBeInTheDocument();
      expect(screen.getByText("TypeScript")).toBeInTheDocument();
      expect(screen.getByText("React")).toBeInTheDocument();
      expect(screen.getByText(/solid framework expertise/i)).toBeInTheDocument();
    });
  });

  it("handles file upload and triggers analysis", async () => {
    vi.mocked(api.uploadResumeFile).mockResolvedValue({
      data: { resume_id: "res-uuid-123", filename: "my_resume.pdf", size: 1024 },
      status: 201,
    });
    vi.mocked(api.analyzeUploadedResume).mockResolvedValue({
      data: {
        score: 92,
        summary: "Excellent resume file parsed successfully.",
        skills: [{ name: "Python", confidence: 0.98, category: "Languages" }],
        strengths: ["Great experience"],
        weaknesses: [],
        recommendations: ["Ready for applications"],
      },
      status: 200,
    });

    const { container } = render(<ResumePage />);

    const file = new File(["dummy pdf content"], "my_resume.pdf", { type: "application/pdf" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).not.toBeNull();

    const user = userEvent.setup();
    await user.upload(input, file);

    await waitFor(() => {
      expect(api.uploadResumeFile).toHaveBeenCalledWith(file);
      expect(api.analyzeUploadedResume).toHaveBeenCalledWith("res-uuid-123");
      expect(screen.getByText("92")).toBeInTheDocument();
      expect(screen.getByText(/excellent resume file parsed/i)).toBeInTheDocument();
    });
  });
});
