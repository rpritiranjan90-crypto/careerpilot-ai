import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InterviewPage } from "../pages/InterviewPage";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    startInterview: vi.fn(),
    submitInterviewAnswer: vi.fn(),
  };
});

describe("InterviewPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders interview category selection on initial load", () => {
    render(<InterviewPage />);

    expect(screen.getByRole("heading", { name: /mock interview/i })).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
    expect(screen.getByText("HR")).toBeInTheDocument();
    expect(screen.getByText("General")).toBeInTheDocument();
  });

  it("starts interview when category is selected and displays question", async () => {
    vi.mocked(api.startInterview).mockResolvedValue({
      data: {
        interview_id: "itw-123",
        question: "Explain the differences between SQL and NoSQL databases.",
        category: "technical",
        tips: ["Mention ACID properties", "Discuss scalability models"],
      },
      status: 201,
    });

    render(<InterviewPage />);
    const user = userEvent.setup();

    await user.click(screen.getByText("Technical"));

    await waitFor(() => {
      expect(api.startInterview).toHaveBeenCalledWith("technical");
      expect(screen.getByText(/explain the differences between sql and nosql/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/type your answer here/i)
      ).toBeInTheDocument();
    });
  });

  it("submits answer and displays structured evaluation feedback", async () => {
    vi.mocked(api.startInterview).mockResolvedValue({
      data: {
        interview_id: "itw-456",
        question: "What is your approach to system debugging?",
        category: "technical",
        tips: [],
      },
      status: 201,
    });
    vi.mocked(api.submitInterviewAnswer).mockResolvedValue({
      data: {
        interview_id: "itw-456",
        score: 85,
        feedback: "Comprehensive answer explaining logs, reproduction, and root-cause analysis.",
        dimensions: [
          { name: "Technical Depth", score: 90, feedback: "Great depth" },
          { name: "Communication", score: 80, feedback: "Structured clearly" },
        ],
        improvements: ["Mention monitoring alerts in production"],
      },
      status: 200,
    });

    render(<InterviewPage />);
    const user = userEvent.setup();

    await user.click(screen.getByText("Technical"));

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/type your answer here/i)
      ).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/type your answer here/i);
    await user.type(
      textarea,
      "I start by inspecting logs and reproduction steps to isolate the issue before fixing."
    );
    await user.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() => {
      expect(screen.getByText("85")).toBeInTheDocument();
      expect(screen.getByText(/comprehensive answer explaining logs/i)).toBeInTheDocument();
      expect(screen.getByText("Technical Depth")).toBeInTheDocument();
      expect(screen.getByText(/mention monitoring alerts in production/i)).toBeInTheDocument();
    });
  });
});
