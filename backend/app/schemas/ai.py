"""Pydantic schemas for validated AI service outputs.

All AI responses — whether from Ollama or the fallback — are validated
against these schemas before being returned to callers. This prevents
malformed LLM output from causing downstream failures.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AISkillItem(BaseModel):
    """Individual skill item from AI resume analysis."""
    name: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: str = Field(default="general", max_length=50)


class AIResumeAnalysis(BaseModel):
    """Validated output schema for resume analysis."""
    score: int = Field(..., ge=0, le=100)
    summary: str = Field(..., max_length=1000)
    skills: list[AISkillItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    experience_summary: str | None = None
    education_summary: str | None = None
    project_summary: str | None = None

    @field_validator("score", mode="before")
    @classmethod
    def _coerce_score(cls, v):
        if isinstance(v, float):
            return int(v)
        return v


class AISkillMatch(BaseModel):
    """Individual skill match from AI job matching."""
    skill: str = Field(..., max_length=100)
    matched: bool
    priority: int = Field(..., ge=1, le=5)


class AIJobMatch(BaseModel):
    """Validated output schema for job matching."""
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: list[AISkillMatch] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str = Field(..., max_length=500)

    @field_validator("match_score", mode="before")
    @classmethod
    def _coerce_score(cls, v):
        if isinstance(v, float):
            return int(v)
        return v


class AIEvaluationDimension(BaseModel):
    """Individual evaluation dimension."""
    name: str = Field(..., max_length=100)
    score: int = Field(..., ge=0, le=100)
    feedback: str = Field(..., max_length=500)


class AIInterviewEvaluation(BaseModel):
    """Validated output schema for interview answer evaluation."""
    interview_id: str = Field(..., max_length=100)
    score: int = Field(..., ge=0, le=100)
    feedback: str = Field(..., max_length=1000)
    dimensions: list[AIEvaluationDimension] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def _coerce_score(cls, v):
        if isinstance(v, float):
            return int(v)
        return v
