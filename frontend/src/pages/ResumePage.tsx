import { useState, useRef } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ScoreCard } from "../components/ScoreCard";
import { Badge } from "../components/Badge";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import {
  analyzeResume,
  analyzeUploadedResume,
  uploadResumeFile,
} from "../services/api";
import type { ResumeAnalysis } from "../services/api";

/**
 * Resume Analysis Page - High quality SaaS experience.
 *
 * Supports drag-and-drop document upload (PDF, DOCX, TXT) and direct text paste.
 */
export function ResumePage() {
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- File upload handler ---
  const handleFileProcess = async (file: File) => {
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds maximum 5MB size limit.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Step 1: Upload file
      const uploadRes = await uploadResumeFile(file);
      if (uploadRes.error) {
        setError(uploadRes.error);
        return;
      }
      const { resume_id } = uploadRes.data!;

      // Step 2: Analyze uploaded file
      const analyzeRes = await analyzeUploadedResume(resume_id);
      if (analyzeRes.error) {
        setError(analyzeRes.error);
        return;
      }
      setAnalysis(analyzeRes.data!);
    } catch {
      setError("Upload failed. Please try again with a valid document.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleFileProcess(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await handleFileProcess(file);
    }
  };

  // --- Text paste handler ---
  const handleAnalyze = async () => {
    if (resumeText.trim().length < 50) {
      setError("Please provide at least 50 characters of resume text.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeResume(resumeText, jobDescription || undefined);
      if (result.error) {
        setError(result.error);
        return;
      }
      setAnalysis(result.data!);
    } catch {
      setError("Analysis failed. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResumeText("");
    setJobDescription("");
    setAnalysis(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  if (loading) {
    return (
      <LoadingState
        message="Analyzing your resume..."
        subMessage="Extracting key skills, evaluating ATS keyword density, and generating recommendations."
      />
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Resume Analysis
        </h1>
        <p className="text-sm sm:text-base text-slate-500 mt-2 max-w-xl mx-auto">
          Upload your resume or paste the text to get instant feedback on strengths, weaknesses, and ATS readiness.
        </p>
      </header>

      {error && <ErrorState message={error} />}

      {!analysis ? (
        <Card title="Upload or Paste Your Resume">
          <div className="space-y-6">
            {/* Drag & Drop Upload Zone */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-2xl p-6 sm:p-10 text-center cursor-pointer transition-all duration-200 ${
                dragActive
                  ? "border-blue-500 bg-blue-50/60"
                  : "border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50"
              }`}
            >
              <input
                id="resume-file"
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileInputChange}
                className="hidden"
                aria-label="Choose file (PDF, DOCX, TXT — max 5MB)"
              />

              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 mx-auto flex items-center justify-center mb-3 shadow-2xs">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1">
                Drop your resume here, or{" "}
                <span className="text-blue-600 hover:underline">browse files</span>
              </h3>
              <p className="text-xs text-slate-500 mb-3">
                Choose file (PDF, DOCX, TXT — max 5MB)
              </p>

              <div className="flex items-center justify-center gap-2">
                <Badge variant="neutral" size="sm">PDF</Badge>
                <Badge variant="neutral" size="sm">DOCX</Badge>
                <Badge variant="neutral" size="sm">TXT</Badge>
                <Badge variant="primary" size="sm">Max 5MB</Badge>
              </div>
            </div>

            {/* Privacy notice */}
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-600">
              <span className="text-blue-600 font-bold shrink-0">🔒 Privacy:</span>
              <span>
                Uploaded files are encrypted and processed securely. You can permanently erase all stored documents anytime in{" "}
                <a href="/settings" className="text-blue-600 font-semibold hover:underline">
                  Settings (GDPR Article 17)
                </a>.
              </span>
            </div>

            {/* Visual Divider */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase tracking-wider">
                <span className="px-3 bg-white text-slate-400 font-bold">or paste text</span>
              </div>
            </div>

            {/* Paste Text Form */}
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label
                    htmlFor="resume-text"
                    className="block text-sm font-bold text-slate-900"
                  >
                    Resume text
                  </label>
                  <span className={`text-xs font-mono font-medium ${
                    resumeText.length >= 50 ? "text-emerald-600" : "text-slate-400"
                  }`}>
                    {resumeText.length} characters (min 50)
                  </span>
                </div>
                <textarea
                  id="resume-text"
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  rows={8}
                  placeholder="Paste your resume content here..."
                  className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>

              <div>
                <label
                  htmlFor="job-description"
                  className="block text-sm font-bold text-slate-900 mb-2"
                >
                  Target job description (optional)
                </label>
                <textarea
                  id="job-description"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={3}
                  placeholder="Paste a job description to tailor the analysis..."
                  className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>

              <div className="pt-2">
                <Button
                  onClick={handleAnalyze}
                  disabled={resumeText.trim().length < 50}
                  size="lg"
                  className="w-full sm:w-auto"
                >
                  Analyze Resume
                </Button>
              </div>
            </div>
          </div>
        </Card>
      ) : (
        <ResumeResults analysis={analysis} onReset={handleReset} />
      )}
    </div>
  );
}

interface ResumeResultsProps {
  analysis: ResumeAnalysis;
  onReset: () => void;
}

function ResumeResults({ analysis, onReset }: ResumeResultsProps) {
  return (
    <div className="space-y-6">
      {/* Overview Score Card */}
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-6">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="md">ATS Audit Complete</Badge>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Resume Score
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">{analysis.summary}</p>
          </div>
          <div className="shrink-0 w-full sm:w-48">
            <ScoreCard score={analysis.score} label="Overall Score" />
          </div>
        </div>
      </Card>

      {/* Strengths and Weaknesses 2-Column Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card
          title="Strengths"
          badge={<Badge variant="success" size="sm">✓ Highlights</Badge>}
        >
          {analysis.strengths.length > 0 ? (
            <ul className="space-y-3">
              {analysis.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5" aria-hidden="true">
                    ✓
                  </span>
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="No strengths identified"
              description="Try adding more detail to your projects and past work experiences."
            />
          )}
        </Card>

        <Card
          title="Areas to Improve"
          badge={<Badge variant="warning" size="sm">⚠ Focus</Badge>}
        >
          {analysis.weaknesses.length > 0 ? (
            <ul className="space-y-3">
              {analysis.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                  <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5" aria-hidden="true">
                    !
                  </span>
                  <span className="leading-relaxed">{w}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="Looking great!"
              description="No critical weaknesses or format violations detected."
            />
          )}
        </Card>
      </div>

      {/* Detected Skills Cloud */}
      {analysis.skills.length > 0 && (
        <Card
          title="Detected Skills"
          description="Key technical and domain skills parsed by the ATS extraction model."
        >
          <div className="flex flex-wrap gap-2 pt-1">
            {analysis.skills.map((skill, i) => (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/60 shadow-2xs"
              >
                {skill.name}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Ranked Action Plan / Recommendations */}
      {analysis.recommendations.length > 0 && (
        <Card
          title="Recommendations & Next Steps"
          description="Prioritized changes to improve your resume's interview conversion rate."
        >
          <ol className="space-y-3">
            {analysis.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                <span className="w-6 h-6 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span className="leading-relaxed font-medium">{r}</span>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-4">
        <Button variant="secondary" onClick={onReset} className="w-full sm:w-auto">
          Analyze Another Resume
        </Button>
        <a href="/improve" className="w-full sm:w-auto">
          <Button variant="secondary" className="w-full sm:w-auto border-blue-200 text-blue-700 bg-blue-50/50 hover:bg-blue-100/60">
            View Improvement Plan ➔
          </Button>
        </a>
        <a href="/job-match" className="w-full sm:w-auto">
          <Button className="w-full sm:w-auto">
            Continue to Job Match →
          </Button>
        </a>
      </div>
    </div>
  );
}
