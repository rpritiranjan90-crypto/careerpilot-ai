import { useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ScoreCard } from "../components/ScoreCard";
import { Badge } from "../components/Badge";
import { LoadingState, ErrorState } from "../components/States";
import {
  startInterview,
  submitInterviewAnswer,
  type InterviewQuestion,
  type InterviewEvaluation,
} from "../services/api";

type InterviewType = "general" | "hr" | "technical" | "role_specific";

interface InterviewTypeConfig {
  value: InterviewType;
  label: string;
  description: string;
  difficulty: "Entry" | "Intermediate" | "Advanced";
  icon: string;
}

const INTERVIEW_TYPES: InterviewTypeConfig[] = [
  {
    value: "general",
    label: "General",
    description: "Common career goals, background, and strengths questions.",
    difficulty: "Entry",
    icon: "🎯",
  },
  {
    value: "hr",
    label: "HR",
    description: "Behavioral fit, teamwork, conflict resolution, and leadership.",
    difficulty: "Intermediate",
    icon: "🤝",
  },
  {
    value: "technical",
    label: "Technical",
    description: "Core computer science, system architecture, and problem solving.",
    difficulty: "Advanced",
    icon: "💻",
  },
  {
    value: "role_specific",
    label: "Role Specific",
    description: "Targeted situational scenarios tailored for your desired job track.",
    difficulty: "Advanced",
    icon: "🚀",
  },
];

/**
 * Mock Interview Page - Distraction-free, interactive practice environment.
 */
