"""Job match Pydantic schemas."""
from pydantic import BaseModel, Field, field_validator


class JobMatchRequest(BaseModel):
    """Request schema for job matching."""

    resume_skills: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of skills from user's resume",
    )
    job_requirements: str = Field(
        ...,
        min_length=50,
        max_length=20000,
        description="Job description text",
    )

    @field_validator("resume_skills", mode="after")
    @classmethod
    def _normalize_skills(cls, v: list[str]) -> list[str]:
        """Normalize skill names."""
        return [s.strip().lower() for s in v if s.strip()]


class SkillMatch(BaseModel):
    """Individual skill match detail."""

    skill: str = Field(..., description="Skill name")
    matched: bool = Field(..., description="Whether skill matches job requirements")
    priority: int = Field(..., ge=1, le=5, description="Priority 1=high, 5=low")


class JobMatchResponse(BaseModel):
    """Response schema for job matching."""

    match_score: int = Field(..., ge=0, le=100, description="Overall match percentage")
    matched_skills: list[SkillMatch] = Field(
        default_factory=list, description="Matched skills"
    )
    missing_skills: list[str] = Field(default_factory=list, description="Missing skills")
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    summary: str = Field(..., description="Match summary")
