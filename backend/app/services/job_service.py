"""Job matching service."""

from __future__ import annotations

import re

from app.schemas.job_match import (
    JobMatchResponse,
    SkillMatch,
)
from app.services.resume_service import extract_required_skills


# Common boilerplate / English stopwords to exclude when computing content keyword overlap
_STOPWORDS: set[str] = {
    "about", "above", "after", "again", "against", "also", "been", "before",
    "being", "below", "between", "both", "candidate", "company", "could",
    "description", "developer", "duties", "each", "equal", "experience",
    "from", "further", "have", "having", "here", "into", "job", "joining",
    "just", "knowledge", "looking", "more", "most", "must", "only", "opportunity",
    "other", "our", "out", "over", "plus", "position", "preferred", "qualifications",
    "requirements", "responsibilities", "role", "same", "should", "skill",
    "skills", "some", "such", "than", "that", "the", "their", "them", "then",
    "there", "these", "they", "this", "those", "through", "under", "until",
    "very", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "work", "working", "would", "years", "your",
}


def calculate_match(
    resume_skills: list[str],
    job_requirements: str,
) -> JobMatchResponse:
    """Calculate match score between resume skills and job requirements."""
    required_skills = extract_required_skills(job_requirements)
    resume_set = {s.strip().lower() for s in resume_skills if s.strip()}
    job_lower = job_requirements.lower()

    matched: list[SkillMatch] = []
    missing: list[str] = []

    for skill in required_skills:
        # Match against resume skills
        is_matched = skill in resume_set or any(
            skill in rs or rs in skill for rs in resume_set
        )
        # Count occurrences of the full skill phrase in the job posting
        count = len(re.findall(r"\b" + re.escape(skill) + r"\b", job_lower))
        priority = min(5, max(1, 6 - max(1, count)))
        matched.append(SkillMatch(skill=skill, matched=is_matched, priority=priority))
        if not is_matched:
            missing.append(skill)

    if not required_skills:
        # If no explicit catalog skills were extracted, do a keyword-based overlap
        raw_job_tokens = set(re.findall(r"\b[a-z]{3,}\b", job_lower)) - _STOPWORDS
        raw_resume_tokens = set()
        for s in resume_set:
            raw_resume_tokens.update(re.findall(r"\b[a-z]{3,}\b", s))

        if raw_job_tokens and raw_resume_tokens:
            overlap = len(raw_job_tokens & raw_resume_tokens) / max(1, len(raw_job_tokens))
            match_score = min(100, max(20, int(overlap * 100)))
        else:
            match_score = 50
    else:
        # 75% weight on skill match, 25% on keyword context overlap
        matched_count = len([m for m in matched if m.matched])
        skills_match_pct = (matched_count / len(required_skills)) * 75

        job_keywords = set(re.findall(r"\b[a-z]{3,}\b", job_lower)) - _STOPWORDS
        resume_keywords = set()
        for s in resume_set:
            resume_keywords.update(re.findall(r"\b[a-z]{3,}\b", s))

        if job_keywords:
            content_overlap = (len(job_keywords & resume_keywords) / max(1, len(job_keywords))) * 25
        else:
            content_overlap = 0

        match_score = min(100, max(0, int(skills_match_pct + content_overlap)))

    recommendations: list[str] = []
    if missing:
        top_missing = [m for m in matched if not m.matched and m.priority <= 2]
        if not top_missing:
            top_missing = [m for m in matched if not m.matched]
        if top_missing:
            skills_list = ", ".join(s.skill for s in top_missing[:3])
            recommendations.append(f"Focus on learning: {skills_list}")

    if match_score < 50:
        recommendations.append("Consider gaining more relevant experience before applying")
    elif match_score < 70:
        recommendations.append("Address key skill gaps to improve your match")
    else:
        recommendations.append("Strong match - consider applying with confidence")

    summary = f"Your resume matches approximately {match_score}% of the job requirements."

    return JobMatchResponse(
        match_score=match_score,
        matched_skills=matched,
        missing_skills=missing,
        recommendations=recommendations,
        summary=summary,
    )