export function InterviewPage() {
  const [step, setStep] = useState<"select" | "answer" | "feedback">("select");
  const [interviewType, setInterviewType] = useState<InterviewType | null>(null);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartInterview = async (type: InterviewType) => {
    setLoading(true);
    setError(null);

    try {
      const res = await startInterview(type);
      if (res.error) {
        setError(res.error);
        return;
      }
      const data = res.data as InterviewQuestion;
      setInterviewId(data.interview_id);
      setInterviewType(type);
      setQuestion(data.question);
      setAnswer("");
      setEvaluation(null);
      setStep("answer");
    } catch {
      setError("Failed to start interview session. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (answer.trim().length < 10) {
      setError("Please provide at least 10 characters in your answer.");
      return;
    }
    if (!interviewId) return;

    setLoading(true);
    setError(null);

    try {
      const res = await submitInterviewAnswer(interviewId, answer, question || "");
      if (res.error) {
        setError(res.error);
        return;
      }
      setEvaluation(res.data as InterviewEvaluation);
      setStep("feedback");
    } catch {
      setError("Evaluation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = async () => {
    if (!interviewType) return;
    await handleStartInterview(interviewType);
  };

  const handleReset = () => {
    setStep("select");
    setInterviewType(null);
    setInterviewId(null);
    setQuestion(null);
    setAnswer("");
    setEvaluation(null);
    setError(null);
  };

  if (loading) {
    return (
      <LoadingState
        message={
          step === "select"
            ? "Preparing your interview question..."
            : "Evaluating your answer with AI rubric..."
        }
        subMessage="Scoring technical depth, communication structure, and actionable improvements."
      />
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Mock Interview
        </h1>
        <p className="text-sm sm:text-base text-slate-500 mt-2 max-w-xl mx-auto">
          Practice answering common interview questions with instant multi-dimension AI feedback.
        </p>
      </header>

      {error && <ErrorState message={error} />}

      {/* Step 1: Category Selection */}
      {step === "select" && (
        <div className="space-y-4">
          <div className="text-center mb-2">
            <h2 className="text-lg font-bold text-slate-900">
              Choose an Interview Category
            </h2>
            <p className="text-xs text-slate-500">
              Select a domain to generate an AI-tailored interview question.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {INTERVIEW_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => handleStartInterview(type.value)}
                className="group text-left p-5 bg-white border border-slate-200/90 rounded-2xl hover:border-blue-500 hover:bg-blue-50/40 transition-all duration-200 shadow-2xs hover:shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <span className="text-2xl p-2 rounded-xl bg-slate-50 group-hover:bg-white transition-colors border border-slate-100">
                    {type.icon}
                  </span>
                  <Badge
                    variant={
                      type.difficulty === "Advanced"
                        ? "warning"
                        : type.difficulty === "Intermediate"
                        ? "primary"
                        : "neutral"
                    }
                    size="sm"
                  >
                    {type.difficulty}
                  </Badge>
                </div>

                <h3 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                  {type.label}
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {type.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Answer Workspace */}
      {step === "answer" && question && (
        <Card>
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2">
                <Badge variant="primary" size="md">
                  {interviewType ? interviewType.toUpperCase() : "INTERVIEW"} SESSION
                </Badge>
              </div>
              <span className="text-xs text-slate-400 font-medium">Question 1 of 1</span>
            </div>

            <div className="p-5 rounded-2xl bg-blue-50/60 border border-blue-100">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider block mb-1">
                Prompt
              </span>
              <p className="text-lg font-bold text-slate-900 leading-relaxed">
                {question}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="answer"
                  className="block text-sm font-bold text-slate-900"
                >
                  Your Answer
                </label>
                <span className="text-xs text-slate-400">
                  {answer.length} characters (min 10)
                </span>
              </div>
              <textarea
                id="answer"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={8}
                placeholder="Type your answer here. Aim for at least 50–100 words with specific examples."
                className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
              />
              <p className="text-xs text-slate-500 flex items-center gap-1">
                <span>💡 Pro-tip: Structure your answer using the</span>
                <span className="font-semibold text-slate-700">STAR Method</span>
                <span>(Situation, Task, Action, Result).</span>
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                onClick={handleSubmitAnswer}
                disabled={answer.trim().length < 10}
                size="lg"
                className="w-full sm:w-auto"
              >
                Submit Answer
              </Button>
              <Button
                variant="ghost"
                onClick={handleReset}
                size="lg"
                className="w-full sm:w-auto text-slate-600"
              >
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Step 3: Structured Evaluation */}
      {step === "feedback" && evaluation && question && (
        <InterviewFeedback
          question={question}
          answer={answer}
          evaluation={evaluation}
          onNext={handleNextQuestion}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

interface InterviewFeedbackProps {
  question: string;
  answer: string;
  evaluation: InterviewEvaluation;
  onNext: () => void;
  onReset: () => void;
}

function InterviewFeedback({
  question,
  answer,
  evaluation,
  onNext,
  onReset,
}: InterviewFeedbackProps) {
  return (
    <div className="space-y-6">
      {/* Overall Performance Card */}
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-6">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="md">Evaluation Complete</Badge>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Your Score
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">{evaluation.feedback}</p>
          </div>
          <div className="shrink-0 w-full sm:w-48">
            <ScoreCard score={evaluation.score} label="Performance" />
          </div>
        </div>
      </Card>

      {/* Question & Answer Recap */}
      <Card title="Question Recap">
        <p className="text-sm sm:text-base text-slate-800 font-semibold mb-3">
          "{question}"
        </p>
        <details className="text-xs sm:text-sm bg-slate-50 border border-slate-200/80 rounded-xl p-3.5">
          <summary className="cursor-pointer text-blue-600 font-bold hover:underline select-none">
            View your answer transcript
          </summary>
          <p className="mt-3 text-slate-700 leading-relaxed whitespace-pre-wrap pl-2 border-l-2 border-blue-500">
            {answer}
          </p>
        </details>
      </Card>

      {/* Dimension Breakdown Cards */}
      {evaluation.dimensions.length > 0 && (
        <Card
          title="Dimension Breakdown"
          description="Detailed assessment across core interview criteria."
        >
          <div className="grid gap-3 sm:grid-cols-2 pt-1">
            {evaluation.dimensions.map((dim, i) => (
              <div
                key={i}
                className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-bold text-slate-900">{dim.name}</span>
                  <Badge variant={dim.score >= 80 ? "success" : dim.score >= 60 ? "primary" : "warning"} size="sm">
                    {dim.score}/100
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{dim.feedback}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Tips to Improve */}
      {evaluation.improvements.length > 0 && (
        <Card
          title="Tips to Improve"
          badge={<Badge variant="warning" size="sm">Actionable</Badge>}
          description="Specific areas to refine your answer for hiring managers."
        >
          <ul className="space-y-3 pt-1">
            {evaluation.improvements.map((tip, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5" aria-hidden="true">
                  →
                </span>
                <span className="leading-relaxed">{tip}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-4">
        <Button onClick={onNext} size="lg" className="w-full sm:w-auto">
          Next Question
        </Button>
        <Button variant="secondary" onClick={onReset} size="lg" className="w-full sm:w-auto">
          Choose Another Category
        </Button>
      </div>
    </div>
  );
}
