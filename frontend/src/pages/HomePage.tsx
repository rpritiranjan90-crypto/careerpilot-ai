import { Link } from "react-router-dom";
import { Button } from "../components/Button";

/**
 * Home page - High-converting, modern SaaS landing experience.
 */
export function HomePage() {
  return (
    <div className="space-y-16 md:space-y-24">
      {/* Hero Section */}
      <section className="text-center pt-6 pb-4 md:pt-12 md:pb-8 max-w-3xl mx-auto">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-xs font-bold mb-6 shadow-2xs">
          <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
          AI Career Preparation Platform
        </div>

        {/* Hero Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.1] mb-6">
          Prepare smarter.
          <br />
          <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 bg-clip-text text-transparent">
            Get career-ready.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
          Analyze your resume, identify critical skill gaps, match yourself to target jobs, and practice AI mock interviews — all in one privacy-conscious tool.
        </p>

        {/* Primary CTAs */}
        <div className="flex flex-col sm:flex-row gap-3.5 justify-center items-center">
          <Link to="/resume" className="w-full sm:w-auto">
            <Button size="lg" className="w-full sm:w-auto shadow-sm">
              <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Analyze My Resume
            </Button>
          </Link>
          <Link to="/interview" className="w-full sm:w-auto">
            <Button variant="secondary" size="lg" className="w-full sm:w-auto">
              <svg className="w-5 h-5 mr-1 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Practice Interview
            </Button>
          </Link>
        </div>
      </section>

      {/* Core Capabilities Section */}
      <section className="space-y-6">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Everything you need to stand out
          </h2>
          <p className="text-sm text-slate-500">
            Intelligent career tools designed to get you from application to offer.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <FeatureCard
            icon={
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            title="Resume Analysis"
            tag="ATS Ready"
            description="Extract skills, quantify project impact, and get tailored recommendations to beat applicant tracking systems."
            linkTo="/resume"
            linkLabel="Analyze Resume"
          />
          <FeatureCard
            icon={
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
            title="Job Match"
            tag="Skill Gap AI"
            description="Compare your qualifications directly against job postings to find match percentages and missing skills."
            linkTo="/job-match"
            linkLabel="Check Match"
          />
          <FeatureCard
            icon={
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            }
            title="Mock Interview"
            tag="STAR Method"
            description="Practice realistic technical and HR interview questions with instant multi-dimension feedback."
            linkTo="/interview"
            linkLabel="Start Interview"
          />
        </div>
      </section>

      {/* How CareerPilot Works 5-Step Roadmap */}
      <section className="bg-white border border-slate-200/90 rounded-3xl p-8 sm:p-10 shadow-xs space-y-8">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <div className="text-xs font-extrabold uppercase tracking-wider text-blue-600">
            Methodology
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How CareerPilot Works
          </h2>
          <p className="text-sm text-slate-500">
            Five structured steps to systematically elevate your hiring readiness.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 pt-2">
          <StepItem
            step="01"
            title="Upload Resume"
            description="Upload PDF/DOCX or paste text to extract your core skills."
          />
          <StepItem
            step="02"
            title="Audit Strengths"
            description="Review strengths, detected weaknesses, and ATS metrics."
          />
          <StepItem
            step="03"
            title="Target Jobs"
            description="Paste job requirements to uncover critical skill gaps."
          />
          <StepItem
            step="04"
            title="Practice Q&A"
            description="Rehearse interview questions using the proven STAR framework."
          />
          <StepItem
            step="05"
            title="Track Readiness"
            description="Monitor your real-time composite score on your dashboard."
          />
        </div>
      </section>

      {/* Career Readiness Preview Banner */}
      <section className="bg-gradient-to-br from-blue-600 via-indigo-600 to-slate-900 rounded-3xl p-8 sm:p-12 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-3 text-center md:text-left max-w-xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 text-white text-xs font-bold backdrop-blur-xs border border-white/20">
              📊 Live Aggregation
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Know Your Career Readiness
            </h2>
            <p className="text-blue-100 text-sm sm:text-base leading-relaxed font-normal">
              CareerPilot aggregates your resume analysis, job match scores, and interview performance into one unified readiness index.
            </p>
          </div>

          <Link to="/dashboard" className="shrink-0 w-full sm:w-auto text-center">
            <Button
              variant="secondary"
              size="lg"
              className="w-full sm:w-auto bg-white text-slate-900 hover:bg-slate-50 border-0 shadow-sm"
            >
              View Dashboard →
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  tag: string;
  description: string;
  linkTo: string;
  linkLabel: string;
}

function FeatureCard({
  icon,
  title,
  tag,
  description,
  linkTo,
  linkLabel,
}: FeatureCardProps) {
  return (
    <article className="group bg-white border border-slate-200/90 rounded-2xl p-6 flex flex-col justify-between hover:border-blue-300 hover:shadow-sm transition-all duration-200">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
            {icon}
          </div>
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200/60">
            {tag}
          </span>
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-sm text-slate-500 leading-relaxed mb-6">{description}</p>
      </div>

      <Link
        to={linkTo}
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 group-hover:text-blue-700 transition-colors"
      >
        <span>{linkLabel}</span>
        <span className="transition-transform group-hover:translate-x-1" aria-hidden="true">→</span>
      </Link>
    </article>
  );
}

interface StepItemProps {
  step: string;
  title: string;
  description: string;
}

function StepItem({ step, title, description }: StepItemProps) {
  return (
    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col justify-between">
      <div>
        <div className="text-xs font-black text-blue-600 tracking-wider mb-2 font-mono">
          {step}
        </div>
        <h4 className="text-sm font-bold text-slate-900 mb-1">{title}</h4>
        <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}