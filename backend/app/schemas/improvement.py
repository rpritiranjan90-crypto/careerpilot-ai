"""Schemas for Career Improvement Engine."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NextBestAction(BaseModel):
    """Exactly one high-leverage recommendation for the user."""

    title: str = Field(..., description="Action title")
    category: str = Field(..., description="Category: resume, skills, or interview")
    why: str = Field(..., description="Why this action matters for hiring conversion")
    what_to_do: str = Field(..., description="Specific, concrete instructions")
    expected_outcome: str = Field(..., description="Expected impact on readiness score")
    cta_label: str = Field(..., description="Call to action button text")
    cta_link: str = Field(..., description="Internal route to take action")


class ResumeEnhancementItem(BaseModel):
    """Concrete Before/After resume improvement suggestion with anti-fabrication guards."""

    id: str = Field(..., description="Unique suggestion ID")
    category: str = Field(..., description="Section category")
    issue: str = Field(..., description="Identified weakness or ATS issue")
    severity: str = Field("medium", description="Severity: high, medium, low")
    explanation: str = Field(..., description="Why the current phrasing or format hurts ATS/recruiters")
    recommended_fix: str = Field(..., description="Direct guidance on how to fix")
    before_example: str = Field(..., description="Weak before example")
    after_example: str = Field(..., description="Strong after example with explicit [X] placeholders")
    is_placeholder_example: bool = Field(
        True,
        description="True indicates the rewrite contains example placeholders to fill with real metrics",
    )


class SkillGapItem(BaseModel):
    """Prioritized missing or improvement-needed skill with complete learning path."""

    skill_name: str = Field(..., description="Skill name")
    status: str = Field(..., description="Status: missing, improve, or strong")
    priority: str = Field("Medium", description="Priority: High, Medium, Low")
    reason: str = Field(..., description="Why this skill is critical for target roles")
    prerequisites: list[str] = Field(default_factory=list, description="Foundational prerequisite skills")
    learning_path: str = Field(..., description="Structured 3-step learning path")
    practical_exercise: str = Field(..., description="Hands-on practice exercise")
    project_idea: str = Field(..., description="Portfolio project idea demonstrating the skill")


class ActionItem(BaseModel):
    """Individual action task with persisted completion state."""

    task_id: str = Field(..., description="Stable task identifier")
    task: str = Field(..., description="Actionable task title")
    category: str = Field(..., description="Category: resume, skills, or interview")
    estimated_minutes: int = Field(30, description="Estimated time to complete in minutes")
    is_completed: bool = Field(False, description="Persisted completion state in DB")
    completed_at: str | None = Field(None, description="ISO timestamp when marked complete")


class ActionPlanTimeline(BaseModel):
    """Prioritized timeline breakdown."""

    today: list[ActionItem] = Field(default_factory=list, description="Quick 15-30 min wins for today")
    this_week: list[ActionItem] = Field(default_factory=list, description="Weekly skill & project milestones")
    this_month: list[ActionItem] = Field(default_factory=list, description="Monthly interview & portfolio goals")


class ScoreProgressItem(BaseModel):
    """Verified historical score progression."""

    current: int = Field(..., description="Current verified score")
    previous: int | None = Field(None, description="Previous verified historical snapshot score")
    delta: int | None = Field(None, description="Actual score delta (current - previous)")


class ProgressTracking(BaseModel):
    """Real progress tracking backed by database snapshots."""

    has_history: bool = Field(False, description="Whether previous historical assessment exists")
    overall_readiness: ScoreProgressItem
    resume_score: ScoreProgressItem
    job_match_score: ScoreProgressItem
    interview_score: ScoreProgressItem
    skills_score: ScoreProgressItem


class CareerImprovementPlan(BaseModel):
    """Complete, deterministic AI Career Improvement Plan."""

    has_data: bool = Field(..., description="Whether user has uploaded data")
    data_completeness: str = Field(..., description="complete, resume_only, no_data, or partial")
    overall_score: int = Field(..., description="Current overall career readiness score (0-100)")
    target_potential_score: int = Field(..., description="Target potential score after applying plan")
    summary: str = Field(..., description="Executive summary of the improvement roadmap")
    next_best_action: NextBestAction | None = Field(None, description="Primary single high-leverage action")
    resume_enhancements: list[ResumeEnhancementItem] = Field(default_factory=list)
    skill_gaps: list[SkillGapItem] = Field(default_factory=list)
    action_plan: ActionPlanTimeline
    progress_tracking: ProgressTracking
