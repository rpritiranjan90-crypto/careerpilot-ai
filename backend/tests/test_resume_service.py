"""Tests for resume analysis service."""
from app.services.resume_service import (
    analyze_resume,
    extract_required_skills,
    extract_skills,
)


def test_extract_skills_detects_technical(sample_resume_text):
    """Test that technical skills are detected."""
    skills = extract_skills(sample_resume_text)
    skill_names = {s.name for s in skills}

    # Should detect key technical skills from sample
    assert "python" in skill_names
    assert "sql" in skill_names
    assert "docker" in skill_names
    assert "kubernetes" in skill_names


def test_extract_skills_returns_skill_analysis_objects(sample_resume_text):
    """Test that skill objects have required fields."""
    skills = extract_skills(sample_resume_text)
    assert len(skills) > 0

    for skill in skills:
        assert skill.name
        assert 0.0 <= skill.confidence <= 1.0
        assert skill.category in ("technical", "soft")


def test_analyze_resume_returns_score_in_range(sample_resume_text):
    """Test that resume score is between 0 and 100."""
    result = analyze_resume(sample_resume_text)
    assert 0 <= result.score <= 100
    assert result.summary


def test_analyze_resume_detects_strengths(sample_resume_text):
    """Test that strengths are detected for good resume."""
    result = analyze_resume(sample_resume_text)
    assert len(result.strengths) > 0
    # Good resume should have multiple skills
    assert len(result.skills) > 3


def test_analyze_resume_identifies_recommendations(sample_resume_text):
    """Test that recommendations are provided."""
    result = analyze_resume(sample_resume_text)
    assert isinstance(result.recommendations, list)


def test_analyze_resume_handles_empty_text():
    """Test that empty text returns low score."""
    result = analyze_resume("")
    assert result.score < 50


def test_extract_required_skills_finds_job_requirements(sample_job_description):
    """Test that job requirements are extracted."""
    skills = extract_required_skills(sample_job_description)
    assert "python" in skills
    assert "sql" in skills
    assert "docker" in skills or "kubernetes" in skills


def test_analyze_resume_includes_summaries(sample_resume_text):
    """Test that section summaries are extracted."""
    result = analyze_resume(sample_resume_text)
    # Sample resume has clear sections
    assert result.experience_summary is not None or result.education_summary is not None
