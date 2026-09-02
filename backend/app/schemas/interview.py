"""Interview Pydantic schemas."""

from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    """Request schema for starting interview."""

    interview_type: str = Field(
        ...,
        description="Interview type: general, hr, technical, role_specific",
    )
    question: str | None = Field(
        default=None,
        description="Optional specific question to start with",
    )


class EvaluationDimension(BaseModel):
    """Individual evaluation dimension."""

    name: str = Field(..., description="Dimension name")
    score: int = Field(..., ge=0, le=100, description="Score 0-100")
    feedback: str = Field(..., description="Feedback for this dimension")


class InterviewResponse(BaseModel):
    """Response schema for interview."""

    interview_id: str = Field(..., description="Unique interview session ID")
    question: str = Field(..., description="Interview question")
    category: str = Field(..., description="Question category")
    evaluation: EvaluationDimension | None = Field(
        default=None, description="Answer evaluation if provided"
    )
    tips: list[str] = Field(default_factory=list, description="General tips for this question")
