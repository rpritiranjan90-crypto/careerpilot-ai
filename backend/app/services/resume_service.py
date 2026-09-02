"""Service layer for resume analysis, job matching, and interview management.

This module implements the core business logic for CareerPilot AI features.
It uses a deterministic scoring system supplemented by AI insights.
"""

import re

from app.schemas.resume import (
    ResumeAnalysisResponse,
    SkillAnalysis,
)

# ---------- Resume Analysis ---------- #

# Common skill keywords (free-first; can be enhanced with AI later)
TECHNICAL_SKILLS: set[str] = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "sql", "html", "css",
    "react", "vue", "angular", "node.js", "express", "django", "flask",
    "fastapi", "spring", "rails", "laravel", "mongodb", "postgresql",
    "mysql", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "linux", "rest api", "graphql", "tensorflow", "pytorch",
    "machine learning", "data analysis", "data science", "pandas",
    "numpy", "scikit-learn", "tableau", "power bi", "excel", "r",
}

SOFT_SKILLS: set[str] = {
    "leadership", "communication", "teamwork", "problem solving",
    "analytical", "creative", "adaptable", "organized", "detail-oriented",
    "collaboration", "time management", "critical thinking", "presentation",
    "negotiation", "mentoring", "project management",
}


def extract_skills(text: str) -> list[SkillAnalysis]:
    """Extract skills from resume text by matching against known skills.

    This is a simple keyword-based approach that works without AI.
    """
    text_lower = text.lower()
    skills: list[SkillAnalysis] = []

    for skill in TECHNICAL_SKILLS | SOFT_SKILLS:
        # Match whole word boundaries
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            category = "technical" if skill in TECHNICAL_SKILLS else "soft"
            skills.append(SkillAnalysis(name=skill, confidence=0.9, category=category))

    return skills


def analyze_resume(
    resume_text: str,
    job_description: str | None = None,
) -> ResumeAnalysisResponse:
    """Analyze resume text and return structured analysis.

    Uses a deterministic scoring algorithm:
    - 30 points: Skills detected
    - 25 points: Experience (length and detail)
    - 15 points: Education
    - 15 points: Projects mentioned
    - 15 points: Formatting/structure (sections, measurable achievements)
    """
    skills = extract_skills(resume_text)
    text_lower = resume_text.lower()

    # Skills score (max 30)
    tech_skills = [s for s in skills if s.category == "technical"]
    soft_skills = [s for s in skills if s.category == "soft"]
    skills_score = min(30, len(tech_skills) * 3 + len(soft_skills) * 2)

    # Experience score (max 25) - looks for years, role titles
    has_years = bool(re.search(r"\d+\+?\s*(?:years?|yrs?)", text_lower))
    has_experience = "experience" in text_lower or "work" in text_lower
    experience_score = 0
    if has_years:
        experience_score += 15
    if has_experience:
        experience_score += 10

    # Education score (max 15)
    education_keywords = ["university", "college", "bachelor", "master", "degree", "phd", "b.sc", "m.sc", "b.tech", "m.tech"]
    has_education = any(kw in text_lower for kw in education_keywords)
    education_score = 15 if has_education else 0

    # Projects score (max 15)
    has_projects = "project" in text_lower or "portfolio" in text_lower
    projects_score = 15 if has_projects else 0

    # Formatting/structure score (max 15)
    has_contact = bool(re.search(r"[\w\.-]+@[\w\.-]+", resume_text))
    has_numbers = bool(re.search(r"\d+%|\d+\s*(?:users|customers|projects)", resume_text))
    has_sections = len(re.findall(r"\n[A-Z][A-Z\s]+\n", resume_text)) >= 3

    formatting_score = 0
    if has_contact:
        formatting_score += 5
    if has_numbers:
        formatting_score += 5
    if has_sections:
        formatting_score += 5

    total_score = skills_score + experience_score + education_score + projects_score + formatting_score

    # Generate strengths and weaknesses
    strengths: list[str] = []
    weaknesses: list[str] = []

    if len(tech_skills) >= 5:
        strengths.append(f"Strong technical skills ({len(tech_skills)} detected)")
    elif len(tech_skills) < 3:
        weaknesses.append("Limited technical skills listed")

    if has_projects:
        strengths.append("Good project experience")
    else:
        weaknesses.append("Consider adding personal or professional projects")

    if has_numbers:
        strengths.append("Uses measurable achievements")
    else:
        weaknesses.append("Add quantifiable achievements (%, numbers, scale)")

    if has_education:
        strengths.append("Education clearly stated")
    else:
        weaknesses.append("Education section missing or unclear")

    if has_years:
        strengths.append("Work experience is quantified")

    # Recommendations
    recommendations: list[str] = []
    if not has_numbers:
        recommendations.append("Add measurable achievements (e.g., 'Improved performance by 40%')")
    if not has_projects:
        recommendations.append("Include 2-3 key projects with technologies used")
    if len(tech_skills) < 5:
        recommendations.append("List more relevant technical skills")
    if not has_sections:
        recommendations.append("Use clear section headers (EDUCATION, EXPERIENCE, SKILLS)")

    # Summaries
    experience_summary = extract_section_summary(resume_text, ["experience", "work history"])
    education_summary = extract_section_summary(resume_text, ["education", "academic"])
    project_summary = extract_section_summary(resume_text, ["projects", "portfolio"])

    summary = f"Resume analysis shows {len(skills)} skills detected with an overall score of {total_score}/100."

    return ResumeAnalysisResponse(
        score=total_score,
        summary=summary,
        skills=skills,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        experience_summary=experience_summary,
        education_summary=education_summary,
        project_summary=project_summary,
    )


def extract_section_summary(text: str, section_keywords: list[str]) -> str | None:
    """Extract a summary line for a section in the resume."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in section_keywords):
            # Return next non-empty lines (up to 200 chars)
            summary_lines = []
            for next_line in lines[i + 1 : i + 5]:
                if next_line.strip():
                    summary_lines.append(next_line.strip())
            if summary_lines:
                return " ".join(summary_lines)[:200]
    return None


def extract_required_skills(job_text: str) -> list[str]:
    """Extract skills mentioned in job description text.

    Uses keyword matching against the known skill catalog.
    Used by both the resume service and the job service.
    """
    text_lower = job_text.lower()
    found: list[str] = []

    for skill in TECHNICAL_SKILLS | SOFT_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)

    return found
