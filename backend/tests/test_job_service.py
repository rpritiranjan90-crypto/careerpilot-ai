"""Tests for job matching service."""
from app.services.job_service import calculate_match
from app.services.resume_service import TECHNICAL_SKILLS


def test_calculate_match_returns_valid_score(sample_resume_text, sample_job_description):
    """Test that match score is in valid range."""
    from app.services.resume_service import extract_skills
    skills = [s.name for s in extract_skills(sample_resume_text)]
    result = calculate_match(skills, sample_job_description)

    assert 0 <= result.match_score <= 100
    assert result.summary


def test_calculate_match_finds_matched_skills(sample_resume_text, sample_job_description):
    """Test that matched skills are identified."""
    from app.services.resume_service import extract_skills
    skills = [s.name for s in extract_skills(sample_resume_text)]
    result = calculate_match(skills, sample_job_description)

    matched = [m for m in result.matched_skills if m.matched]
    assert len(matched) > 0


def test_calculate_match_identifies_missing_skills(sample_job_description):
    """Test that missing skills are identified."""
    # Empty skills - all should be missing
    result = calculate_match([], sample_job_description)
    assert len(result.missing_skills) > 0


def test_calculate_match_higher_score_with_more_skills(sample_job_description):
    """Test that more skills = higher score."""
    few_skills = ["python"]
    many_skills = ["python", "sql", "aws", "docker", "kubernetes", "git"]

    result_few = calculate_match(few_skills, sample_job_description)
    result_many = calculate_match(many_skills, sample_job_description)

    assert result_many.match_score >= result_few.match_score


def test_calculate_match_provides_recommendations(sample_job_description):
    """Test that recommendations are provided."""
    result = calculate_match(["python"], sample_job_description)
    assert isinstance(result.recommendations, list)
    assert len(result.recommendations) > 0


def test_calculate_match_handles_empty_job_description():
    """Test graceful handling of empty job description."""
    result = calculate_match(["python"], "")
    assert 0 <= result.match_score <= 100
