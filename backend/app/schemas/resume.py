"""Resume-related Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator


class ResumeUploadRequest(BaseModel):
    """Request schema for resume analysis."""

    resume_text: str = Field(
        ...,
        min_length=50,
        max_length=50000,
        description="Extracted text from the resume",
    )
    job_description: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional job description for comparison",
    )

    @field_validator("resume_text", mode="after")
    @classmethod
    def _clean_resume_text(cls, v: str) -> str:
        """Normalize whitespace in resume text."""
        return " ".join(v.split())


class SkillAnalysis(BaseModel):
    """Individual skill analysis."""

    name: str = Field(..., description="Skill name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    category: str = Field(default="general", description="Skill category")


class ResumeAnalysisResponse(BaseModel):
    """Response schema for resume analysis."""

    score: int = Field(..., ge=0, le=100, description="Overall resume score 0-100")
    summary: str = Field(..., description="Brief analysis summary")
    skills: list[SkillAnalysis] = Field(default_factory=list, description="Detected skills")
    strengths: list[str] = Field(default_factory=list, description="Resume strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Areas for improvement")
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable improvement suggestions"
    )
    experience_summary: str | None = Field(default=None, description="Experience overview")
    education_summary: str | None = Field(default=None, description="Education overview")
    project_summary: str | None = Field(default=None, description="Projects overview")
